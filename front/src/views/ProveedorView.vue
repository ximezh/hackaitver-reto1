<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ANDENES_RECIBO, DURACIONES_CITA, citas, ordenesProveedor } from '@/api'
import Icono from '@/components/Icono.vue'
import { useToast } from '@/composables/useToast'
import { useSesionStore } from '@/stores/sesion'

defineOptions({
  name: 'ProveedorView',
})

const NAV = [
  { id: 'cita', icono: 'calendar', etiqueta: 'Agendar cita' },
  { id: 'fac', icono: 'file', etiqueta: 'Factura y bultos' },
  { id: 'hist', icono: 'history', etiqueta: 'Historial' },
]
const BLOQUES = 20
const ABRE_MIN = 8 * 60
const NOMBRES_DIA = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
const ZONA = 'America/Mexico_City'

const sesion = useSesionStore()
const { visible, mensaje, icono, mostrar } = useToast()

const vista = ref('cita')
const ordenes = ref([])
const ocSeleccionada = ref('')
const folio = ref('')
const folioTocado = ref(false)
const errorFolio = ref('')
const duracion = ref(DURACIONES_CITA[0].minutos)
const semana = ref(0)
const dia = ref('')
const andenes = ref([])
const seleccion = ref(null) // { a, s }
const errorAnden = ref('')
const enviando = ref(false)

const titulo = computed(() => NAV.find((n) => n.id === vista.value)?.etiqueta || '')
const nombreProveedor = computed(() => sesion.usuario?.nombre || 'Proveedor')
const iniciales = computed(() =>
  nombreProveedor.value
    .split(/\s+/)
    .filter((p) => p.length > 3)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join(''),
)

// --- Fechas ---
const hoyIso = () => new Intl.DateTimeFormat('en-CA', { timeZone: ZONA }).format(new Date())
function sumarDias(iso, n) {
  const d = new Date(`${iso}T12:00:00Z`)
  d.setUTCDate(d.getUTCDate() + n)
  return d.toISOString().slice(0, 10)
}
const diaSemana = (iso) => new Date(`${iso}T12:00:00Z`).getUTCDay()

const hoy = hoyIso()
const limite = sumarDias(hoy, 14)
const lunesActual = sumarDias(hoy, -((diaSemana(hoy) + 6) % 7))

const dias = computed(() =>
  Array.from({ length: 6 }, (_, i) => {
    const iso = sumarDias(lunesActual, semana.value * 7 + i)
    return {
      iso,
      nombre: NOMBRES_DIA[diaSemana(iso)],
      numero: Number(iso.slice(8, 10)),
      habil: iso >= hoy && iso <= limite,
    }
  }),
)
const haySemanaAnterior = computed(() => semana.value > 0)
const haySemanaSiguiente = computed(() => sumarDias(lunesActual, (semana.value + 1) * 7) <= limite)

function primerDiaHabil() {
  let d = hoy
  while (diaSemana(d) === 0) d = sumarDias(d, 1)
  return d
}

// --- Calendario ---
const aMin = (hhmm) => Number(hhmm.slice(0, 2)) * 60 + Number(hhmm.slice(3, 5))
const aBloque = (hhmm) => (aMin(hhmm) - ABRE_MIN) / 30
const formatoHora = (bloque) => {
  const min = ABRE_MIN + bloque * 30
  return `${Math.floor(min / 60)}:${min % 60 ? '30' : '00'}`
}
const aHora = (bloque) => {
  const min = ABRE_MIN + bloque * 30
  return `${String(Math.floor(min / 60)).padStart(2, '0')}:${String(min % 60).padStart(2, '0')}`
}
const bloquesDuracion = computed(() => duracion.value / 30)

const ocupados = computed(() =>
  andenes.value.flatMap((an) => {
    const a = ANDENES_RECIBO.indexOf(an.anden)
    return (an.ocupados || []).map((o) => ({
      a,
      s: aBloque(o.inicio),
      d: aBloque(o.fin) - aBloque(o.inicio),
      etiqueta: o.etiqueta,
    }))
  }),
)

const choca = computed(() => {
  const p = seleccion.value
  if (!p) return false
  const d = bloquesDuracion.value
  return (
    p.s + d > BLOQUES || ocupados.value.some((b) => b.a === p.a && p.s < b.s + b.d && b.s < p.s + d)
  )
})

function estiloBloque(a, s, d) {
  return {
    left: `calc(52px + (100% - 52px) * ${a} / 4 + 4px)`,
    width: `calc((100% - 52px) / 4 - 8px)`,
    top: `${37 + s * 24 + 2}px`,
    height: `${Math.min(d, BLOQUES - s) * 24 - 4}px`,
  }
}

