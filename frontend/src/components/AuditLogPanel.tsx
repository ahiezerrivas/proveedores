import type { RegistroAuditoria } from '../types'

type AuditLogPanelProps = {
  registros: RegistroAuditoria[]
  total: number
  pagina: number
  paginas: number
  cargando: boolean
  error: string
  onRetry: () => void
  onCambiarPagina: (pagina: number) => void
}

function AuditLogPanel({
  registros,
  total,
  pagina,
  paginas,
  cargando,
  error,
  onRetry,
  onCambiarPagina,
}: AuditLogPanelProps) {
  return (
    <section className="table-card audit-card" aria-label="Registro de auditoría">
      <div className="table-heading audit-heading">
        <div>
          <h2>Actividad de usuarios</h2>
          <p>Acciones realizadas en la aplicación. Se muestran primero las más recientes.</p>
        </div>
        <span className="audit-total">{total} registros</span>
      </div>

      {error && (
        <div className="error-banner audit-error" role="alert">
          <span>{error}</span>
          <button className="text-button" type="button" onClick={onRetry}>Reintentar</button>
        </div>
      )}

      <div className="table-wrap">
        <table className="audit-table">
          <thead>
            <tr>
              <th>Fecha y hora</th>
              <th>Usuario</th>
              <th>Acción</th>
              <th>Descripción</th>
              <th>Resultado</th>
              <th>Dirección IP</th>
            </tr>
          </thead>
          <tbody>
            {cargando ? (
              <tr><td className="empty-state" colSpan={6}>Cargando auditoría…</td></tr>
            ) : registros.length === 0 ? (
              <tr><td className="empty-state" colSpan={6}>No hay actividad registrada.</td></tr>
            ) : registros.map((registro) => (
              <tr key={registro.id}>
                <td>{new Intl.DateTimeFormat('es-CO', {
                  dateStyle: 'short',
                  timeStyle: 'medium',
                }).format(new Date(registro.fecha))}</td>
                <td>{registro.nombre_usuario}</td>
                <td>{registro.accion_display}</td>
                <td>
                  <span className="audit-description">{registro.descripcion}</span>
                  <code className="audit-technical">{registro.metodo} {registro.ruta}</code>
                </td>
                <td>
                  <span
                    className={`status ${registro.codigo_estado < 400 ? 'status-activo' : 'status-inactivo'}`}
                    title={`Código HTTP ${registro.codigo_estado}`}
                  >
                    {registro.codigo_estado < 400 ? 'Exitoso' : 'Rechazado'} ({registro.codigo_estado})
                  </span>
                </td>
                <td>{registro.direccion_ip ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="audit-pagination">
        <span>Página {pagina} de {paginas}</span>
        <div>
          <button
            className="button button-secondary"
            type="button"
            disabled={cargando || pagina <= 1}
            onClick={() => onCambiarPagina(pagina - 1)}
          >
            Anterior
          </button>
          <button
            className="button button-secondary"
            type="button"
            disabled={cargando || pagina >= paginas}
            onClick={() => onCambiarPagina(pagina + 1)}
          >
            Siguiente
          </button>
        </div>
      </div>
    </section>
  )
}

export default AuditLogPanel
