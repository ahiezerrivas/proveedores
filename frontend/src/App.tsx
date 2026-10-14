import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'

type Estado = 'Activo' | 'Pendiente' | 'Inactivo'

type Proveedor = {
  id: number
  proveedor: string
  contrato: string
  tarifa_mensual: string
  servicios: string
  estado: Estado
  tiene_pdf: boolean
  pdf_url: string | null
}

type Formulario = Omit<Proveedor, 'id' | 'tiene_pdf' | 'pdf_url'>
type Usuario = {
  id: number
  username: string
  first_name: string
  last_name: string
  is_admin: boolean
  roles: string[]
}

const API_ROOT = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace(/\/+$/, '')
const API_URL = `${API_ROOT}/proveedores/`
const formatoTarifa = new Intl.NumberFormat('es-CO', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})
function formatoTarifaEnEdicion(valor: string) {
  const [entero = '', decimales] = valor.split('.')
  const enteroAgrupado = entero.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return decimales === undefined ? enteroAgrupado : `${enteroAgrupado},${decimales}`
}

const formularioVacio: Formulario = {
  proveedor: '',
  contrato: '',
  tarifa_mensual: '',
  servicios: '',
  estado: 'Activo',
}

async function respuestaJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail =
      body && typeof body === 'object'
        ? Object.values(body).flat().join(' ')
        : `Error ${response.status}`
    throw new Error(detail || `Error ${response.status}`)
  }
  return response.json() as Promise<T>
}

function csrfToken() {
  const value = document.cookie
    .split('; ')
    .find((cookie) => cookie.startsWith('csrftoken='))
    ?.split('=')
    .slice(1)
    .join('=')
  return value ? decodeURIComponent(value) : ''
}

type LoginPageProps = {
  onLogin: (username: string, password: string) => Promise<void>
  busy: boolean
  error: string
}

function LoginPage({ onLogin, busy, error }: LoginPageProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void onLogin(username, password)
  }

  return (
    <main className="login-screen">
      <section className="login-card">
        <a className="brand login-brand" href="#" aria-label="Gestión de proveedores">
          <span className="brand-mark">P</span>
          <span>provee<span className="brand-light">dores</span></span>
        </a>
        <p className="eyebrow">ACCESO SEGURO</p>
        <h1>Inicia sesión</h1>
        <p className="subtitle">Ingresa con la cuenta que te asignó el administrador.</p>
        {error && <div className="error-banner login-error" role="alert">{error}</div>}
        <form className="login-form" onSubmit={submit}>
          <label>Usuario<input autoComplete="username" autoFocus required value={username} onChange={(event) => setUsername(event.target.value)} /></label>
          <label>Contraseña<input autoComplete="current-password" required type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          <button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Ingresando…' : 'Iniciar sesión'}</button>
        </form>
      </section>
    </main>
  )
}

