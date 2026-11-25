/**
 * Visor local del prototipo (DO-06, hallazgo H-16).
 *
 * Las vistas previas de `design/CEDIS Flow` esperan que su herramienta de diseño les inyecte
 * `tokens.css`, `components/bundle.css` y `components/bundle.js`, y sirva las ilustraciones en
 * `/_blob/<id>`. Este servidor hace lo mismo sin tocar nada dentro de `design/`: solo lee.
 */
import { readFileSync } from 'node:fs'
import { readFile } from 'node:fs/promises'
import { createServer } from 'node:http'
import { extname, join, normalize, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

export const DISENO = resolve(fileURLToPath(new URL('../../design/CEDIS Flow', import.meta.url)))

const TIPOS = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.md': 'text/plain; charset=utf-8',
}

export function cargarManifiesto(carpeta = DISENO) {
  return JSON.parse(readFileSync(join(carpeta, 'manifest.json'), 'utf8'))
}

/** `/_blob/<id>` → ruta del archivo dentro del prototipo, según `manifest.json`. */
export function rutasDeBlobs(manifiesto) {
  const blobs = {}
  for (const [ruta, info] of Object.entries(manifiesto.storage?.files ?? {})) blobs[info.id] = ruta
  return blobs
}

/** Ruta absoluta dentro de `carpeta`, o null si la petición intenta salir de ella. */
export function rutaSegura(carpeta, relativa) {
  const destino = normalize(join(carpeta, decodeURIComponent(relativa)))
  return destino === carpeta || destino.startsWith(carpeta + sep) ? destino : null
}

const INYECCION =
  '<link rel="stylesheet" href="/ds/tokens.css">' +
  '<link rel="stylesheet" href="/ds/components/bundle.css">' +
  '<script src="/ds/components/bundle.js"></script>'

/** Agrega los recursos del sistema de diseño al inicio del <head> de una vista previa. */
export function inyectar(html) {
  return html.includes('<head>')
    ? html.replace('<head>', `<head>${INYECCION}`)
    : INYECCION + html
}

/** Datos de la tarjeta `@dsCard` del comentario inicial: grupo, tamaño y subtítulo. */
export function tarjeta(html) {
  const linea = html.match(/@dsCard([^>]*)-->/)?.[1] ?? ''
  const valor = (clave) => linea.match(new RegExp(`${clave}=(?:"([^"]*)"|(\\d+))`))
  const v = (clave) => {
    const m = valor(clave)
    return m ? (m[1] ?? m[2]) : undefined
  }
  return { grupo: v('group'), alto: v('height'), ancho: v('width'), subtitulo: v('subtitle') }
}

function indice(manifiesto, carpeta) {
  const nombres = [...manifiesto.components.map((c) => c.name), 'Cover']
  const grupos = {}
  for (const nombre of nombres) {
    const html = readFileSync(join(carpeta, 'components', nombre, 'preview.html'), 'utf8')
    const t = tarjeta(html)
    const grupo = t.grupo ?? 'Portada'
    ;(grupos[grupo] ??= []).push({ nombre, ...t })
  }
  const secciones = Object.entries(grupos)
    .map(
      ([grupo, items]) =>
        `<h2>${grupo}</h2><ul>${items
          .map(
            (i) =>
              `<li><a href="/c/${i.nombre}">${i.nombre}</a> <small>${i.subtitulo ?? ''}` +
              `${i.ancho ? ` · ${i.ancho}×${i.alto}` : i.alto ? ` · alto ${i.alto}` : ''}</small></li>`,
          )
          .join('')}</ul>`,
    )
    .join('')
  return `<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Prototipo · CEDIS Flow</title>
<link rel="stylesheet" href="/ds/tokens.css"><link rel="stylesheet" href="/ds/components/bundle.css">
<style>body{padding:32px}h1{font:var(--text-display)}h2{font:var(--text-subtitle);margin-top:24px}
li{margin:6px 0}a{color:var(--brand-700);font-weight:600}small{color:var(--ink-muted)}</style></head>
<body><h1>Prototipo · CEDIS Flow</h1><p>Solo lectura: <code>design/CEDIS Flow</code>. Cada pantalla se abre tal como la dibuja el prototipo.</p>${secciones}</body></html>`
}

export function crearVisor(carpeta = DISENO) {
  const manifiesto = cargarManifiesto(carpeta)
  const blobs = rutasDeBlobs(manifiesto)

  async function enviarArchivo(res, ruta) {
    try {
      const contenido = await readFile(ruta)
      res.writeHead(200, { 'Content-Type': TIPOS[extname(ruta)] ?? 'application/octet-stream' })
      res.end(contenido)
    } catch {
      noEncontrado(res)
    }
  }

  function noEncontrado(res) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' })
    res.end('No encontrado')
  }

  return createServer(async (req, res) => {
    const { pathname } = new URL(req.url, 'http://visor')

    if (pathname === '/') {
      res.writeHead(200, { 'Content-Type': TIPOS['.html'] })
      return res.end(indice(manifiesto, carpeta))
    }

    const componente = pathname.match(/^\/c\/([A-Za-z0-9]+)\/?$/)
    if (componente) {
      const ruta = rutaSegura(carpeta, `components/${componente[1]}/preview.html`)
      try {
        const html = await readFile(ruta, 'utf8')
        res.writeHead(200, { 'Content-Type': TIPOS['.html'] })
        return res.end(inyectar(html))
      } catch {
        return noEncontrado(res)
      }
    }

    const blob = pathname.match(/^\/_blob\/([0-9a-f]+)$/)
    if (blob) return blobs[blob[1]] ? enviarArchivo(res, join(carpeta, blobs[blob[1]])) : noEncontrado(res)

    if (pathname.startsWith('/ds/')) {
      const ruta = rutaSegura(carpeta, pathname.slice('/ds/'.length))
      return ruta ? enviarArchivo(res, ruta) : noEncontrado(res)
    }

    return noEncontrado(res)
  })
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const puerto = Number(process.env.PUERTO ?? 5180)
  crearVisor().listen(puerto, () => {
    console.log(`Prototipo en http://localhost:${puerto}`)
  })
}
