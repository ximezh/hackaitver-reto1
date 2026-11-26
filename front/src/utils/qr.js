const VERSIONES_L = [
  null,
  { version: 1, size: 21, dataBytes: 19, ecBytes: 7, align: [] },
  { version: 2, size: 25, dataBytes: 34, ecBytes: 10, align: [18] },
  { version: 3, size: 29, dataBytes: 55, ecBytes: 15, align: [22] },
  { version: 4, size: 33, dataBytes: 80, ecBytes: 20, align: [26] },
]

const GF_EXP = new Uint8Array(512)
const GF_LOG = new Uint8Array(256)
;(function initGf() {
  let x = 1
  for (let i = 0; i < 255; i++) {
    GF_EXP[i] = x
    GF_LOG[x] = i
    x <<= 1
    if (x & 0x100) x ^= 0x11d
  }
  for (let i = 255; i < 512; i++) {
    GF_EXP[i] = GF_EXP[i - 255]
  }
})()

function gfMul(a, b) {
  if (a === 0 || b === 0) return 0
  return GF_EXP[GF_LOG[a] + GF_LOG[b]]
}

function reedSolomon(data, ecLen) {
  let gen = [1]
  for (let i = 0; i < ecLen; i++) {
    const next = Array.from({ length: gen.length + 1 }).fill(0)
    const factor = GF_EXP[i]
    for (let j = 0; j < gen.length; j++) {
      next[j] ^= gen[j]
      next[j + 1] ^= gfMul(gen[j], factor)
    }
    gen = next
  }

  const msg = new Uint8Array(data.length + ecLen)
  msg.set(data, 0)
  for (let i = 0; i < data.length; i++) {
    const coef = msg[i]
    if (coef !== 0) {
      for (let j = 0; j < gen.length; j++) {
        msg[i + j] ^= gfMul(gen[j], coef)
      }
    }
  }
  return msg.slice(data.length)
}

function encodeData(text) {
  const utf8 = Array.from(new TextEncoder().encode(String(text ?? '')))
  let cfg = VERSIONES_L[2]
  for (let v = 2; v < VERSIONES_L.length; v++) {
    if (utf8.length + 2 <= VERSIONES_L[v].dataBytes) {
      cfg = VERSIONES_L[v]
      break
    }
    cfg = VERSIONES_L[v]
  }

  const maxLen = cfg.dataBytes - 2
  const payload = utf8.slice(0, maxLen)
  const bits = []
  const pushBits = (val, len) => {
    for (let i = len - 1; i >= 0; i--) {
      bits.push((val >> i) & 1)
    }
  }

  // Modo Byte (0100) + longitud (8 bits en versiones 1-9)
  pushBits(0b0100, 4)
  pushBits(payload.length, 8)
  for (const b of payload) {
    pushBits(b, 8)
  }

  const totalDataBits = cfg.dataBytes * 8
  const term = Math.min(4, totalDataBits - bits.length)
  pushBits(0, term)
  while (bits.length % 8 !== 0) {
    bits.push(0)
  }

  const dataBytes = new Uint8Array(cfg.dataBytes)
  for (let i = 0; i < bits.length / 8; i++) {
    let byte = 0
    for (let b = 0; b < 8; b++) {
      byte = (byte << 1) | bits[i * 8 + b]
    }
    dataBytes[i] = byte
  }

  const pads = [0xec, 0x11]
  for (let i = bits.length / 8, p = 0; i < cfg.dataBytes; i++, p ^= 1) {
    dataBytes[i] = pads[p]
  }

  const ecBytes = reedSolomon(dataBytes, cfg.ecBytes)
  const allBytes = new Uint8Array(cfg.dataBytes + cfg.ecBytes)
  allBytes.set(dataBytes, 0)
  allBytes.set(ecBytes, cfg.dataBytes)

  return { cfg, allBytes }
}

export function generarMatrizQr(texto = '') {
  const { cfg, allBytes } = encodeData(texto)
  const n = cfg.size
  const grid = Array.from({ length: n }, () => Array.from({ length: n }).fill(false))
  const reserved = Array.from({ length: n }, () => Array.from({ length: n }).fill(false))

  const setModule = (x, y, dark) => {
    if (x >= 0 && x < n && y >= 0 && y < n) {
      grid[y][x] = Boolean(dark)
      reserved[y][x] = true
    }
  }

  const placeFinder = (ox, oy) => {
    for (let dy = -1; dy <= 7; dy++) {
      for (let dx = -1; dx <= 7; dx++) {
        const inOuter = dx >= 0 && dx <= 6 && dy >= 0 && dy <= 6
        const onBorder = dx === 0 || dx === 6 || dy === 0 || dy === 6
        const inInner = dx >= 2 && dx <= 4 && dy >= 2 && dy <= 4
        setModule(ox + dx, oy + dy, inOuter && (onBorder || inInner))
      }
    }
  }

  placeFinder(0, 0)
  placeFinder(n - 7, 0)
  placeFinder(0, n - 7)

  for (let i = 8; i < n - 8; i++) {
    setModule(i, 6, i % 2 === 0)
    setModule(6, i, i % 2 === 0)
  }

  for (const c of cfg.align) {
    for (let dy = -2; dy <= 2; dy++) {
      for (let dx = -2; dx <= 2; dx++) {
        const dark = Math.max(Math.abs(dx), Math.abs(dy)) !== 1
        setModule(c + dx, c + dy, dark)
      }
    }
  }

  // Módulo oscuro fijo y reserva de información de formato
  setModule(8, n - 8, true)
  for (let i = 0; i < 9; i++) {
    if (!reserved[8][i]) reserved[8][i] = true
    if (!reserved[i][8]) reserved[i][8] = true
  }
  for (let i = 0; i < 8; i++) {
    reserved[8][n - 1 - i] = true
    reserved[n - 1 - i][8] = true
  }

  // Colocación de bits en zig-zag con máscara 0: (x + y) % 2 === 0
  let bitIdx = 0
  const totalBits = allBytes.length * 8
  let upward = true

  for (let right = n - 1; right >= 1; right -= 2) {
    if (right === 6) right = 5
    for (let step = 0; step < n; step++) {
      const y = upward ? n - 1 - step : step
      for (let dx = 0; dx < 2; dx++) {
        const x = right - dx
        if (!reserved[y][x]) {
          let bit = 0
          if (bitIdx < totalBits) {
            const byte = allBytes[bitIdx >> 3]
            bit = (byte >> (7 - (bitIdx & 7))) & 1
            bitIdx++
          }
          const masked = (x + y) % 2 === 0 ? bit ^ 1 : bit
          grid[y][x] = Boolean(masked)
        }
      }
    }
    upward = !upward
  }

  // Información de formato para Nivel L (01) y Máscara 0 (000): 0x77c4
  const formatBits = 0x77c4
  for (let i = 0; i < 15; i++) {
    const bit = ((formatBits >> i) & 1) === 1
    if (i < 6) grid[i][8] = bit
    else if (i < 8) grid[i + 1][8] = bit
    else grid[n - 15 + i][8] = bit

    if (i < 8) grid[8][n - 1 - i] = bit
    else if (i < 9) grid[8][15 - i] = bit
    else grid[8][15 - i - 1] = bit
  }

  return grid
}
