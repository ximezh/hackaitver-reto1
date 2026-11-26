import { ref } from 'vue'

export const DURACION_TOAST = 1900

const visible = ref(false)
const mensaje = ref('')
const icono = ref('')
let temporizador = null

export function useToast() {
  function ocultar() {
    if (temporizador) {
      clearTimeout(temporizador)
      temporizador = null
    }
    visible.value = false
  }

  function mostrar(texto, nombreIcono = 'check', duracion = DURACION_TOAST) {
    if (temporizador) {
      clearTimeout(temporizador)
      temporizador = null
    }
    mensaje.value = String(texto ?? '')
    icono.value = nombreIcono || ''
    visible.value = true
    temporizador = setTimeout(() => {
      visible.value = false
      temporizador = null
    }, duracion)
  }

  return {
    visible,
    mensaje,
    icono,
    duracion: DURACION_TOAST,
    mostrar,
    show: mostrar,
    toast: mostrar,
    ocultar,
    hide: ocultar,
  }
}
