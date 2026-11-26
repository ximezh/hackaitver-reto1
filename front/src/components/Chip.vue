<script setup>
import { computed } from 'vue'
import Icono from '@/components/Icono.vue'

defineOptions({
  name: 'CedisChip',
})

const props = defineProps({
  variante: {
    type: String,
    default: 'normal',
  },
  variant: {
    type: String,
    default: '',
  },
  punto: {
    type: Boolean,
    default: false,
  },
  dot: {
    type: Boolean,
    default: false,
  },
  icono: {
    type: String,
    default: '',
  },
  iconoTamano: {
    type: [Number, String],
    default: 14,
  },
  iconoGrosor: {
    type: [Number, String],
    default: 2,
  },
})

const claseVariante = computed(() => {
  const v = props.variant || props.variante || 'normal'
  return v === 'normal' ? '' : v
})
</script>

<template>
  <span class="chip" :class="[claseVariante]">
    <span v-if="punto || dot" class="dot"></span>
    <Icono v-if="icono" :nombre="icono" :tamano="iconoTamano" :grosor="iconoGrosor" />
    <slot />
  </span>
</template>