// --- Orden y folio ---
const orden = computed(() => ordenes.value.find((o) => o.oc === ocSeleccionada.value) || null)
const folioVacio = computed(() => !folio.value.trim())
const mensajeFolio = computed(() => {
  if (folioVacio.value) return folioTocado.value ? 'El folio es obligatorio' : ''
  return errorFolio.value
})
const diaSeleccionado = computed(() => dias.value.find((d) => d.iso === dia.value))
const horario = computed(() => {
  const p = seleccion.value
  if (!p) return '—'
  const d = diaSeleccionado.value
  const etiqueta = d ? `${d.nombre} ${d.numero}` : dia.value
  return `${etiqueta} · ${formatoHora(p.s)}–${formatoHora(p.s + bloquesDuracion.value)}`
})
const puedeConfirmar = computed(
  () =>
    Boolean(orden.value && seleccion.value && dia.value) &&
    !choca.value &&
    !folioVacio.value &&
    !errorFolio.value &&
    !enviando.value,
)

async function cargarOrdenes() {
  try {
    const data = await ordenesProveedor.listar({ sinCita: true })
    ordenes.value = data?.items || []
    if (!ordenes.value.some((o) => o.oc === ocSeleccionada.value)) {
      ocSeleccionada.value = ordenes.value[0]?.oc || ''
    }
  } catch (e) {
    ordenes.value = []
    mostrar(e?.message || 'No se pudieron cargar las órdenes', 'alert')
  }
}

async function cargarDisponibilidad() {
  if (!dia.value) return
  try {
    const data = await citas.disponibilidad(dia.value)
    andenes.value = data?.andenes || []
  } catch (e) {
    andenes.value = []
    mostrar(e?.message || 'No se pudo cargar la disponibilidad', 'alert')
  }
}

async function verificarFolio() {
  folioTocado.value = true
  errorFolio.value = ''
  if (folioVacio.value || !ocSeleccionada.value) return
  try {
    const r = await citas.verificarFolio({ folio: folio.value.trim(), oc: ocSeleccionada.value })
    errorFolio.value = r?.disponible ? '' : r?.detail || 'Este folio ya está registrado'
  } catch (e) {
    errorFolio.value = e?.campos?.folio || ''
  }
}

function elegirDia(d) {
  if (!d.habil) return
  dia.value = d.iso
}

function cambiarSemana(paso) {
  semana.value += paso
  const primero = dias.value.find((d) => d.habil)
  if (primero) dia.value = primero.iso
}

function elegirCelda(a, s) {
  seleccion.value = { a, s }
  errorAnden.value = ''
}

async function confirmar() {
  if (!puedeConfirmar.value) return
  enviando.value = true
  errorAnden.value = ''
  try {
    await citas.agendar({
      oc: ocSeleccionada.value,
      folio_factura: folio.value.trim().toUpperCase(),
      anden: ANDENES_RECIBO[seleccion.value.a],
      dia: dia.value,
      inicio: aHora(seleccion.value.s),
      duracion_min: duracion.value,
    })
    seleccion.value = null
    folio.value = ''
    folioTocado.value = false
    errorFolio.value = ''
    mostrar('Cita confirmada · QR enviado', 'check')
    await Promise.all([cargarOrdenes(), cargarDisponibilidad()])
  } catch (e) {
    if (e?.codigo === 'anden_ocupado') {
      errorAnden.value = e.message || 'Ese andén ya está ocupado'
      await cargarDisponibilidad()
    } else if (e?.codigo === 'folio_registrado') {
      errorFolio.value = e.message || 'Este folio ya está registrado'
    } else if (e?.campos?.folio_factura) {
      errorFolio.value = e.campos.folio_factura
    } else {
      mostrar(e?.message || 'No se pudo agendar la cita', 'alert')
      if (e?.codigo === 'cita_existente') await cargarOrdenes()
    }
  } finally {
    enviando.value = false
  }
}

watch(dia, () => {
  seleccion.value = null
  errorAnden.value = ''
  cargarDisponibilidad()
})
watch(ocSeleccionada, () => {
  if (folio.value.trim()) verificarFolio()
})

onMounted(async () => {
  dia.value = primerDiaHabil()
  await cargarOrdenes()
})
</script>

