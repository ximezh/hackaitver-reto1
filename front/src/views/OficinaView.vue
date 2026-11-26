<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  ESTADOS,
  ROLES,
  obtenerIndicadoresOficina,
  productos,
  proveedores,
  sucursales,
  usuarios,
} from '@/api'
import Icono from '@/components/Icono.vue'
import { useToast } from '@/composables/useToast'
import { ILUSTRACIONES } from '@/utils/cedis'

defineOptions({
  name: 'OficinaView',
})

const CATALOGOS = {
  productos: {
    k: 'productos',
    t: 'Productos',
    i: 'box',
    servicio: productos,
    cols: [
      ['sku', 'SKU'],
      ['nombre', 'Producto'],
      ['piezas_por_bulto', 'Piezas/bulto'],
      ['kg', 'Peso bulto (kg)'],
      ['m3', 'Volumen (m³)'],
    ],
  },
  proveedores: {
    k: 'proveedores',
    t: 'Proveedores',
    i: 'factory',
    servicio: proveedores,
    cols: [
      ['rfc', 'RFC'],
      ['nombre', 'Proveedor'],
      ['contacto', 'Contacto'],
      ['telefono', 'Teléfono'],
      ['estado', 'Estado'],
    ],
  },
  sucursales: {
    k: 'sucursales',
    t: 'Sucursales',
    i: 'store',
    servicio: sucursales,
    cols: [
      ['clave', 'Clave'],
      ['nombre', 'Sucursal'],
      ['rack', 'Rack'],
      ['ciudad', 'Ciudad'],
      ['estado', 'Estado'],
    ],
  },
  usuarios: {
    k: 'usuarios',
    t: 'Usuarios',
    i: 'users',
    servicio: usuarios,
    cols: [
      ['usuario', 'Usuario'],
      ['nombre', 'Nombre'],
      ['rol', 'Rol'],
      ['canal', 'Canal'],
      ['estado', 'Estado'],
    ],
  },
}

const { visible, mensaje, icono, mostrar } = useToast()

const actual = ref('productos')
const busqueda = ref('')
const filas = ref([])
const idParpadeo = ref(null)

const conteos = reactive({
  productos: 0,
  proveedores: 0,
  sucursales: 0,
  usuarios: 0,
})

const listaSucursales = ref([])
const listaProveedores = ref([])

const indicadores = ref({
  camiones_recibidos: { valor: 0, total: 0 },
  embarques: { valor: 0, total: 0 },
  recepciones_sin_error: 0,
  racks: [],
})

const modoModal = ref('') // '', 'form', 'eliminar', 'contrasena'
const registroEditando = ref(null)
const registroAEliminar = ref(null)
const usuarioConClave = ref(null)
const formulario = reactive({})
const erroresCampos = reactive({})

const catalogoActual = computed(() => CATALOGOS[actual.value] || CATALOGOS.productos)
const modalAbierto = computed(() => Boolean(modoModal.value))

const kpisDia = computed(() => [
  {
    icono: 'truck',
    etiqueta: 'Camiones recibidos hoy',
    valor: `${indicadores.value.camiones_recibidos.valor} / ${indicadores.value.camiones_recibidos.total}`,
  },
  {
    icono: 'send',
    etiqueta: 'Embarques hoy',
    valor: `${indicadores.value.embarques.valor} / ${indicadores.value.embarques.total}`,
  },
  {
    icono: 'check',
    etiqueta: 'Recepciones sin error',
    valor: `${indicadores.value.recepciones_sin_error}%`,
  },
])

const porcentajeRacks = computed(() => {
  const lista = indicadores.value.racks.slice(0, 32)
  if (!lista.length) return 0
  const ocupadas = lista.reduce((acc, r) => acc + r.ocupadas, 0)
  const capacidadTotal = lista.reduce((acc, r) => acc + (r.capacidad || 32), 0)
  return Math.round((ocupadas / capacidadTotal) * 100)
})

function etiquetaRol(rol) {
  return ROLES.find((r) => r.rol === rol)?.etiqueta || rol
}

function canalDeRol(rol) {
  const info = ROLES.find((r) => r.rol === rol)
  if (!info) return 'Web'
  return info.canal === 'android' ? 'Android' : 'Web'
}

function chipEstado(estado) {
  const clave = String(estado ?? 'activo').toLowerCase()
  return ESTADOS[clave] || { etiqueta: estado, chip: clave === 'activo' ? 'ok' : 'warn' }
}

