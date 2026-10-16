import type { Contrato, Proveedor } from '../types'
import { formatoTarifa } from '../utils'

type ProviderSummaryProps = {
  proveedores: Proveedor[]
  contratos: Contrato[]
  onManageProviders: () => void
}

const camposTarifa = [
  ['Mensual', 'tarifa_mensual'],
  ['Trimestral', 'tarifa_trimestral'],
  ['Semestral', 'tarifa_semestral'],
  ['Anual', 'tarifa_anual'],
] as const

export default function ProviderSummary({ proveedores, contratos, onManageProviders }: ProviderSummaryProps) {
  const activos = contratos.filter((item) => item.estado === 'Activo')
  const resumenTarifas = camposTarifa.map(([periodo, campo]) => ({
    periodo,
    total: activos.reduce((suma, item) => suma + Number(item[campo]), 0),
  }))

  return (
    <div className="summary-grid">
      <button className="summary-card provider-summary-trigger" type="button" onClick={onManageProviders} aria-label="Ver proveedores">
          <span className="summary-icon purple">▦</span>
          <div><p>Total proveedores</p><strong>{proveedores.length}</strong></div>
          <span className="summary-note">Ver proveedores</span>
      </button>
      <article className="summary-card">
        <span className="summary-icon green">✓</span>
        <div><p>Contratos activos</p><strong>{activos.length}</strong></div>
        <span className="summary-note">de {contratos.length} contratos</span>
      </article>
      <article className="summary-card tariff-summary">
        <div className="tariff-summary-heading">
          <span className="summary-icon orange">$</span>
          <div><p>Tarifas activas</p></div>
        </div>
        <div className="tariff-summary-list">
          {resumenTarifas.map(({ periodo, total }) => (
            <div className="tariff-summary-item" key={periodo}>
              <span>{periodo}</span>
              <strong>$ {formatoTarifa.format(total)}</strong>
            </div>
          ))}
        </div>
      </article>
    </div>
  )
}
