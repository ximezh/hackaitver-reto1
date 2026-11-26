<script setup>
import { computed, getCurrentInstance } from 'vue'
import { RouterView } from 'vue-router'
import Icono from '@/components/Icono.vue'
import { useToast } from '@/composables/useToast'

const tieneRouter = Boolean(getCurrentInstance()?.appContext.config.globalProperties.$router)

defineOptions({
  name: 'LayoutWeb',
})

const props = defineProps({
  marca: {
    type: String,
    default: 'CEDIS Flow',
  },
  titulo: {
    type: String,
    default: '',
  },
  navItems: {
    type: Array,
    default: () => [],
  },
  navActivo: {
    type: String,
    default: '',
  },
  usuarioIniciales: {
    type: String,
    default: 'AD',
  },
  usuarioNombre: {
    type: String,
    default: 'Ana Domínguez',
  },
  usuarioRol: {
    type: String,
    default: 'Oficina · Admin',
  },
  mostrarBusqueda: {
    type: Boolean,
    default: true,
  },
  busqueda: {
    type: String,
    default: '',
  },
  placeholderBusqueda: {
    type: String,
    default: 'Buscar',
  },
  mostrarCampana: {
    type: Boolean,
    default: true,
  },
  modalAbierto: {
    type: Boolean,
    default: false,
  },
  toastVisible: {
    type: Boolean,
    default: undefined,
  },
  toastMensaje: {
    type: String,
    default: undefined,
  },
  toastIcono: {
    type: String,
    default: undefined,
  },
})

defineEmits(['navegar', 'update:busqueda', 'avisos', 'cerrar-modal'])

const { visible, mensaje, icono } = useToast()

const avisoVisible = computed(() => props.toastVisible ?? visible.value)
const avisoMensaje = computed(() => props.toastMensaje ?? mensaje.value)
const avisoIcono = computed(() => props.toastIcono ?? icono.value)
</script>

<template>
  <div class="web web-layout">
    <aside class="side">
      <div class="brand">
        <span class="logo">
          <Icono nombre="cube" :tamano="20" :grosor="2.2" />
        </span>
        {{ marca }}
      </div>

      <nav class="nav">
        <slot name="nav">
          <button
            v-for="item in navItems"
            :key="item.id || item.etiqueta || item.label"
            type="button"
            :class="{ on: item.activo || item.on || navActivo === (item.id || item.etiqueta) }"
            @click="$emit('navegar', item.id || item.etiqueta || item.label)"
          >
            <Icono :nombre="item.icono || item.icon || 'box'" :tamano="20" />
            {{ item.etiqueta || item.label }}
            <span
              v-if="item.chip != null"
              class="chip"
              style="margin-left: auto; height: 22px"
            >
              {{ item.chip }}
            </span>
            <span
              v-else-if="item.conteo != null"
              class="t-cap"
              style="margin-left: auto"
            >
              {{ item.conteo }}
            </span>
          </button>
        </slot>
      </nav>

      <div style="margin-top: auto" class="card pad">
        <slot name="usuario">
          <div class="row">
            <div class="avatar">{{ usuarioIniciales }}</div>
            <div class="grow">
              <div class="t-data ellip" style="font-size: 13px">{{ usuarioNombre }}</div>
              <div class="t-cap">{{ usuarioRol }}</div>
            </div>
          </div>
        </slot>
      </div>
    </aside>

    <section class="main">
      <header class="top">
        <slot name="top">
          <h1>{{ titulo }}</h1>
          <slot name="top-extra" />
          <label v-if="mostrarBusqueda" class="field sm" style="width: 260px">
            <span>
              <Icono nombre="search" :tamano="18" />
            </span>
            <input
              :value="busqueda"
              :placeholder="placeholderBusqueda"
              @input="$emit('update:busqueda', $event.target.value)"
            />
          </label>
          <button
            v-if="mostrarCampana"
            type="button"
            class="iconbtn"
            aria-label="Avisos"
            @click="$emit('avisos')"
          >
            <Icono nombre="bell" :tamano="20" />
          </button>
        </slot>
      </header>

      <div class="content">
        <slot>
          <RouterView v-if="tieneRouter" />
        </slot>
      </div>
    </section>

    <div class="modal" :class="{ open: modalAbierto }" @click.self="$emit('cerrar-modal')">
      <div class="body">
        <slot name="modal" />
      </div>
    </div>

    <div class="toast" :class="{ show: avisoVisible }" role="status" aria-live="polite">
      <Icono v-if="avisoIcono" :nombre="avisoIcono" :tamano="16" :grosor="2.2" />
      <span>{{ avisoMensaje }}</span>
    </div>
  </div>
</template>
