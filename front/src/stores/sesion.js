import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  cambiarContrasena,
  cerrarSesion,
  configurarHttp,
  haySesion,
  iniciarSesion,
  obtenerPerfil,
} from '@/api'

export const RUTAS_INICIO_ROL = {
  oficina: '/web/oficina',
  sucursal: '/web/sucursal',
  proveedor: '/web/proveedor',
  caseta: '/movil/caseta',
  desembarque: '/movil/desembarque',
  embarque: '/movil/embarque',
}

export function obtenerRutaInicioRol(rol) {
  return RUTAS_INICIO_ROL[rol] || '/login'
}

export const useSesionStore = defineStore('sesion', () => {
  const usuario = ref(null)
  const contrasenaTemporal = ref(false)
  const cambioContrasenaRequerido = ref(false)

  const rol = computed(() => usuario.value?.rol || '')
  const canal = computed(() => usuario.value?.canal || '')
  const nombreUsuario = computed(() => usuario.value?.usuario || '')
  const autenticado = computed(() => Boolean(usuario.value) && haySesion())
  const rutaInicio = computed(() => obtenerRutaInicioRol(rol.value))

  function limpiarEstado() {
    usuario.value = null
    contrasenaTemporal.value = false
    cambioContrasenaRequerido.value = false
  }

  configurarHttp({
    alNoAutorizado: () => {
      limpiarEstado()
    },
    alCambioContrasena: () => {
      contrasenaTemporal.value = true
      cambioContrasenaRequerido.value = true
    },
  })

  async function entrar({ usuario: nombre, contrasena, canal: canalAcceso, recordar = false }) {
    const data = await iniciarSesion({
      usuario: nombre,
      contrasena,
      canal: canalAcceso,
      recordar,
    })
    usuario.value = data.usuario
    contrasenaTemporal.value = Boolean(data.contrasena_temporal)
    cambioContrasenaRequerido.value = Boolean(data.contrasena_temporal)
    return data
  }

  async function cargarPerfil() {
    if (!haySesion()) {
      limpiarEstado()
      return null
    }
    try {
      const perfil = await obtenerPerfil()
      usuario.value = perfil
      contrasenaTemporal.value = Boolean(perfil.contrasena_temporal)
      return perfil
    } catch {
      limpiarEstado()
      return null
    }
  }

  async function actualizarContrasena({ actual, nueva }) {
    const data = await cambiarContrasena({ actual, nueva })
    usuario.value = data.usuario
    contrasenaTemporal.value = Boolean(data.contrasena_temporal)
    cambioContrasenaRequerido.value = false
    return data
  }

  function salir() {
    cerrarSesion()
    limpiarEstado()
  }

  return {
    usuario,
    contrasenaTemporal,
    cambioContrasenaRequerido,
    rol,
    canal,
    nombreUsuario,
    autenticado,
    rutaInicio,
    entrar,
    cargarPerfil,
    actualizarContrasena,
    salir,
  }
})
