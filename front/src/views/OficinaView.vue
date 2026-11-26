<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { obtenerIndicadoresOficina, productos, proveedores, sucursales, usuarios } from '@/api'
import Icono from '@/components/Icono.vue'

defineOptions({
  name: 'OficinaView',
})

const CATALOGOS = [
  { k: 'productos', t: 'Productos', i: 'box', servicio: productos },
  { k: 'proveedores', t: 'Proveedores', i: 'factory', servicio: proveedores },
  { k: 'sucursales', t: 'Sucursales', i: 'store', servicio: sucursales },
  { k: 'usuarios', t: 'Usuarios', i: 'users', servicio: usuarios },
]

const actual = ref('productos')
const conteos = reactive({
  productos: 0,
  proveedores: 0,
  sucursales: 0,
  usuarios: 0,
})
const indicadores = ref({
  camiones_recibidos: { valor: 0, total: 0 },
  embarques: { valor: 0, total: 0 },
  recepciones_sin_error: 0,
  racks: [],
})

const catalogoActual = computed(() => CATALOGOS.find((c) => c.k === actual.value) || CATALOGOS[0])

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

async function cargarDatosIniciales() {
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
}

function cambiarCatalogo(clave) {
  actual.value = clave
}

onMounted(() => {
  cargarDatosIniciales()
})
</script>

<template>
  <div id="scr" class="web web-layout">
    <aside class="side">
      <div class="brand">
        <span id="lg" class="logo">
          <Icono nombre="cube" :tamano="20" :grosor="2.2" />
        </span>
        CEDIS Flow
      </div>

      <nav id="nav" class="nav">
        <button
          v-for="cat in CATALOGOS"
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
      </div>
    </section>
  </div>
</template>

<style scoped>
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
</style>
