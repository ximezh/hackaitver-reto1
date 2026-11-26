<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { pedidos, productos } from '@/api'
import Icono from '@/components/Icono.vue'
import { useToast } from '@/composables/useToast'
import LayoutWeb from '@/layouts/LayoutWeb.vue'
import { useSesionStore } from '@/stores/sesion'
import { ILUSTRACIONES, formatoKg } from '@/utils/cedis'

defineOptions({
  name: 'SucursalView',
})

const NAV = [
  { id: 'pedir', icono: 'cart', etiqueta: 'Pedir' },
  { id: 'camino', icono: 'truck', etiqueta: 'En camino' },
  { id: 'hist', icono: 'history', etiqueta: 'Historial' },
]

const sesion = useSesionStore()
const { mostrar } = useToast()

const vista = ref('pedir')
const busqueda = ref('')
const catalogo = ref([])
const carrito = reactive({})
const enCurso = ref(0)
const enviando = ref(false)

const sucursal = computed(() => sesion.usuario?.sucursal || null)
const nombreSucursal = computed(
  () => sucursal.value?.nombre || sesion.usuario?.nombre || 'Sucursal',
)
const iniciales = computed(() => sucursal.value?.clave || 'SU')

const navItems = computed(() =>
  NAV.map((n) => ({ ...n, chip: n.id === 'camino' ? enCurso.value : null })),
)
const titulo = computed(() => NAV.find((n) => n.id === vista.value)?.etiqueta || '')

const productosVisibles = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  if (!q) return catalogo.value
  return catalogo.value.filter(
    (p) => p.nombre.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q),
  )
})

const lineas = computed(() =>
  Object.keys(carrito)
    .map((sku) => {
      const producto = catalogo.value.find((p) => p.sku === sku)
      return producto ? { producto, bultos: carrito[sku] } : null
    })
    .filter(Boolean),
)
const totalBultos = computed(() => lineas.value.reduce((acc, l) => acc + l.bultos, 0))
const totalKg = computed(() =>
  lineas.value.reduce((acc, l) => acc + l.bultos * Number(l.producto.kg || 0), 0),
)

function ilustracion(p) {
  return ILUSTRACIONES[p?.ilustracion] || ILUSTRACIONES.bulto
}

function cambiar(sku, delta) {
  const n = (carrito[sku] || 0) + delta
  if (n <= 0) delete carrito[sku]
  else carrito[sku] = n
}

async function cargarEnCurso() {
  try {
    const res = await pedidos.listar({ enCurso: true })
    enCurso.value = res.total ?? res.items?.length ?? 0
  } catch {
    // El conteo es informativo; si falla se queda el anterior
  }
}

async function enviar() {
  if (!totalBultos.value || enviando.value) return
  enviando.value = true
  try {
    const pedido = await pedidos.crear(
      lineas.value.map((l) => ({ sku: l.producto.sku, bultos: l.bultos })),
    )
    for (const sku of Object.keys(carrito)) delete carrito[sku]
    mostrar(`${pedido.folio} enviada al CEDIS`, 'check')
    await cargarEnCurso()
  } catch (error) {
    mostrar(error?.message || 'No se pudo enviar el pedido', 'alert')
  } finally {
    enviando.value = false
  }
}

onMounted(async () => {
  try {
    const res = await productos.listar()
    catalogo.value = res.items || []
  } catch (error) {
    mostrar(error?.message || 'No se pudo cargar el catálogo', 'alert')
  }
  await cargarEnCurso()
})
</script>

<template>
  <LayoutWeb
    :titulo="titulo"
    :nav-items="navItems"
    :nav-activo="vista"
    :usuario-iniciales="iniciales"
    :usuario-nombre="nombreSucursal"
    usuario-rol="Sucursal"
    placeholder-busqueda="Buscar producto o pedido"
    :busqueda="busqueda"
    @update:busqueda="busqueda = $event"
    @navegar="vista = $event"
  >
    <div v-if="vista === 'pedir'" class="cols">
      <div class="cat">
        <div v-for="p in productosVisibles" :key="p.sku" class="card prod" :data-sku="p.sku">
          <div class="im"><img :src="ilustracion(p)" alt="" /></div>
          <div class="t-data ellip">{{ p.nombre }}</div>
          <div class="t-cap">
            {{ p.sku }} · bulto de {{ p.piezas_por_bulto }} {{ p.unidad || 'piezas' }}
          </div>
          <div class="step">
            <button type="button" aria-label="Menos" data-d="-1" @click="cambiar(p.sku, -1)">
              <Icono nombre="minus" :tamano="16" />
            </button>
            <b>{{ carrito[p.sku] || 0 }}</b>
            <button type="button" aria-label="Más" data-d="1" @click="cambiar(p.sku, 1)">
              <Icono nombre="plus" :tamano="16" />
            </button>
          </div>
        </div>
      </div>

      <div>
        <div class="card pad cart" style="position: sticky; top: 0">
          <div class="row">
            <div class="t-sub grow">Tu pedido</div>
            <span class="chip">{{ totalBultos }} bultos</span>
          </div>
          <template v-if="totalBultos">
            <div v-for="l in lineas" :key="l.producto.sku" class="it">
              <span class="thumb" style="width: 36px; height: 36px">
                <img :src="ilustracion(l.producto)" alt="" />
              </span>
              <div class="grow">
                <div class="t-data ellip" style="font-size: 13px">{{ l.producto.nombre }}</div>
                <div class="t-cap">{{ l.bultos }} bultos</div>
              </div>
              <b style="font-size: 13px">{{ formatoKg(l.bultos * Number(l.producto.kg || 0)) }}</b>
            </div>
          </template>
          <div v-else class="t-cap vacio">
            <Icono nombre="cart" :tamano="28" />
            <br />
            Agrega productos
          </div>
          <div class="row" style="justify-content: space-between; margin: 12px 0">
            <span class="muted">Peso estimado</span>
            <b>{{ formatoKg(totalKg) }}</b>
          </div>
          <button
            id="send"
            type="button"
            class="btn primary block"
            :disabled="!totalBultos || enviando"
            @click="enviar"
          >
            <Icono nombre="send" :tamano="18" />
            Enviar pedido
          </button>
        </div>
      </div>
    </div>

    <div v-else class="t-cap vacio">Próximamente</div>
  </LayoutWeb>
</template>

<style scoped>
.cols {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 18px;
}
.cat {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.prod {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.prod .im {
  height: 110px;
  border-radius: 12px;
  background: var(--brand-50);
  display: grid;
  place-items: center;
}
.prod .im img {
  height: 96px;
  max-width: 90%;
  object-fit: contain;
}
.step {
  display: flex;
  align-items: center;
  border: 1.5px solid var(--line);
  border-radius: 12px;
  height: 38px;
  overflow: hidden;
}
.step button {
  width: 38px;
  height: 100%;
  border: 0;
  background: var(--surface-50);
  display: grid;
  place-items: center;
}
.step b {
  flex: 1;
  text-align: center;
}
.cart .it {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--line);
}
.vacio {
  padding: 30px 0;
  text-align: center;
}
</style>