function App() {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [sesionCargando, setSesionCargando] = useState(true)
  const [loginBusy, setLoginBusy] = useState(false)
  const [loginError, setLoginError] = useState('')
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [formulario, setFormulario] = useState<Formulario>(formularioVacio)
  const [tarifaEnfocada, setTarifaEnfocada] = useState(false)
  const [archivoPdf, setArchivoPdf] = useState<File | null>(null)
  const inputPdf = useRef<HTMLInputElement>(null)
  const inputTarifa = useRef<HTMLInputElement>(null)
  const [editando, setEditando] = useState<number | null>(null)
  const [modalAbierto, setModalAbierto] = useState(false)
  const dialogoProveedor = useRef<HTMLDialogElement>(null)
  const [sidebarVisible, setSidebarVisible] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const dialogo = dialogoProveedor.current
    if (!dialogo) return
    if (modalAbierto && !dialogo.open) dialogo.showModal()
    if (!modalAbierto && dialogo.open) dialogo.close()
  }, [modalAbierto])

  useEffect(() => {
    async function iniciarSesion() {
      try {
        const csrfResponse = await fetch(`${API_ROOT}/auth/csrf/`, { credentials: 'include' })
        await respuestaJson<{ csrf_token: string }>(csrfResponse)
        const response = await fetch(`${API_ROOT}/auth/session/`, { credentials: 'include' })
        const data = await respuestaJson<{ authenticated: boolean; user?: Usuario }>(response)
        setUsuario(data.authenticated ? data.user ?? null : null)
      } catch (err) {
        setLoginError(err instanceof Error ? err.message : 'No se pudo conectar con el servidor.')
      } finally {
        setSesionCargando(false)
      }
    }
    void iniciarSesion()
  }, [])

  async function iniciarSesionConCredenciales(username: string, password: string) {
    setLoginBusy(true)
    setLoginError('')
    try {
      const csrfResponse = await fetch(`${API_ROOT}/auth/csrf/`, { credentials: 'include' })
      await respuestaJson<{ csrf_token: string }>(csrfResponse)
      const response = await fetch(`${API_ROOT}/auth/login/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
        body: JSON.stringify({ username, password }),
      })
      const data = await respuestaJson<{ user: Usuario }>(response)
      setUsuario(data.user)
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : 'No se pudo iniciar sesión.')
    } finally {
      setLoginBusy(false)
    }
  }

  async function cerrarSesion() {
    try {
      const response = await fetch(`${API_ROOT}/auth/logout/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRFToken': csrfToken() },
      })
      await respuestaJson<{ authenticated: boolean }>(response)
      setUsuario(null)
      setProveedores([])
      cancelarEdicion()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cerrar la sesión.')
    }
  }

  const cargarProveedores = useCallback(async () => {
    if (!usuario) return
    setCargando(true)
    setError('')
    try {
      setProveedores(await respuestaJson<Proveedor[]>(await fetch(API_URL, { credentials: 'include' })))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron cargar los proveedores.')
    } finally {
      setCargando(false)
    }
  }, [usuario])

  useEffect(() => {
    if (usuario) void cargarProveedores()
  }, [cargarProveedores])

  const visibles = proveedores.filter((item) =>
    `${item.proveedor} ${item.contrato} ${item.servicios}`
      .toLocaleLowerCase('es')
      .includes(busqueda.toLocaleLowerCase('es')),
  )
  const activos = proveedores.filter((item) => item.estado === 'Activo').length
  const gastoMensual = proveedores
    .filter((item) => item.estado === 'Activo')
    .reduce((suma, item) => suma + Number(item.tarifa_mensual), 0)

  function cambiarCampo(campo: keyof Formulario, valor: string) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
  }

  function cambiarTarifa(valor: string) {
    const input = inputTarifa.current
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

    cambiarCampo('tarifa_mensual', canonico)
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

  function editar(item: Proveedor) {
    setEditando(item.id)
    setModalAbierto(true)
    setArchivoPdf(null)
    if (inputPdf.current) inputPdf.current.value = ''
    setFormulario({
      proveedor: item.proveedor,
      contrato: item.contrato,
      tarifa_mensual: item.tarifa_mensual,
      servicios: item.servicios,
      estado: item.estado,
    })
  }

  function cancelarEdicion() {
    setModalAbierto(false)
    setEditando(null)
    setFormulario(formularioVacio)
    setArchivoPdf(null)
    if (inputPdf.current) inputPdf.current.value = ''
  }

  async function guardar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setGuardando(true)
    setError('')
    try {
      const datos = new FormData()
      Object.entries(formulario).forEach(([campo, valor]) => datos.append(campo, valor))
      datos.set('tarifa_mensual', String(Number(formulario.tarifa_mensual)))
      if (archivoPdf) datos.append('archivo_pdf', archivoPdf)
      const response = await fetch(editando ? `${API_URL}${editando}/` : API_URL, {
        method: editando ? 'PUT' : 'POST',
        credentials: 'include',
        headers: { 'X-CSRFToken': csrfToken() },
        body: datos,
      })
      await respuestaJson<Proveedor>(response)
      cancelarEdicion()
      await cargarProveedores()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el proveedor.')
    } finally {
      setGuardando(false)
    }
  }

  async function eliminar(item: Proveedor) {
    if (!window.confirm(`¿Eliminar a ${item.proveedor}? Esta acción no se puede deshacer.`)) return
    setError('')
    try {
      const response = await fetch(`${API_URL}${item.id}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'X-CSRFToken': csrfToken() },
      })
      if (!response.ok) throw new Error(`No se pudo eliminar el proveedor (error ${response.status}).`)
      setProveedores((actuales) => actuales.filter((proveedor) => proveedor.id !== item.id))
      if (editando === item.id) cancelarEdicion()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo eliminar el proveedor.')
    }
  }

  if (sesionCargando) {
    return <main className="login-screen"><p className="subtitle">Comprobando sesión…</p></main>
  }

  if (!usuario) {
    return <LoginPage onLogin={iniciarSesionConCredenciales} busy={loginBusy} error={loginError} />
  }

  return (
    <main className={`app-shell${sidebarVisible ? ' sidebar-visible' : ' sidebar-hidden'}`}>
      <aside className="sidebar" aria-hidden={!sidebarVisible}>
        <a className="brand" href="#" aria-label="Inicio">
          <span className="brand-mark">P</span>
          <span>provee<span className="brand-light">dores</span></span>
        </a>
        <p className="nav-label">GESTIÓN</p>
        <a className="nav-item active" href="#lista"><span aria-hidden="true">▦</span> Proveedores</a>
        <div className="sidebar-bottom">
          <span className="avatar">{usuario.username.slice(0, 2).toUpperCase()}</span>
          <span><strong>{usuario.first_name || usuario.username}</strong><small>{usuario.is_admin ? 'Administrador' : 'Consulta'}</small></span>
        </div>
      </aside>

      <section className="main-panel">
        <header className="topbar">
          <div className="topbar-heading">
            <button
              className="sidebar-toggle"
              type="button"
              aria-label={sidebarVisible ? 'Ocultar menú de navegación' : 'Mostrar menú de navegación'}
              aria-expanded={sidebarVisible}
              onClick={() => setSidebarVisible((visible) => !visible)}
            >
              <span aria-hidden="true">{sidebarVisible ? '×' : '☰'}</span>
            </button>
            <span>Panel de gestión <span className="crumb">/ Proveedores</span></span>
          </div>
          <div className="user-menu">
            <span className="today">{new Intl.DateTimeFormat('es', { dateStyle: 'long' }).format(new Date())}</span>
            <span className="user-name">{usuario.first_name || usuario.username}</span>
            <button className="text-button" type="button" onClick={() => void cerrarSesion()}>Cerrar sesión</button>
          </div>
        </header>

        <div className="content">
          <div className="page-heading">
            <div>
              <p className="eyebrow">Gerencia de Tecnología</p>
              <h1>Proveedores</h1>
            </div>
            {usuario.is_admin && <button className="button button-secondary" type="button" onClick={() => {
              cancelarEdicion()
              setModalAbierto(true)
            }}>＋ Nuevo proveedor</button>}
          </div>

          <div className="summary-grid">
            <article className="summary-card">
              <span className="summary-icon purple">▦</span>
              <div><p>Total proveedores</p><strong>{proveedores.length}</strong></div>
              <span className="summary-note">registrados</span>
            </article>
            <article className="summary-card">
              <span className="summary-icon green">✓</span>
              <div><p>Contratos activos</p><strong>{activos}</strong></div>
              <span className="summary-note">de {proveedores.length} proveedores</span>
            </article>
            <article className="summary-card">
              <span className="summary-icon orange">$</span>
              <div><p>Tarifa mensual activa</p><strong>$ {formatoTarifa.format(gastoMensual)}</strong></div>
              <span className="summary-note">total mensual</span>
            </article>
          </div>

          {error && (
            <div className="error-banner" role="alert">
              <span>{error}</span>
              <button className="text-button" type="button" onClick={() => void cargarProveedores()}>Reintentar</button>
            </div>
          )}

          {usuario.is_admin && <dialog
            ref={dialogoProveedor}
            className="provider-dialog"
            aria-labelledby="provider-dialog-title"
            onCancel={(event) => {
              event.preventDefault()
              cancelarEdicion()
            }}
            onClick={(event) => {
              if (event.target === dialogoProveedor.current) cancelarEdicion()
            }}
          >
            <section className="form-card">
            <div className="section-heading">
              <div>
                <h2 id="provider-dialog-title">{editando ? 'Editar proveedor' : 'Agregar proveedor'}</h2>
                <p>{editando ? 'Actualiza los datos del contrato.' : 'Completa los datos para registrar un nuevo proveedor.'}</p>
              </div>
              <button className="dialog-close" type="button" aria-label="Cerrar formulario" onClick={cancelarEdicion}>×</button>
            </div>
            <form onSubmit={guardar}>
              <div className="form-grid">
                <label>Proveedor<input required maxLength={200} value={formulario.proveedor} onChange={(event) => cambiarCampo('proveedor', event.target.value)} placeholder="Nombre del proveedor" /></label>
                <label>Contrato<input required maxLength={120} value={formulario.contrato} onChange={(event) => cambiarCampo('contrato', event.target.value)} placeholder="N.º o nombre del contrato" /></label>
                <label>Tarifa mensual<div className="currency-input"><span aria-hidden="true">$</span><input ref={inputTarifa} required inputMode="decimal" type="text" value={tarifaEnfocada || !formulario.tarifa_mensual ? formatoTarifaEnEdicion(formulario.tarifa_mensual) : formatoTarifa.format(Number(formulario.tarifa_mensual))} onFocus={() => setTarifaEnfocada(true)} onBlur={() => setTarifaEnfocada(false)} onChange={(event) => cambiarTarifa(event.target.value)} placeholder="0,00" aria-label="Tarifa mensual en dólares" /></div></label>
                <label>Estado<select value={formulario.estado} onChange={(event) => cambiarCampo('estado', event.target.value as Estado)}><option>Activo</option><option>Pendiente</option><option>Inactivo</option></select></label>
                <label className="services-field">Servicios<textarea required rows={2} value={formulario.servicios} onChange={(event) => cambiarCampo('servicios', event.target.value)} placeholder="Describe los servicios contratados" /></label>
                <label className="pdf-field">Adjuntar PDF <span className="field-hint">Opcional · máximo 10 MB</span><input ref={inputPdf} accept=".pdf,application/pdf" type="file" onChange={(event) => {
                  const file = event.target.files?.[0] ?? null
                  if (file && (file.type !== 'application/pdf' || !file.name.toLowerCase().endsWith('.pdf'))) {
                    setError('Selecciona un archivo PDF válido.')
                    event.target.value = ''
                    setArchivoPdf(null)
                    return
                  }
                  if (file && file.size > 10 * 1024 * 1024) {
                    setError('El PDF no puede superar los 10 MB.')
                    event.target.value = ''
                    setArchivoPdf(null)
                    return
                  }
                  setError('')
                  setArchivoPdf(file)
                }} />{archivoPdf && <span className="field-hint">{archivoPdf.name}</span>}</label>
              </div>
              <div className="form-actions">
                <button className="button button-primary" type="submit" disabled={guardando}>{guardando ? 'Guardando…' : editando ? 'Guardar cambios' : 'Guardar proveedor'}</button>
                {editando !== null && <button className="button button-plain" type="button" onClick={cancelarEdicion}>Cancelar</button>}
              </div>
            </form>
            </section>
          </dialog>}

          <section className="table-card" id="lista">
            <div className="section-heading table-heading">
              <div><h2>Directorio de proveedores</h2><p>{usuario.is_admin ? 'Consulta y administra los proveedores registrados.' : 'Consulta los proveedores registrados.'}</p></div>
              <label className="search-box"><span aria-hidden="true">⌕</span><input aria-label="Buscar proveedores" value={busqueda} onChange={(event) => setBusqueda(event.target.value)} placeholder="Buscar proveedor..." /></label>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>PROVEEDOR</th><th>CONTRATO</th><th>TARIFA MENSUAL</th><th>SERVICIOS</th><th>ESTADO</th><th>PDF</th><th>ACCIONES</th></tr></thead>
                <tbody>
                  {cargando ? <tr><td className="empty-state" colSpan={7}>Cargando proveedores…</td></tr> : visibles.length === 0 ? <tr><td className="empty-state" colSpan={7}>{proveedores.length ? 'No hay resultados para esta búsqueda.' : 'Aún no hay proveedores. Agrega el primero en el formulario.'}</td></tr> : visibles.map((item) => (
                    <tr key={item.id}>
                      <td><span className="provider-name">{item.proveedor}</span></td>
                      <td>{item.contrato}</td>
                      <td className="rate">$ {formatoTarifa.format(Number(item.tarifa_mensual))}</td>
                      <td className="services-cell">{item.servicios}</td>
                      <td><span className={`status status-${item.estado.toLocaleLowerCase('es')}`}>{item.estado}</span></td>
                      <td>{item.tiene_pdf && item.pdf_url ? <span className="pdf-actions"><a href={item.pdf_url} target="_blank" rel="noopener noreferrer">Ver PDF</a></span> : <span className="no-pdf">Sin PDF</span>}</td>
                      <td>{usuario.is_admin && <div className="row-actions"><button type="button" aria-label={`Editar ${item.proveedor}`} onClick={() => editar(item)}>Editar</button><button className="delete-action" type="button" aria-label={`Eliminar ${item.proveedor}`} onClick={() => void eliminar(item)}>Eliminar</button></div>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="table-footer">Mostrando {visibles.length} de {proveedores.length} proveedores</div>
          </section>
          <footer className="page-footer">Gestión de proveedores <span>•</span> Coordinación de Logistica</footer>
          <footer className="author-footer">Elaborado por la Coordinación de Logistica</footer>
        </div>
      </section>
    </main>
  )
}

export default App