<template>
  <div id="scr" class="web web-layout portal-web-placeholder proveedor-view">
    <aside class="side">
      <div class="brand">
        <span class="logo">
          <Icono nombre="cube" :tamano="20" :grosor="2.2" />
        </span>
        CEDIS Flow
      </div>

      <nav id="nav" class="nav">
        <button
          v-for="n in NAV"
          :key="n.id"
          type="button"
          :class="{ on: vista === n.id }"
          :data-v="n.id"
          @click="vista = n.id"
        >
          <Icono :nombre="n.icono" />
          {{ n.etiqueta }}
        </button>
      </nav>

      <div style="margin-top: auto" class="card pad">
        <div class="row">
          <div class="avatar">{{ iniciales }}</div>
          <div class="grow">
            <div class="t-data ellip" style="font-size: 13px">{{ nombreProveedor }}</div>
            <div class="t-cap">Proveedor</div>
          </div>
        </div>
      </div>
    </aside>

    <section class="main">
      <header class="top">
        <h1 id="ttl">{{ titulo }}</h1>
        <label class="field sm" style="width: 260px">
          <span>
            <Icono nombre="search" :tamano="18" />
          </span>
          <input placeholder="Buscar OC o factura" />
        </label>
        <button type="button" class="iconbtn" aria-label="Avisos">
          <Icono nombre="bell" />
        </button>
      </header>

      <div id="ct" class="content">
        <div v-if="vista === 'cita'" class="cols">
          <div style="display: flex; flex-direction: column; gap: 14px">
            <div class="card pad">
              <span class="lbl" style="margin-top: 0">Orden de compra</span>
              <label class="field sm">
                <span>
                  <Icono nombre="file" :tamano="18" />
                </span>
                <select id="oc" v-model="ocSeleccionada" :disabled="!ordenes.length">
                  <option v-if="!ordenes.length" value="">Sin órdenes pendientes</option>
                  <option v-for="o in ordenes" :key="o.oc" :value="o.oc">
                    {{ o.oc }} · {{ o.sucursal?.nombre }}
                  </option>
                </select>
              </label>

              <span class="lbl">Folio de factura</span>
              <label class="field sm" :style="mensajeFolio ? 'border-color: var(--danger)' : ''">
                <span>
                  <Icono nombre="qr" :tamano="18" />
                </span>
                <input
                  id="fac"
                  v-model="folio"
                  placeholder="FAC-A-00000"
                  @change="verificarFolio"
                  @input="errorFolio = ''"
                />
              </label>
              <div v-if="mensajeFolio" id="err-fac" class="err">
                <Icono nombre="alert" :tamano="14" :grosor="2" />
                {{ mensajeFolio }}
              </div>

              <span class="lbl">Tiempo estimado de descarga</span>
              <div id="dur" class="dur">
                <button
                  v-for="d in DURACIONES_CITA"
                  :key="d.minutos"
                  type="button"
                  :class="{ on: duracion === d.minutos }"
                  @click="duracion = d.minutos"
                >
                  {{ d.etiqueta }}
                </button>
              </div>
            </div>

            <div class="card pad sum">
              <div class="t-sub" style="margin-bottom: 4px">Resumen</div>
              <div class="r">
                <span>Destino</span><b>{{ orden?.sucursal?.nombre || '—' }}</b>
              </div>
              <div class="r">
                <span>Bultos</span><b>{{ orden?.bultos ?? '—' }}</b>
              </div>
              <div class="r">
                <span>Andén</span><b>{{ seleccion ? ANDENES_RECIBO[seleccion.a] : '—' }}</b>
              </div>
              <div class="r">
                <span>Horario</span><b>{{ horario }}</b>
              </div>
              <button
                id="ok"
                type="button"
                class="btn primary block"
                style="margin-top: 14px"
                :disabled="!puedeConfirmar"
                @click="confirmar"
              >
                <Icono nombre="check" :tamano="18" />
                Confirmar cita
              </button>
              <div v-if="choca || errorAnden" id="err-anden" class="err">
                <Icono nombre="alert" :tamano="14" :grosor="2" />
                {{ errorAnden || 'Ese andén ya está ocupado' }}
              </div>
            </div>
          </div>

          <div>
            <div class="row" style="justify-content: space-between; align-items: flex-start">
              <div id="days" class="days">
                <button
                  type="button"
                  class="sem"
                  aria-label="Semana anterior"
                  :disabled="!haySemanaAnterior"
                  @click="cambiarSemana(-1)"
                >
                  <Icono nombre="left" :tamano="16" />
                </button>
                <button
                  v-for="d in dias"
                  :key="d.iso"
                  type="button"
                  :data-dia="d.iso"
                  :class="{ on: dia === d.iso }"
                  :disabled="!d.habil"
                  @click="elegirDia(d)"
                >
                  {{ d.nombre }}<b>{{ d.numero }}</b>
                </button>
                <button
                  type="button"
                  class="sem"
                  aria-label="Semana siguiente"
                  :disabled="!haySemanaSiguiente"
                  @click="cambiarSemana(1)"
                >
                  <Icono nombre="right" :tamano="16" />
                </button>
              </div>
              <div class="row t-cap" style="gap: 14px; padding-top: 6px; white-space: nowrap">
                <span class="row" style="gap: 6px">
                  <i class="dot" style="color: #dfe4ee"></i>Ocupado
                </span>
                <span class="row" style="gap: 6px">
                  <i class="dot" style="color: var(--brand-600)"></i>Tu cita
                </span>
              </div>
            </div>

            <div id="cal" class="cal">
              <div class="hd"></div>
              <div v-for="an in ANDENES_RECIBO" :key="an" class="hd">
                <Icono nombre="warehouse" :tamano="14" :grosor="2" />
                Andén {{ an }}
              </div>
              <template v-for="r in BLOQUES" :key="r">
                <div class="hr">{{ (r - 1) % 2 === 0 ? `${8 + (r - 1) / 2}:00` : '' }}</div>
                <div
                  v-for="(an, a) in ANDENES_RECIBO"
                  :key="an"
                  class="c"
                  :class="{ hh: (r - 1) % 2 === 0 }"
                  :data-a="a"
                  :data-s="r - 1"
                  @click="elegirCelda(a, r - 1)"
                ></div>
              </template>
              <div
                v-for="(b, i) in ocupados"
                :key="`o-${i}`"
                class="blk busy"
                :style="estiloBloque(b.a, b.s, b.d)"
              >
                {{ b.etiqueta }}
              </div>
              <div
                v-if="seleccion"
                class="blk"
                :class="choca ? 'bad' : 'mine'"
                :style="estiloBloque(seleccion.a, seleccion.s, bloquesDuracion)"
              >
                {{ orden?.oc || 'Tu cita' }}
              </div>
            </div>
          </div>
        </div>

        <div v-else class="card pad vacia">
          <div class="t-sub">{{ titulo }}</div>
          <div class="t-cap">Esta sección llega en una próxima entrega.</div>
        </div>
      </div>
    </section>

    <div class="toast" :class="{ show: visible }" role="status" aria-live="polite">
      <Icono v-if="icono" :nombre="icono" :tamano="16" :grosor="2.2" />
      <span>{{ mensaje }}</span>
    </div>
  </div>
