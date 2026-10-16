import type { Contrato } from '../types'
import { formatoTarifa } from '../utils'

type ProviderTableProps = {
  contratos: Contrato[]
  visibles: Contrato[]
  cargando: boolean
  esAdministrador: boolean
  busqueda: string
  onBusquedaChange: (valor: string) => void
  onEditar: (contrato: Contrato) => void
  onEliminar: (contrato: Contrato) => void
}

function mostrarTarifa(valor: string) {
  const monto = Number(valor)
  return monto === 0 ? '—' : `$ ${formatoTarifa.format(monto)}`
}

export default function ProviderTable({
  contratos,
  visibles,
  cargando,
  esAdministrador,
  busqueda,
  onBusquedaChange,
  onEditar,
  onEliminar,
}: ProviderTableProps) {
  return (
    <section className="table-card" id="lista">
      <div className="section-heading table-heading">
        <div><h2>Contratos de proveedores</h2><p>{esAdministrador ? 'Consulta y administra los contratos registrados.' : 'Consulta los contratos registrados.'}</p></div>
        <label className="search-box"><span aria-hidden="true">⌕</span><input aria-label="Buscar proveedores" value={busqueda} onChange={(event) => onBusquedaChange(event.target.value)} placeholder="Buscar proveedor..." /></label>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>PROVEEDOR</th><th>CONTRATO</th><th>MENSUAL</th><th>TRIMESTRAL</th><th>SEMESTRAL</th><th>ANUAL</th><th>SERVICIOS</th><th>ESTADO</th><th>PDF</th><th>ACCIONES</th></tr></thead>
          <tbody>
            {cargando ? <tr><td className="empty-state" colSpan={10}>Cargando contratos…</td></tr> : visibles.length === 0 ? <tr><td className="empty-state" colSpan={10}>{contratos.length ? 'No hay resultados para esta búsqueda.' : 'Aún no hay contratos. Agrega el primero en el formulario.'}</td></tr> : visibles.map((item) => (
              <tr key={item.id}>
                <td><span className="provider-name">{item.proveedor.nombre}</span>{item.proveedor.codigo && <small className="provider-code">{item.proveedor.codigo}</small>}</td>
                <td>{item.contrato}</td>
                <td className="rate">{mostrarTarifa(item.tarifa_mensual)}</td>
                <td className="rate">{mostrarTarifa(item.tarifa_trimestral)}</td>
                <td className="rate">{mostrarTarifa(item.tarifa_semestral)}</td>
                <td className="rate">{mostrarTarifa(item.tarifa_anual)}</td>
                <td className="services-cell">{item.servicios}</td>
                <td><span className={`status status-${item.estado.toLocaleLowerCase('es')}`}>{item.estado}</span></td>
                <td>{item.tiene_pdf && item.pdf_url ? <span className="pdf-actions"><a href={item.pdf_url} target="_blank" rel="noopener noreferrer">Ver PDF</a></span> : <span className="no-pdf">Sin PDF</span>}</td>
                <td>{esAdministrador && <div className="row-actions"><button type="button" aria-label={`Editar contrato ${item.contrato} de ${item.proveedor.nombre}`} onClick={() => onEditar(item)}>Editar</button><button className="delete-action" type="button" aria-label={`Eliminar contrato ${item.contrato} de ${item.proveedor.nombre}`} onClick={() => onEliminar(item)}>Eliminar</button></div>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-footer">Mostrando {visibles.length} de {contratos.length} contratos</div>
    </section>
  )
}