function limpiarErrores() {
  for (const k of Object.keys(erroresCampos)) {
    delete erroresCampos[k]
  }
}

async function cargarConteosYListas() {
  const [ind, prod, prov, suc, usr] = await Promise.all([
    obtenerIndicadoresOficina(),
    productos.listar(),
    proveedores.listar(),
    sucursales.listar(),
    usuarios.listar(),
  ])
  indicadores.value = ind
  conteos.productos = prod.total
  conteos.proveedores = prov.total
  conteos.sucursales = suc.total
  conteos.usuarios = usr.total
  listaProveedores.value = prov.items
  listaSucursales.value = suc.items
}

async function cargarTabla() {
  const servicio = catalogoActual.value.servicio
  const q = busqueda.value.trim()
  const res = await servicio.listar(q ? { q } : {})
  filas.value = res.items
  if (!q) {
    conteos[actual.value] = res.total
  }
}

async function cambiarCatalogo(clave) {
  actual.value = clave
  busqueda.value = ''
  idParpadeo.value = null
  await cargarTabla()
}

function abrirNuevo() {
  limpiarErrores()
  registroEditando.value = null
  for (const k of Object.keys(formulario)) delete formulario[k]

  for (const [clave] of catalogoActual.value.cols) {
    formulario[clave] = ''
  }
  if (actual.value === 'usuarios') {
    formulario.rol = ROLES[0].rol
    formulario.sucursal_id = ''
    formulario.proveedor_id = ''
    formulario.estado = 'activo'
  } else if (actual.value === 'proveedores' || actual.value === 'sucursales') {
    formulario.estado = 'activo'
  }
  modoModal.value = 'form'
}

function abrirEditar(fila) {
  limpiarErrores()
  registroEditando.value = fila
  for (const k of Object.keys(formulario)) delete formulario[k]

  for (const [clave] of catalogoActual.value.cols) {
    formulario[clave] = fila[clave] ?? ''
  }
  if (actual.value === 'usuarios') {
    formulario.sucursal_id = fila.sucursal_id ?? ''
    formulario.proveedor_id = fila.proveedor_id ?? ''
  }
  modoModal.value = 'form'
}

function abrirEliminar(fila) {
  limpiarErrores()
  registroAEliminar.value = fila
  modoModal.value = 'eliminar'
}

function cerrarModal() {
  modoModal.value = ''
  registroEditando.value = null
  registroAEliminar.value = null
  usuarioConClave.value = null
  limpiarErrores()
}

function construirPayload() {
  const editando = Boolean(registroEditando.value)
  if (actual.value === 'productos') {
    return {
      sku: formulario.sku,
      nombre: formulario.nombre,
      piezas_por_bulto: formulario.piezas_por_bulto,
      kg: formulario.kg,
      m3: formulario.m3,
    }
  }
  if (actual.value === 'proveedores') {
    const datos = {
      rfc: formulario.rfc,
      nombre: formulario.nombre,
      contacto: formulario.contacto,
      telefono: formulario.telefono,
    }
    if (editando && formulario.estado) datos.estado = formulario.estado
    return datos
  }
  if (actual.value === 'sucursales') {
    if (editando) {
      return {
        nombre: formulario.nombre,
        ciudad: formulario.ciudad,
        ...(formulario.estado ? { estado: formulario.estado } : {}),
      }
    }
    return {
      clave: formulario.clave,
      nombre: formulario.nombre,
      ciudad: formulario.ciudad,
    }
  }
  const datosUsuario = {
    usuario: formulario.usuario,
    nombre: formulario.nombre,
    rol: formulario.rol,
  }
  if (formulario.rol === 'sucursal') {
    datosUsuario.sucursal_id = formulario.sucursal_id ? Number(formulario.sucursal_id) : null
  }
  if (formulario.rol === 'proveedor') {
    datosUsuario.proveedor_id = formulario.proveedor_id ? Number(formulario.proveedor_id) : null
  }
  if (editando && formulario.estado) {
    datosUsuario.estado = formulario.estado
  }
  return datosUsuario
}

async function guardarFormulario() {
  limpiarErrores()
  const servicio = catalogoActual.value.servicio
  const editando = Boolean(registroEditando.value)
  try {
    const datos = construirPayload()
    const guardado = editando
      ? await servicio.editar(registroEditando.value.id, datos)
      : await servicio.crear(datos)

    idParpadeo.value = guardado.id
    await Promise.all([cargarConteosYListas(), cargarTabla()])
    mostrar(editando ? 'Cambios guardados' : 'Registro creado', 'check')

    if (!editando && guardado.contrasena_generada) {
      usuarioConClave.value = guardado
      modoModal.value = 'contrasena'
    } else {
      cerrarModal()
    }
  } catch (error) {
    if (error?.campos) {
      Object.assign(erroresCampos, error.campos)
    }
    mostrar(error?.message || 'Revisa los campos', 'alert')
  }
}

