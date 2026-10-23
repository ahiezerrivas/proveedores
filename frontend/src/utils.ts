import type { Formulario } from './types'

export const API_ROOT = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace(/\/+$/, '')
export const PROVEEDORES_URL = `${API_ROOT}/proveedores/`
export const CONTRATOS_URL = `${API_ROOT}/contratos/`
export const AUDITORIA_URL = `${API_ROOT}/auditoria/`

export const formatoTarifa = new Intl.NumberFormat('es-CO', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export const formularioVacio: Formulario = {
  proveedor_id: '',
  contrato: '',
  tarifa_mensual: '',
  tarifa_trimestral: '',
  tarifa_semestral: '',
  tarifa_anual: '',
  servicios: '',
  estado: 'Activo',
}

export function formatoTarifaEnEdicion(valor: string) {
  const [entero = '', decimales] = valor.split('.')
  const enteroAgrupado = entero.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return decimales === undefined ? enteroAgrupado : `${enteroAgrupado},${decimales}`
}

export async function respuestaJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const obtenerMensajes = (valor: unknown): string[] => {
      if (typeof valor === 'string') return [valor]
      if (Array.isArray(valor)) return valor.flatMap(obtenerMensajes)
      if (valor && typeof valor === 'object') return Object.values(valor).flatMap(obtenerMensajes)
      return []
    }
    const detail = obtenerMensajes(body).join(' ')
    throw new Error(detail || `Error ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function csrfToken() {
  const value = document.cookie
    .split('; ')
    .find((cookie) => cookie.startsWith('csrftoken='))
    ?.split('=')
    .slice(1)
    .join('=')
  return value ? decodeURIComponent(value) : ''
}
