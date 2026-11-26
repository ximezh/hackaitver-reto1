<script setup>
import { computed } from 'vue'

defineOptions({
  name: 'BarraAvance',
})

const props = defineProps({
  valor: {
    type: Number,
    default: 0,
  },
  tope: {
    type: Number,
    default: 100,
  },
  variante: {
    type: String,
    default: '',
  },
  etiqueta: {
    type: String,
    default: '',
  },
  textoValor: {
    type: String,
    default: '',
  },
  unidad: {
    type: String,
    default: '',
  },
  colorValor: {
    type: String,
    default: '',
  },
  estiloBarra: {
    type: [String, Object],
    default: undefined,
  },
})

const porcentaje = computed(() => {
  if (!props.tope || props.tope <= 0) return 0
  const crudo = (props.valor / props.tope) * 100
  return Math.min(100, Math.max(0, Math.round(crudo * 10) / 10))
})

const resumen = computed(() => {
  if (props.textoValor) return props.textoValor
  const sufijo = props.unidad ? ` ${props.unidad}` : ''
  return `${props.valor.toLocaleString('es-MX')} / ${props.tope.toLocaleString('es-MX')}${sufijo}`
})
</script>

<template>
  <div>
    <div v-if="etiqueta" class="row" style="justify-content: space-between">
      <span class="t-cap">{{ etiqueta }}</span>
      <b :style="colorValor ? { color: colorValor } : undefined">{{ resumen }}</b>
    </div>
    <div class="bar" :class="[variante]" :style="estiloBarra">
      <i :style="{ width: `${porcentaje}%` }"></i>
    </div>
  </div>
</template>
