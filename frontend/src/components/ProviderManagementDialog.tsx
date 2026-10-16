import { useEffect, useRef } from 'react'
import type { Proveedor } from '../types'

type ProviderManagementDialogProps = {
  open: boolean
  proveedores: Proveedor[]
  contratosPorProveedor: Map<number, number>
  eliminandoId: number | null
  puedeEliminar: boolean
  error: string
  onClose: () => void
  onDelete: (proveedor: Proveedor) => void
}

export default function ProviderManagementDialog({
  open,
  proveedores,
  contratosPorProveedor,
  eliminandoId,
  puedeEliminar,
  error,
  onClose,
  onDelete,
}: ProviderManagementDialogProps) {
  const dialog = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const elemento = dialog.current
    if (!elemento) return
    if (open && !elemento.open) elemento.showModal()
    if (!open && elemento.open) elemento.close()
  }, [open])

  return (
    <dialog
      ref={dialog}
      className="provider-dialog"
      aria-labelledby="provider-management-title"
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
      onClick={(event) => {
        if (event.target === dialog.current) onClose()
      }}
    >
      <section className="form-card provider-management">
        <div className="section-heading">
          <div>
            <h2 id="provider-management-title">{puedeEliminar ? 'Administrar proveedores' : 'Proveedores registrados'}</h2>
            <p>{puedeEliminar ? 'Solo se pueden eliminar proveedores que no tengan contratos asociados.' : 'Consulta los proveedores y sus contratos asociados.'}</p>
          </div>
          <button className="dialog-close" type="button" aria-label="Cerrar" onClick={onClose}>×</button>
        </div>
        {error && <div className="error-banner" role="alert">{error}</div>}
        {proveedores.length === 0 ? (
          <p className="provider-management-empty">No hay proveedores registrados.</p>
        ) : (
          <ul className="provider-management-list">
            {proveedores.map((proveedor) => {
              const totalContratos = contratosPorProveedor.get(proveedor.id) ?? 0
              const eliminando = eliminandoId === proveedor.id
              return (
                <li key={proveedor.id} className="provider-management-item">
                  <div>
                    <strong>{proveedor.nombre || 'Proveedor sin nombre'}</strong>
                    {proveedor.codigo && <small>{proveedor.codigo}</small>}
                    <span>{totalContratos === 1 ? '1 contrato asociado' : `${totalContratos} contratos asociados`}</span>
                  </div>
                  {puedeEliminar && <button
                    className="button button-plain provider-delete-button"
                    type="button"
                    disabled={totalContratos > 0 || eliminandoId !== null}
                    title={totalContratos > 0 ? 'Elimina primero los contratos asociados.' : undefined}
                    onClick={() => onDelete(proveedor)}
                  >
                    {eliminando ? 'Eliminando…' : 'Eliminar'}
                  </button>}
                </li>
              )
            })}
          </ul>
        )}
      </section>
    </dialog>
  )
}
