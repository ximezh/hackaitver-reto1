<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { iniciarSesion } from '@/api'
import Icono from '@/components/Icono.vue'
import { useToast } from '@/composables/useToast'
import { ILUSTRACIONES } from '@/utils/cedis'

defineOptions({
  name: 'LoginWebView',
})

const ROLES_WEB = [
  {
    k: 'sucursal',
    n: 'Sucursal',
    i: 'store',
    img: ILUSTRACIONES.sucursal,
    cap: 'Pide y recibe a tiempo',
    u: 'suc07@empresa.mx',
    ruta: '/web/sucursal',
  },
  {
    k: 'proveedor',
    n: 'Proveedor',
    i: 'factory',
    img: ILUSTRACIONES.anden,
    cap: 'Agenda tu cita de entrega',
    u: 'ventas@papeleradelgolfo.mx',
    ruta: '/web/proveedor',
  },
  {
    k: 'oficina',
    n: 'Oficina',
    i: 'grid',
    img: ILUSTRACIONES.datos,
    cap: 'Control total del catálogo',
    u: 'admin.cedis',
    ruta: '/web/oficina',
  },
]

const RUTAS_ROL = {
  sucursal: '/web/sucursal',
  proveedor: '/web/proveedor',
  oficina: '/web/oficina',
  caseta: '/movil/caseta',
  desembarque: '/movil/desembarque',
  embarque: '/movil/embarque',
}

const router = useRouter()
const { visible, mensaje, icono, mostrar } = useToast()

const indiceRol = ref(0)
const usuario = ref('')
const contrasena = ref('')
const recordar = ref(true)

const rolActual = computed(() => ROLES_WEB[indiceRol.value] || ROLES_WEB[0])

async function entrar() {
  if (!usuario.value.trim() || !contrasena.value) {
    mostrar('Revisa usuario y contraseña', 'alert')
    return
  }
  try {
    const sesion = await iniciarSesion({
      usuario: usuario.value,
      contrasena: contrasena.value,
      canal: 'web',
      recordar: recordar.value,
    })
    const destino = RUTAS_ROL[sesion?.usuario?.rol] || rolActual.value.ruta
    if (router) {
      await router.push(destino)
    }
  } catch (error) {
    mostrar(error?.message || 'Revisa usuario y contraseña', 'alert')
  }
}
</script>

<template>
  <div class="stage">
    <div id="scr" class="lw">
      <div class="art">
        <div class="brand" style="color: #fff; padding: 0">
          <span id="lg" class="logo" style="background: #fff; color: var(--brand-600)">
            <Icono nombre="cube" :tamano="20" :grosor="2.2" />
          </span>
          CEDIS Flow
        </div>
        <div class="ill">
          <span class="disc"></span>
          <img id="ill" :src="rolActual.img" alt="" />
        </div>
        <div>
          <div id="cap" class="t-title" style="color: #fff">{{ rolActual.cap }}</div>
          <div id="dots" class="dots" style="margin-top: 12px">
            <i v-for="(r, i) in ROLES_WEB" :key="r.k" :class="{ on: i === indiceRol }"></i>
          </div>
        </div>
      </div>

      <div class="frm">
        <div class="t-display">Inicia sesión</div>
        <div id="roles" class="roles">
          <button
            v-for="(r, i) in ROLES_WEB"
            :key="r.k"
            type="button"
            :class="{ on: i === indiceRol }"
            :data-i="i"
            @click="indiceRol = i"
          >
            <Icono :nombre="r.i" :tamano="24" />
            {{ r.n }}
          </button>
        </div>

        <label class="field">
          <span id="iU">
            <Icono nombre="user" />
          </span>
          <input
            id="u"
            v-model="usuario"
            :placeholder="rolActual.u"
            aria-label="Usuario"
            @keyup.enter="entrar"
          />
        </label>

        <label class="field">
          <span id="iL">
            <Icono nombre="lock" />
          </span>
          <input
            id="p"
            v-model="contrasena"
            type="password"
            placeholder="Contraseña"
            aria-label="Contraseña"
            @keyup.enter="entrar"
          />
        </label>

        <div class="row" style="justify-content: space-between">
          <label class="row t-cap" style="gap: 6px">
            <input v-model="recordar" type="checkbox" /> Recordarme
          </label>
          <a
            class="t-cap"
            style="color: var(--brand-700); font-weight: 600"
            href="#"
            @click.prevent
          >
            ¿Olvidaste tu contraseña?
          </a>
        </div>

        <button id="go" type="button" class="btn primary block" @click="entrar">Entrar</button>
      </div>

      <div class="toast" :class="{ show: visible }" role="status" aria-live="polite">
        <Icono v-if="icono" :nombre="icono" :tamano="16" :grosor="2.2" />
        <span>{{ mensaje }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lw {
  width: 1200px;
  height: 740px;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  box-shadow: var(--shadow-pop);
  background: var(--surface-0);
  position: relative;
}
.art {
  flex: 1.15;
  background: var(--brand-600);
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 36px;
  color: #fff;
  overflow: hidden;
}
.art .ill {
  position: absolute;
  inset: 90px 30px 110px;
  display: grid;
  place-items: center;
}
.art .ill img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: opacity 0.3s;
  position: relative;
}
.art .ill .disc {
  position: absolute;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.95);
}
.dots {
  display: flex;
  gap: 8px;
}
.dots i {
  width: 8px;
  height: 8px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.4);
  transition: 0.2s;
}
.dots i.on {
  width: 26px;
  background: #fff;
}
.frm {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 90px;
  gap: 14px;
}
.roles {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.roles button {
  height: 84px;
  border: 1.5px solid var(--line);
  border-radius: 16px;
  background: var(--surface-0);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-weight: 600;
  font-size: 13px;
  color: var(--ink-muted);
  transition: 0.15s;
}
.roles button.on {
  border-color: var(--brand-600);
  background: var(--brand-50);
  color: var(--brand-700);
}
</style>
