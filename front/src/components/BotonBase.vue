<script setup>
import { computed } from 'vue'
import Icono from '@/components/Icono.vue'

defineOptions({
  name: 'BotonBase',
})

const props = defineProps({
  variante: {
    type: String,
    default: 'primary',
  },
  variant: {
    type: String,
    default: '',
  },
  sm: {
    type: Boolean,
    default: false,
  },
  pequeno: {
    type: Boolean,
    default: false,
  },
  block: {
    type: Boolean,
    default: false,
  },
  bloque: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  deshabilitado: {
    type: Boolean,
    default: false,
  },
  tipo: {
    type: String,
    default: 'button',
  },
  icono: {
    type: String,
    default: '',
  },
  iconoDerecha: {
    type: String,
    default: '',
  },
  iconoTamano: {
    type: [Number, String],
    default: undefined,
  },
  iconoGrosor: {
    type: [Number, String],
    default: undefined,
  },
})

const varianteFinal = computed(() => props.variant || props.variante || 'primary')
</script>

<template>
  <button
    :type="tipo"
    class="btn"
    :class="[varianteFinal, { sm: sm || pequeno, block: block || bloque }]"
    :disabled="disabled || deshabilitado"
  >
    <Icono v-if="icono" :nombre="icono" :tamano="iconoTamano ?? 20" :grosor="iconoGrosor" />
    <slot />
    <Icono
      v-if="iconoDerecha"
      :nombre="iconoDerecha"
      :tamano="iconoTamano ?? 18"
      :grosor="iconoGrosor"
    />
  </button>
</template>
