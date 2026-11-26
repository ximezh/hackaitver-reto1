<script setup>
import { computed } from 'vue'
import { ICONOS } from '@/utils/cedis'

defineOptions({
  name: 'CedisIcono',
})

const props = defineProps({
  nombre: {
    type: String,
    default: '',
  },
  name: {
    type: String,
    default: '',
  },
  tamano: {
    type: [Number, String],
    default: undefined,
  },
  size: {
    type: [Number, String],
    default: undefined,
  },
  grosor: {
    type: [Number, String],
    default: undefined,
  },
  sw: {
    type: [Number, String],
    default: undefined,
  },
  strokeWidth: {
    type: [Number, String],
    default: undefined,
  },
})

const clave = computed(() => props.nombre || props.name || 'box')
const trazo = computed(() => ICONOS[clave.value] || ICONOS.box)
const medida = computed(() => props.tamano ?? props.size ?? 20)
const anchoTrazo = computed(() => props.grosor ?? props.sw ?? props.strokeWidth ?? 1.8)
</script>

<template>
  <svg
    :width="medida"
    :height="medida"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="anchoTrazo"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="trazo" />
  </svg>
</template>
