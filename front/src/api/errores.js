/**
 * Error de la API con una forma única para todas las pantallas.
 * El back responde `{ detail, code }` y, en validación, `campos` (docs/api/README.md). Si llega
 * el formato por defecto de FastAPI (`detail` como lista), se junta igual por campo.
 * Las pantallas deciden con `codigo`, nunca con el mensaje.
 */
export class ErrorApi extends Error {
  constructor({ estado, codigo, mensaje, campos = {} }) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
    this.codigo = codigo
    this.campos = campos
  }
}

const MENSAJES = {
  sin_conexion: 'No hay conexión con el servidor',
  tiempo_agotado: 'El servidor tardó demasiado en responder',
  error_servidor: 'Ocurrió un error en el servidor',
}

function desdeValidacion(detalle) {
  const campos = {}
  for (const item of detalle) {
    const campo = Array.isArray(item.loc) ? item.loc.at(-1) : 'general'
    campos[campo] = item.msg
  }
  return { mensaje: Object.values(campos).join('. '), campos }
}

/** Convierte cualquier error de Axios en un `ErrorApi`. */
export function normalizarError(error) {
  if (error instanceof ErrorApi) return error

  const respuesta = error?.response
  if (!respuesta) {
    const codigo = error?.code === 'ECONNABORTED' ? 'tiempo_agotado' : 'sin_conexion'
    return new ErrorApi({ estado: 0, codigo, mensaje: MENSAJES[codigo] })
  }

  const { status, data } = respuesta
  if (Array.isArray(data?.detail)) {
    const { mensaje, campos } = desdeValidacion(data.detail)
    return new ErrorApi({ estado: status, codigo: 'validacion', mensaje, campos })
  }

  const codigo = data?.code ?? (status >= 500 ? 'error_servidor' : `http_${status}`)
  const mensaje = data?.detail ?? MENSAJES.error_servidor
  // Validación del back (contrato, docs/api/README.md): `campos` trae el mensaje de cada campo.
  const campos = data?.campos && typeof data.campos === 'object' ? data.campos : {}
  return new ErrorApi({ estado: status, codigo, mensaje, campos })
}
