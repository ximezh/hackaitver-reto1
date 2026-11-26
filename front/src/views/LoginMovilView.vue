<script setup>
import { computed, getCurrentInstance, ref } from 'vue'
import { cerrarSesion, iniciarSesion } from '@/api'
import Icono from '@/components/Icono.vue'
import { useToast } from '@/composables/useToast'
import { ILUSTRACIONES, ROLES_MOVIL, detectarRolMovil } from '@/utils/cedis'

defineOptions({
  name: 'LoginMovilView',
})

const props = defineProps({
  esProduccion: {
    type: Boolean,
    default: () => Boolean(import.meta.env.PROD),
  },
})

const router = getCurrentInstance()?.appContext.config.globalProperties.$router
const { visible, mensaje, icono, mostrar } = useToast()

const usuario = ref('')
const contrasena = ref('')
const mostrarClave = ref(false)
const rolAutenticado = ref('')

const claveDetectada = computed(() => detectarRolMovil(usuario.value))
const rolDetectado = computed(() =>
  claveDetectada.value ? ROLES_MOVIL[claveDetectada.value] : null,
)
const rolBienvenida = computed(() =>
  rolAutenticado.value ? ROLES_MOVIL[rolAutenticado.value] : null,
)
const mostrarDemo = computed(() => !props.esProduccion)

function probarComo(clave) {
  const info = ROLES_MOVIL[clave]
  if (!info) return
  usuario.value = info.u
  contrasena.value = 'cedis2026'
}

async function entrar() {
  if (!usuario.value.trim() || !contrasena.value) {
    mostrar('Revisa usuario y contraseña', 'alert')
    return
  }
  try {
    const sesion = await iniciarSesion({
      usuario: usuario.value,
      contrasena: contrasena.value,
      canal: 'android',
    })
    rolAutenticado.value = sesion?.usuario?.rol || claveDetectada.value || 'caseta'
  } catch (error) {
    mostrar(error?.message || 'Revisa usuario y contraseña', 'alert')
  }
}

function irAModulo() {
  if (rolBienvenida.value && router) {
    router.push(rolBienvenida.value.ruta)
  }
}

function salir() {
  cerrarSesion()
  rolAutenticado.value = ''
}
</script>

<template>
  <div id="scr" class="screen screen-movil login-movil-placeholder">
    <div class="hero">
      <img id="heroImg" :src="ILUSTRACIONES.login" alt="Ilustración de acceso" />
    </div>

    <div class="form">
      <div>
        <div class="t-display">Inicia sesión</div>
        <div class="muted">CEDIS Flow · operación</div>
      </div>

      <label class="field">
        <span id="iU">
          <Icono nombre="user" />
        </span>
        <input
          id="u"
          v-model="usuario"
          placeholder="Usuario"
          autocomplete="off"
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
          :type="mostrarClave ? 'text' : 'password'"
          placeholder="Contraseña"
          aria-label="Contraseña"
          @keyup.enter="entrar"
        />
        <button
          id="eye"
          class="iconbtn ghost"
          type="button"
          aria-label="Mostrar contraseña"
          @click="mostrarClave = !mostrarClave"
        >
          <Icono nombre="eye" />
        </button>
      </label>

      <div id="role" class="role" :class="{ show: Boolean(rolDetectado) }">
        <template v-if="rolDetectado">
          <span class="chip">
            <Icono :nombre="rolDetectado.i" :tamano="14" :grosor="2" />
            {{ rolDetectado.n }}
          </span>
          <span class="t-cap">CEDIS Veracruz</span>
        </template>
      </div>

      <button id="go" type="button" class="btn primary block" @click="entrar">Entrar</button>

      <template v-if="mostrarDemo">
        <div class="t-cap" style="text-align: center; margin-top: 4px">Probar como</div>
        <div id="demo" class="demo">
          <button
            v-for="(info, clave) in ROLES_MOVIL"
            :key="clave"
            type="button"
            :data-k="clave"
            @click="probarComo(clave)"
          >
            <Icono :nombre="info.i" :tamano="22" />
            {{ info.s || info.n }}
          </button>
        </div>
      </template>
    </div>

    <div id="wel" class="welcome" :class="{ show: Boolean(rolBienvenida) }">
      <template v-if="rolBienvenida">
        <div class="badge">
          <Icono :nombre="rolBienvenida.i" :tamano="40" />
        </div>
        <div class="t-title">Bienvenido</div>
        <span class="chip">{{ rolBienvenida.n }}</span>
        <div class="mods">
          <div v-for="mod in rolBienvenida.m" :key="mod[1]" @click="irAModulo">
            <span>
              <Icono :nombre="mod[0]" :tamano="26" />
            </span>
            {{ mod[1] }}
          </div>
        </div>
        <button id="back" type="button" class="btn line" style="margin-top: 18px" @click="salir">
          <Icono nombre="logout" :tamano="18" />
          Salir
        </button>
      </template>
    </div>

    <div class="toast" :class="{ show: visible }" role="status" aria-live="polite">
      <Icono v-if="icono" :nombre="icono" :tamano="16" :grosor="2.2" />
      <span>{{ mensaje }}</span>
    </div>
  </div>
</template>

<style scoped>
.hero {
  height: 250px;
  background: linear-gradient(180deg, var(--brand-50), var(--surface-50));
  display: grid;
  place-items: center;
  position: relative;
}
.hero img {
  width: 230px;
  height: 200px;
  object-fit: contain;
}
.form {
  padding: 4px 22px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.form .field {
  height: 48px;
}
.role {
  height: 34px;
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0;
  transform: translateY(-4px);
  transition: 0.2s;
}
.role.show {
  opacity: 1;
  transform: none;
}
.demo {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 6px;
}
.demo button {
  border: 1px solid var(--line);
  background: var(--surface-0);
  border-radius: 14px;
  width: 96px;
  height: 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 10px;
  font-weight: 600;
  color: var(--ink-muted);
}
.demo button:hover {
  border-color: var(--brand-600);
  color: var(--brand-700);
}
.welcome {
  position: absolute;
  inset: 0;
  background: var(--surface-0);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  opacity: 0;
  pointer-events: none;
  transition: 0.3s;
  z-index: 10;
  padding: 24px;
  text-align: center;
}
.welcome.show {
  opacity: 1;
  pointer-events: auto;
}
.welcome .badge {
  width: 84px;
  height: 84px;
  border-radius: 26px;
  background: var(--brand-600);
  color: #fff;
  display: grid;
  place-items: center;
  animation: pop 0.4s;
}
.mods {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  width: 100%;
  margin-top: 14px;
}
.mods div {
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 14px 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ink);
}
.mods div span {
  color: var(--brand-600);
}
</style>
