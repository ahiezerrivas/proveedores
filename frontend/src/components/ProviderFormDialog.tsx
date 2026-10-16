import { useEffect, useRef, useState, type FormEvent } from 'react'
import type { Formulario, Estado, Proveedor, TarifaCampo } from '../types'
import { formatoTarifa, formatoTarifaEnEdicion } from '../utils'

type ProviderFormDialogProps = {
  open: boolean
  editando: boolean
  proveedores: Proveedor[]
  formulario: Formulario
  guardando: boolean
  archivoPdf: File | null
  error: string
  onChange: (campo: keyof Formulario, valor: string) => void
  onSubmit: (
    event: FormEvent<HTMLFormElement>,
    nuevoProveedor: { codigo: string; nombre: string },
    codigoProveedor: string,
  ) => void
  onClose: () => void
  onFileChange: (file: File | null) => void
  onError: (error: string) => void
}

const camposTarifa: [TarifaCampo, string][] = [
  ['tarifa_mensual', 'Tarifa mensual'],
  ['tarifa_trimestral', 'Tarifa trimestral'],
  ['tarifa_semestral', 'Tarifa semestral'],
  ['tarifa_anual', 'Tarifa anual'],
]

export default function ProviderFormDialog({
  open,
  editando,
  proveedores,
  formulario,
  guardando,
  archivoPdf,
  error,
  onChange,
  onSubmit,
  onClose,
  onFileChange,
  onError,
}: ProviderFormDialogProps) {
  const dialog = useRef<HTMLDialogElement>(null)
  const inputPdf = useRef<HTMLInputElement>(null)
  const inputTarifas = useRef<Record<TarifaCampo, HTMLInputElement | null>>({
    tarifa_mensual: null,
    tarifa_trimestral: null,
    tarifa_semestral: null,
    tarifa_anual: null,
  })
  const [tarifaEnfocada, setTarifaEnfocada] = useState<TarifaCampo | null>(null)
  const [nuevoProveedor, setNuevoProveedor] = useState({ codigo: '', nombre: '' })
  const [codigoProveedor, setCodigoProveedor] = useState('')

  useEffect(() => {
    const elemento = dialog.current
    if (!elemento) return
    if (open && !elemento.open) elemento.showModal()
    if (open) {
      setNuevoProveedor({ codigo: '', nombre: '' })
      setCodigoProveedor(
        proveedores.find((proveedor) => String(proveedor.id) === formulario.proveedor_id)?.codigo ?? '',
      )
    }
    if (!open) {
      if (elemento.open) elemento.close()
      if (inputPdf.current) inputPdf.current.value = ''
      setTarifaEnfocada(null)
      setNuevoProveedor({ codigo: '', nombre: '' })
      setCodigoProveedor('')
    }
  }, [open, formulario.proveedor_id, proveedores])

  function cambiarTarifa(campo: TarifaCampo, valor: string) {
    const input = inputTarifas.current[campo]
    const posicion = input?.selectionStart ?? valor.length
    const antesDelCursor = valor.slice(0, posicion)
    const digitosAntes = (antesDelCursor.match(/\d/g) ?? []).length
    const comaAntes = antesDelCursor.includes(',')
    const limpio = valor.replace(/\./g, '').replace(/[^\d,]/g, '')
    const partes = limpio.split(',')
    const entero = partes[0] || (partes.length > 1 ? '0' : '')
    const decimales = (partes.slice(1).join('') || '').slice(0, 2)
    const tieneComa = partes.length > 1
    const canonico = `${entero}${tieneComa ? `.${decimales}` : ''}`
    const enteroAgrupado = entero.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
    const visual = `${enteroAgrupado}${tieneComa ? `,${decimales}` : ''}`

    onChange(campo, canonico)
    if (input) {
      requestAnimationFrame(() => {
        let nuevaPosicion = 0
        let digitosContados = 0
        while (nuevaPosicion < visual.length && digitosContados < digitosAntes) {
          if (/\d/.test(visual[nuevaPosicion])) digitosContados += 1
          nuevaPosicion += 1
        }
        if (comaAntes && tieneComa) nuevaPosicion = Math.max(nuevaPosicion, visual.indexOf(',') + 1)
        input.setSelectionRange(nuevaPosicion, nuevaPosicion)
      })
    }
  }

  function cambiarArchivo(file: File | null, input: HTMLInputElement) {
    if (file && (file.type !== 'application/pdf' || !file.name.toLowerCase().endsWith('.pdf'))) {
      onError('Selecciona un archivo PDF válido.')
      input.value = ''
      onFileChange(null)
      return
    }
    if (file && file.size > 10 * 1024 * 1024) {
      onError('El PDF no puede superar los 10 MB.')
      input.value = ''
      onFileChange(null)
      return
    }
    onError('')
    onFileChange(file)
  }

  return (
    <dialog
      ref={dialog}
      className="provider-dialog"
      aria-labelledby="provider-dialog-title"
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
      onClick={(event) => {
        if (event.target === dialog.current) onClose()
      }}
    >
      <section className="form-card">
        <div className="section-heading">
          <div>
            <h2 id="provider-dialog-title">{editando ? 'Editar contrato' : 'Agregar contrato'}</h2>
            <p>{editando ? 'Actualiza los datos del contrato.' : 'Asocia el contrato a un proveedor existente o registra uno nuevo.'}</p>
          </div>
          <button className="dialog-close" type="button" aria-label="Cerrar formulario" onClick={onClose}>×</button>
        </div>
        {error && <div className="error-banner" role="alert">{error}</div>}
        <form onSubmit={(event) => onSubmit(event, nuevoProveedor, codigoProveedor)}>
          <div className="form-grid">
            <label>Proveedor<select value={formulario.proveedor_id} onChange={(event) => onChange('proveedor_id', event.target.value)}>
              <option value="">Seleccionar proveedor</option>
              {proveedores.map((proveedor) => (
                <option key={proveedor.id} value={String(proveedor.id)}>
                  {proveedor.codigo ? `${proveedor.codigo} — ` : ''}{proveedor.nombre}
                </option>
              ))}
              <option value="nuevo">＋ Registrar proveedor nuevo</option>
            </select></label>
            {formulario.proveedor_id !== '' && formulario.proveedor_id !== 'nuevo' && (
              <label>Código del proveedor<input maxLength={60} value={codigoProveedor} onChange={(event) => setCodigoProveedor(event.target.value)} placeholder="Código único (opcional)" /></label>
            )}
            {formulario.proveedor_id === 'nuevo' && <>
              <label>Código del proveedor<input maxLength={60} value={nuevoProveedor.codigo} onChange={(event) => setNuevoProveedor((actual) => ({ ...actual, codigo: event.target.value }))} placeholder="Código único (opcional)" /></label>
              <label>Nombre del proveedor<input maxLength={200} value={nuevoProveedor.nombre} onChange={(event) => setNuevoProveedor((actual) => ({ ...actual, nombre: event.target.value }))} placeholder="Nombre del proveedor" /></label>
            </>}
            <label>Contrato<input maxLength={120} value={formulario.contrato} onChange={(event) => onChange('contrato', event.target.value)} placeholder="N.º o nombre del contrato" /></label>
            {camposTarifa.map(([campo, etiqueta]) => (
              <label key={campo}>{etiqueta}<div className="currency-input"><span aria-hidden="true">$</span><input ref={(input) => { inputTarifas.current[campo] = input }} inputMode="decimal" type="text" value={tarifaEnfocada === campo || !formulario[campo] ? formatoTarifaEnEdicion(formulario[campo]) : formatoTarifa.format(Number(formulario[campo]))} onFocus={() => setTarifaEnfocada(campo)} onBlur={() => setTarifaEnfocada(null)} onChange={(event) => cambiarTarifa(campo, event.target.value)} placeholder="0,00" aria-label={`${etiqueta} en dólares`} /></div></label>
            ))}
            <label>Estado<select value={formulario.estado} onChange={(event) => onChange('estado', event.target.value as Estado)}><option>Activo</option><option>Pendiente</option><option>Inactivo</option></select></label>
            <label className="services-field">Servicios<textarea rows={2} value={formulario.servicios} onChange={(event) => onChange('servicios', event.target.value)} placeholder="Describe los servicios contratados" /></label>
            <label className="pdf-field">Adjuntar PDF <span className="field-hint">Opcional · máximo 10 MB</span><input ref={inputPdf} accept=".pdf,application/pdf" type="file" onChange={(event) => cambiarArchivo(event.target.files?.[0] ?? null, event.currentTarget)} />{archivoPdf && <span className="field-hint">{archivoPdf.name}</span>}</label>
          </div>
          <div className="form-actions">
            <button className="button button-primary" type="submit" disabled={guardando}>{guardando ? 'Guardando…' : editando ? 'Guardar cambios' : 'Guardar contrato'}</button>
            {editando && <button className="button button-plain" type="button" onClick={onClose}>Cancelar</button>}
          </div>
        </form>
      </section>
    </dialog>
  )
}
