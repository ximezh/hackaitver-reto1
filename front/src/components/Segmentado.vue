<script setup>
import Icono from '@/components/Icono.vue'

defineOptions({
  name: 'CedisSegmentado',
})

defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  opciones: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['update:modelValue'])

function obtenerValor(op) {
  return op.valor ?? op.value ?? op.id ?? op.etiqueta ?? op.label
}

function obtenerEtiqueta(op) {
  return op.etiqueta ?? op.label ?? op.valor ?? op.value
}
</script>

<template>
  <div class="seg">
    <slot>
      <button
        v-for="op in opciones"
        :key="obtenerValor(op)"
        type="button"
        :class="{ on: Boolean(op.on || op.activo) || obtenerValor(op) === modelValue }"
        @click="$emit('update:modelValue', obtenerValor(op))"
      >
        <Icono
          v-if="op.icono || op.icon"
          :nombre="op.icono || op.icon"
          :tamano="op.iconoTamano ?? 16"
          :grosor="op.iconoGrosor"
        />
        {{ obtenerEtiqueta(op) }}
      </button>
    </slot>
  </div>
</template>