</template>

<style scoped>
.cols {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 18px;
  height: 100%;
}
.days {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.days button {
  border: 1.5px solid var(--line);
  background: #fff;
  border-radius: 12px;
  width: 62px;
  height: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: var(--ink-muted);
  font-weight: 500;
  cursor: pointer;
}
.days button.sem {
  width: 36px;
}
.days button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.days button b {
  font-size: 17px;
  color: var(--ink);
}
.days button.on {
  border-color: var(--brand-600);
  background: var(--brand-50);
}
.days button.on b {
  color: var(--brand-700);
}
.cal {
  display: grid;
  grid-template-columns: 52px repeat(4, 1fr);
  position: relative;
  border: 1px solid var(--line);
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
}
.cal .hd {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  border-bottom: 1px solid var(--line);
  background: var(--surface-50);
}
.cal .hr {
  height: 24px;
  font-size: 10px;
  color: var(--ink-muted);
  padding: 0 6px;
  text-align: right;
  border-right: 1px solid var(--line);
}
.cal .c {
  height: 24px;
  border-right: 1px solid var(--line);
  cursor: pointer;
}
.cal .c.hh {
  border-top: 1px solid var(--line);
}
.cal .c:hover {
  background: var(--brand-50);
}
.blk {
  position: absolute;
  border-radius: 8px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 600;
  overflow: hidden;
  pointer-events: none;
  line-height: 15px;
}
.blk.busy {
  background: repeating-linear-gradient(135deg, #eef1f6 0 6px, #e5e9f1 6px 12px);
  color: var(--ink-muted);
}
.blk.mine {
  background: var(--brand-600);
  color: #fff;
  box-shadow: var(--shadow-pop);
}
.blk.bad {
  background: var(--danger);
  color: #fff;
}
.sum .r {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--line);
  font-size: 13px;
}
.sum .r span:first-child {
  color: var(--ink-muted);
}
.dur {
  display: flex;
  gap: 6px;
}
.dur button {
  flex: 1;
  height: 36px;
  border-radius: 10px;
  border: 1.5px solid var(--line);
  background: #fff;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
}
.dur button.on {
  border-color: var(--brand-600);
  color: var(--brand-700);
  background: var(--brand-50);
}
.err {
  color: var(--danger);
  font-size: 12px;
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 6px;
}
.vacia {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
</style>
