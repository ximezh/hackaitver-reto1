<script setup>
import Icono from '@/components/Icono.vue'

defineOptions({
  name: 'CampoTexto',
})

defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  tipo: {
    type: String,
    default: 'text',
  },
  icono: {
    type: String,
    default: '',
  },
  iconoTamano: {
    type: [Number, String],
    default: undefined,
  },
  sm: {
    type: Boolean,
    default: false,
  },
  pequeno: {
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
})

defineEmits(['update:modelValue'])
</script>

<template>
  <label class="field" :class="{ sm: sm || pequeno }">
    <span v-if="icono || $slots.icono">
      <slot name="icono">
        <Icono :nombre="icono" :tamano="iconoTamano ?? (sm || pequeno ? 18 : 20)" />
      </slot>
    </span>
    <input
      :type="tipo"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled || deshabilitado"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <slot name="derecha" />
  </label>
</template>