async function confirmarEliminar() {
  if (!registroAEliminar.value) return
  const servicio = catalogoActual.value.servicio
  try {
    await servicio.eliminar(registroAEliminar.value.id)
    cerrarModal()
    await Promise.all([cargarConteosYListas(), cargarTabla()])
    mostrar('Registro eliminado', 'check')
  } catch (error) {
    mostrar(error?.message || 'No se pudo eliminar', 'alert')
  }
}

onMounted(async () => {
  try {
    await Promise.all([cargarConteosYListas(), cargarTabla()])
  } catch {
    // Ignorar cuando se monta sin sesión en pruebas de rutas
  }
})
</script>

<template>
  <div id="scr" class="web web-layout portal-web-placeholder">
    <aside class="side">
      <div class="brand">
        <span id="lg" class="logo">
          <Icono nombre="cube" :tamano="20" :grosor="2.2" />
        </span>
        CEDIS Flow
      </div>

      <nav id="nav" class="nav">
        <button
          v-for="cat in Object.values(CATALOGOS)"
          :key="cat.k"
          type="button"
          :class="{ on: actual === cat.k }"
          :data-k="cat.k"
          @click="cambiarCatalogo(cat.k)"
        >
          <Icono :nombre="cat.i" />
          {{ cat.t }}
          <span class="t-cap" style="margin-left: auto">{{ conteos[cat.k] }}</span>
        </button>
      </nav>

      <div style="margin-top: auto" class="card pad">
        <div class="row">
          <div class="avatar">AD</div>
          <div class="grow">
            <div class="t-data" style="font-size: 13px">Ana Domínguez</div>
            <div class="t-cap">Oficina · Admin</div>
          </div>
        </div>
      </div>
    </aside>

    <section class="main">
      <header class="top">
        <h1 id="ttl">{{ catalogoActual.t }}</h1>
        <span id="dt" class="chip mute">
          <Icono nombre="calendar" :tamano="14" :grosor="2" />
          Mié 25 nov
        </span>
        <button id="bell" type="button" class="iconbtn" aria-label="Avisos">
          <Icono nombre="bell" />
        </button>
      </header>

      <div class="content">
        <div id="kpis" class="kpis">
          <div v-for="k in kpisDia" :key="k.etiqueta" class="card kpi">
            <span class="ic">
              <Icono :nombre="k.icono" :tamano="22" />
            </span>
            <div>
              <div class="t-cap">{{ k.etiqueta }}</div>
              <div class="t-data" style="font-size: 17px">{{ k.valor }}</div>
            </div>
          </div>

          <div class="card kpi" style="display: block">
            <div class="row" style="justify-content: space-between">
              <span class="t-cap">Ocupación de racks</span>
              <b style="font-size: 13px">{{ porcentajeRacks }}%</b>
            </div>
            <div class="racks" style="grid-template-columns: repeat(16, 1fr)">
              <i
                v-for="r in indicadores.racks.slice(0, 32)"
                :key="r.rack"
                :title="`${r.ocupadas}/${r.capacidad}`"
              >
                <b :style="{ height: `${(r.ocupadas / r.capacidad) * 100}%` }"></b>
              </i>
            </div>
          </div>
        </div>

        <div class="card" style="overflow: hidden">
          <div class="bar2">
            <label class="field sm" style="width: 300px">
              <span id="is">
                <Icono nombre="search" :tamano="18" />
              </span>
              <input id="q" v-model="busqueda" placeholder="Buscar" @input="cargarTabla" />
            </label>
            <span id="cnt" class="t-cap grow">{{ filas.length }} registros</span>
            <button id="new" type="button" class="btn primary sm" @click="abrirNuevo">
              <Icono nombre="plus" :tamano="16" />
              Nuevo
            </button>
          </div>

          <div id="tb">
            <table class="tbl">
              <thead>
                <tr>
                  <th v-for="col in catalogoActual.cols" :key="col[0]">{{ col[1] }}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="fila in filas" :key="fila.id" :class="{ flash: fila.id === idParpadeo }">
                  <td v-for="(col, j) in catalogoActual.cols" :key="col[0]">
                    <template v-if="col[0] === 'estado'">
                      <span class="chip" :class="chipEstado(fila.estado).chip">
                        <span class="dot"></span>
                        {{ chipEstado(fila.estado).etiqueta }}
                      </span>
                    </template>
                    <template v-else-if="j === 1 && actual === 'productos'">
                      <div class="row" style="gap: 10px">
                        <span class="thumb" style="width: 34px; height: 34px">
                          <img
                            :src="ILUSTRACIONES[fila.ilustracion || 'bulto'] || ILUSTRACIONES.bulto"
                            alt=""
                          />
                        </span>
                        {{ fila.nombre }}
                      </div>
                    </template>
                    <template v-else-if="col[0] === 'rol' && actual === 'usuarios'">
                      {{ etiquetaRol(fila.rol) }}
                    </template>
                    <template v-else-if="col[0] === 'canal' && actual === 'usuarios'">
                      {{ canalDeRol(fila.rol) }}
                    </template>
                    <template v-else-if="j === 0">
                      <b>{{ fila[col[0]] }}</b>
                    </template>
                    <template v-else>
                      {{ fila[col[0]] }}
                    </template>
                  </td>
                  <td>
                    <div class="acts">
                      <button
                        type="button"
                        class="ed"
                        aria-label="Editar"
                        @click="abrirEditar(fila)"
                      >
                        <Icono nombre="edit" :tamano="16" />
                      </button>
                      <button
                        type="button"
                        class="del"
                        aria-label="Eliminar"
                        @click="abrirEliminar(fila)"
                      >
                        <Icono nombre="trash" :tamano="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <div id="md" class="modal" :class="{ open: modalAbierto }" @click.self="cerrarModal">
      <div id="mdb" class="body">
        <template v-if="modoModal === 'form'">
          <div class="row">
            <span class="kpi" style="padding: 0">
              <span
                class="ic"
                style="
                  width: 44px;
                  height: 44px;
                  border-radius: 12px;
                  display: grid;
                  place-items: center;
                  background: var(--brand-50);
                  color: var(--brand-700);
                "
              >
                <Icono :nombre="registroEditando ? 'edit' : 'plus'" :tamano="22" />
              </span>
            </span>
            <div class="grow">
              <div class="t-title">{{ registroEditando ? 'Editar' : 'Nuevo' }}</div>
              <div class="t-cap">{{ catalogoActual.t }}</div>
            </div>
            <button
              id="cx"
              type="button"
              class="iconbtn ghost"
              aria-label="Cerrar"
              @click="cerrarModal"
            >
              <Icono nombre="x" />
            </button>
          </div>

          <div class="grid2">
            <div v-for="col in catalogoActual.cols" :key="col[0]">
              <span class="lbl">{{ col[1] }}</span>
              <label class="field sm">
                <select
                  v-if="actual === 'usuarios' && col[0] === 'rol'"
                  v-model="formulario.rol"
                  data-f="rol"
                >
                  <option v-for="r in ROLES" :key="r.rol" :value="r.rol">
                    {{ r.etiqueta }}
                  </option>
                </select>
                <input
                  v-else-if="actual === 'usuarios' && col[0] === 'canal'"
                  data-f="canal"
                  :value="canalDeRol(formulario.rol)"
                  readonly
                />
                <input
                  v-else-if="actual === 'sucursales' && col[0] === 'rack'"
                  data-f="rack"
                  :value="formulario.clave ? `R-${formulario.clave}` : ''"
                  readonly
                />
                <select v-else-if="col[0] === 'estado'" v-model="formulario.estado" data-f="estado">
                  <option
                    v-for="(info, claveEstado) in ESTADOS"
                    :key="claveEstado"
                    :value="claveEstado"
                  >
                    {{ info.etiqueta }}
                  </option>
                </select>
                <input
                  v-else
                  v-model="formulario[col[0]]"
                  :data-f="col[0]"
                  :disabled="
                    Boolean(registroEditando && actual === 'sucursales' && col[0] === 'clave')
                  "
                />
              </label>
              <small v-if="erroresCampos[col[0]]" :data-err="col[0]" class="err-campo">
                {{ erroresCampos[col[0]] }}
              </small>
            </div>

            <div v-if="actual === 'usuarios' && formulario.rol === 'sucursal'">
              <span class="lbl">Sucursal</span>
              <label class="field sm">
                <select v-model="formulario.sucursal_id" data-f="sucursal_id">
                  <option value="">Seleccionar</option>
                  <option v-for="s in listaSucursales" :key="s.id" :value="s.id">
                    {{ s.nombre }}
                  </option>
                </select>
              </label>
              <small v-if="erroresCampos.sucursal_id" data-err="sucursal_id" class="err-campo">
                {{ erroresCampos.sucursal_id }}
              </small>
            </div>

            <div v-if="actual === 'usuarios' && formulario.rol === 'proveedor'">
              <span class="lbl">Proveedor</span>
              <label class="field sm">
                <select v-model="formulario.proveedor_id" data-f="proveedor_id">
                  <option value="">Seleccionar</option>
                  <option v-for="p in listaProveedores" :key="p.id" :value="p.id">
                    {{ p.nombre }}
                  </option>
                </select>
              </label>
              <small v-if="erroresCampos.proveedor_id" data-err="proveedor_id" class="err-campo">
                {{ erroresCampos.proveedor_id }}
              </small>
            </div>
          </div>

          <div class="row" style="justify-content: flex-end; margin-top: 20px">
            <button id="cn" type="button" class="btn line" @click="cerrarModal">Cancelar</button>
            <button id="sv" type="button" class="btn primary" @click="guardarFormulario">
              <Icono nombre="check" :tamano="18" />
              Guardar
            </button>
          </div>
        </template>

        <template v-else-if="modoModal === 'eliminar'">
          <div style="text-align: center">
            <div
              style="
                width: 64px;
                height: 64px;
                border-radius: 20px;
                background: var(--danger-50);
                color: var(--danger);
                display: grid;
                place-items: center;
                margin: 0 auto 12px;
              "
            >
              <Icono nombre="trash" :tamano="30" />
            </div>
            <div class="t-title">¿Eliminar?</div>
            <div class="muted" style="margin: 4px 0 18px">{{ registroAEliminar?.nombre }}</div>
            <div class="row" style="justify-content: center">
              <button id="cn" type="button" class="btn line" @click="cerrarModal">Cancelar</button>
              <button
                id="dl"
                type="button"
                class="btn"
                style="background: var(--danger); color: #fff"
                @click="confirmarEliminar"
              >
                <Icono nombre="trash" :tamano="18" />
                Eliminar
              </button>
            </div>
          </div>
        </template>

        <template v-else-if="modoModal === 'contrasena'">
          <div style="text-align: center">
            <div
              style="
                width: 64px;
                height: 64px;
                border-radius: 20px;
                background: var(--brand-50);
                color: var(--brand-700);
                display: grid;
                place-items: center;
                margin: 0 auto 12px;
              "
            >
              <Icono nombre="lock" :tamano="30" />
            </div>
            <div class="t-title">Contraseña temporal</div>
            <div class="muted" style="margin: 4px 0 12px">
              {{ usuarioConClave?.usuario }}
            </div>
            <div class="card pad t-data" style="margin-bottom: 18px; font-size: 18px">
              {{ usuarioConClave?.contrasena_generada }}
            </div>
            <div class="row" style="justify-content: center">
              <button id="ok-pass" type="button" class="btn primary" @click="cerrarModal">
                Entendido
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div class="toast" :class="{ show: visible }" role="status" aria-live="polite">
      <Icono v-if="icono" :nombre="icono" :tamano="16" :grosor="2.2" />
      <span>{{ mensaje }}</span>
    </div>
  </div>
</template>

<style scoped>
.bar2 {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 14px 16px;
}
.racks {
  display: grid;
  grid-template-columns: repeat(16, 1fr);
  gap: 4px;
  margin-top: 8px;
}
.racks i {
  height: 18px;
  border-radius: 4px;
  background: var(--brand-100);
  position: relative;
  overflow: hidden;
}
.racks i b {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--brand-600);
}
.acts {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
}
.acts button {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid var(--line);
  background: #fff;
  display: grid;
  place-items: center;
  color: var(--ink-muted);
}
.acts button.del:hover {
  color: var(--danger);
  border-color: var(--danger);
}
.acts button.ed:hover {
  color: var(--brand-600);
  border-color: var(--brand-600);
}
.grid2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}
.err-campo {
  color: var(--danger);
  font-size: 11px;
  display: block;
  margin-top: 4px;
}
tr.flash td {
  animation: fl 1.4s;
}
@keyframes fl {
  0% {
    background: var(--brand-50);
  }
  100% {
    background: transparent;
  }
}
</style>
