export type Estado = 'Activo' | 'Pendiente' | 'Inactivo'

export type Proveedor = {
  id: number
  codigo: string
  nombre: string
}

export type Contrato = {
  id: number
  proveedor: Proveedor
  contrato: string
  tarifa_mensual: string
  tarifa_trimestral: string
  tarifa_semestral: string
  tarifa_anual: string
  servicios: string
  estado: Estado
  tiene_pdf: boolean
  pdf_url: string | null
}

export type Formulario = Omit<Contrato, 'id' | 'proveedor' | 'tiene_pdf' | 'pdf_url'> & {
  proveedor_id: string
}
export type TarifaCampo = 'tarifa_mensual' | 'tarifa_trimestral' | 'tarifa_semestral' | 'tarifa_anual'

export type Usuario = {
  id: number
  username: string
  first_name: string
  last_name: string
  is_superuser: boolean
  roles: string[]
  permisos: string[]
}

export type RegistroAuditoria = {
  id: number
  nombre_usuario: string
  accion: string
  accion_display: string
  descripcion: string
  metodo: string
  ruta: string
  codigo_estado: number
  direccion_ip: string | null
  fecha: string
}
