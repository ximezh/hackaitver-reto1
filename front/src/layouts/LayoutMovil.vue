<script setup>
import { computed } from 'vue'
import Icono from '@/components/Icono.vue'
import { useToast } from '@/composables/useToast'

defineOptions({
  name: 'LayoutMovil',
})

const props = defineProps({
  titulo: {
    type: String,
    default: '',
  },
  subtitulo: {
    type: String,
    default: '',
  },
  sobretitulo: {
    type: String,
    default: '',
  },
  avatar: {
    type: String,
    default: '',
  },
  mostrarRegresar: {
    type: Boolean,
    default: false,
  },
  mostrarCampana: {
    type: Boolean,
    default: false,
  },
  tabs: {
    type: Array,
    default: () => [],
  },
  tabActivo: {
    type: String,
    default: '',
  },
  mostrarFab: {
    type: Boolean,
    default: false,
  },
  fabIcono: {
    type: String,
    default: '',
  },
  fabLabel: {
    type: String,
    default: 'Escanear',
  },
  sheetAbierto: {
    type: Boolean,
    default: false,
  },
  sheetOpen: {
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

defineEmits(['regresar', 'avisos', 'cambiar-tab', 'fab', 'cerrar-sheet'])

const { visible, mensaje, icono } = useToast()

const hojaAbierta = computed(() => props.sheetAbierto || props.sheetOpen)
const avisoVisible = computed(() => props.toastVisible ?? visible.value)
const avisoMensaje = computed(() => props.toastMensaje ?? mensaje.value)
const avisoIcono = computed(() => props.toastIcono ?? icono.value)
const tieneFab = computed(() => props.mostrarFab || Boolean(props.fabIcono))
</script>

<template>
  <div class="screen screen-movil">
    <header class="appbar">
      <slot name="appbar">
        <slot name="appbar-left">
          <button
            v-if="mostrarRegresar"
            type="button"
            class="iconbtn"
            aria-label="Regresar"
            @click="$emit('regresar')"
          >
            <Icono nombre="left" />
          </button>
          <div v-else-if="avatar" class="avatar">{{ avatar }}</div>
        </slot>

        <div class="grow">
          <div v-if="sobretitulo" class="t-cap">{{ sobretitulo }}</div>
          <h1 style="font-size: 18px; line-height: 24px">{{ titulo }}</h1>
          <div v-if="subtitulo" class="sub">{{ subtitulo }}</div>
        </div>

        <slot name="appbar-right">
          <button
            v-if="mostrarCampana"
            type="button"
            class="iconbtn"
            aria-label="Avisos"
            @click="$emit('avisos')"
          >
            <Icono nombre="bell" />
          </button>
        </slot>
      </slot>
    </header>

    <main class="scroll">
      <slot />
    </main>

    <slot name="fab">
      <button
        v-if="tieneFab"
        type="button"
        class="fab"
        :aria-label="fabLabel"
        @click="$emit('fab')"
      >
        <Icono :nombre="fabIcono || 'qr'" :tamano="28" />
      </button>
    </slot>

    <slot name="tabbar">
      <nav v-if="tabs && tabs.length" class="tabbar">
        <button
          v-for="tab in tabs"
          :key="tab.id || tab.etiqueta || tab.label"
          type="button"
          :class="{ on: tab.activo || tab.on || tabActivo === (tab.id || tab.etiqueta) }"
          @click="$emit('cambiar-tab', tab.id || tab.etiqueta || tab.label)"
        >
          <span class="pill">
            <Icono :nombre="tab.icono || tab.icon || 'home'" :tamano="20" />
          </span>
          {{ tab.etiqueta || tab.label }}
        </button>
      </nav>
    </slot>

    <div class="sheet" :class="{ open: hojaAbierta }" @click.self="$emit('cerrar-sheet')">
      <div class="body">
        <div class="grab"></div>
        <slot name="sheet" />
      </div>
    </div>

    <div class="toast" :class="{ show: avisoVisible }" role="status" aria-live="polite">
      <Icono v-if="avisoIcono" :nombre="avisoIcono" :tamano="16" :grosor="2.2" />
      <span>{{ avisoMensaje }}</span>
    </div>
  </div>
</template>
