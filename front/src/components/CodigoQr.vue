<script setup>
import { computed } from 'vue'
import { generarMatrizQr } from '@/utils/qr'

defineOptions({
  name: 'CodigoQr',
})

const props = defineProps({
  texto: {
    type: String,
    default: '',
  },
  text: {
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
  px: {
    type: [Number, String],
    default: undefined,
  },
})

const textoFinal = computed(() => props.texto || props.text || '')
const pxFinal = computed(() => props.tamano ?? props.size ?? props.px ?? 96)
const matriz = computed(() => generarMatrizQr(textoFinal.value))
const n = computed(() => matriz.value.length)

const celdasOscuras = computed(() => {
  const lista = []
  const grid = matriz.value
  for (let y = 0; y < grid.length; y++) {
    for (let x = 0; x < grid[y].length; x++) {
      if (grid[y][x]) {
        lista.push({ key: `${x}-${y}`, x, y })
      }
    }
  }
  return lista
})
</script>

<template>
  <svg
    class="qr"
    :width="pxFinal"
    :height="pxFinal"
    :viewBox="`-1 -1 ${n + 2} ${n + 2}`"
    shape-rendering="crispEdges"
    role="img"
    :aria-label="`Código QR ${textoFinal}`"
  >
    <rect x="-1" y="-1" :width="n + 2" :height="n + 2" fill="#fff" />
    <g fill="#0f1f3d">
      <rect
        v-for="celda in celdasOscuras"
        :key="celda.key"
        :x="celda.x"
        :y="celda.y"
        width="1"
        height="1"
      />
    </g>
  </svg>
</template>
