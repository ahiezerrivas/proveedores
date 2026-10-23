import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router'
import AuditLogPanel from './components/AuditLogPanel'
import LoginPage from './components/LoginPage'
import ProviderFormDialog from './components/ProviderFormDialog'
import ProviderManagementDialog from './components/ProviderManagementDialog'
import ProviderSummary from './components/ProviderSummary'
import ProviderTable from './components/ProviderTable'
import type { Contrato, Formulario, Proveedor, RegistroAuditoria, Usuario } from './types'
import { API_ROOT, AUDITORIA_URL, CONTRATOS_URL, PROVEEDORES_URL, csrfToken, formularioVacio, puede, respuestaJson } from './utils'

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const seccion = location.pathname.replace(/\/+$/, '') === '/auditoria' ? 'auditoria' : 'proveedores'
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [sesionCargando, setSesionCargando] = useState(true)
  const [loginBusy, setLoginBusy] = useState(false)
  const [loginError, setLoginError] = useState('')
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [contratos, setContratos] = useState<Contrato[]>([])
  const [formulario, setFormulario] = useState<Formulario>(formularioVacio)
  const [archivoPdf, setArchivoPdf] = useState<File | null>(null)
  const [editando, setEditando] = useState<number | null>(null)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [modalProveedoresAbierto, setModalProveedoresAbierto] = useState(false)
  const [eliminandoProveedorId, setEliminandoProveedorId] = useState<number | null>(null)
  const [errorEliminarProveedor, setErrorEliminarProveedor] = useState('')
  const [sidebarVisible, setSidebarVisible] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState('')
  const [formError, setFormError] = useState('')
  const [registrosAuditoria, setRegistrosAuditoria] = useState<RegistroAuditoria[]>([])
  const [totalAuditoria, setTotalAuditoria] = useState(0)
  const [paginaAuditoria, setPaginaAuditoria] = useState(1)
  const [cargandoAuditoria, setCargandoAuditoria] = useState(false)
  const [errorAuditoria, setErrorAuditoria] = useState('')
  const [filtroUsuarioAuditoria, setFiltroUsuarioAuditoria] = useState('')
  const [filtroAccionAuditoria, setFiltroAccionAuditoria] = useState('')
  const [usuariosAuditoria, setUsuariosAuditoria] = useState<string[]>([])

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
      navigate('/')
      setProveedores([])
      setContratos([])
      setRegistrosAuditoria([])
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
      const [respuestaProveedores, respuestaContratos] = await Promise.all([
        fetch(PROVEEDORES_URL, { credentials: 'include' }),
        fetch(CONTRATOS_URL, { credentials: 'include' }),
      ])
      const [proveedoresCargados, contratosCargados] = await Promise.all([
        respuestaJson<Proveedor[]>(respuestaProveedores),
        respuestaJson<Contrato[]>(respuestaContratos),
      ])
      setProveedores(proveedoresCargados)
      setContratos(contratosCargados)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron cargar los proveedores.')
    } finally {
      setCargando(false)
    }
  }, [usuario])

  useEffect(() => {
    if (usuario) void cargarProveedores()
  }, [cargarProveedores])

  const cargarAuditoria = useCallback(async () => {
    if (!puede(usuario, 'view_registroauditoria') || seccion !== 'auditoria') return
    setCargandoAuditoria(true)
    setErrorAuditoria('')
    try {
      const params = new URLSearchParams({ page: String(paginaAuditoria) })
      if (filtroUsuarioAuditoria) params.set('usuario', filtroUsuarioAuditoria)
      if (filtroAccionAuditoria) params.set('accion', filtroAccionAuditoria)
      const response = await fetch(`${AUDITORIA_URL}?${params}`, { credentials: 'include' })
      const data = await respuestaJson<{ count: number; results: RegistroAuditoria[] }>(response)
      setRegistrosAuditoria(data.results)
      setTotalAuditoria(data.count)
    } catch (err) {
      setErrorAuditoria(err instanceof Error ? err.message : 'No se pudo cargar la auditoría.')
    } finally {
      setCargandoAuditoria(false)
    }
  }, [filtroAccionAuditoria, filtroUsuarioAuditoria, paginaAuditoria, seccion, usuario])

  useEffect(() => {
    void cargarAuditoria()
  }, [cargarAuditoria])

  useEffect(() => {
    if (!puede(usuario, 'view_registroauditoria') || seccion !== 'auditoria') return
    fetch(`${AUDITORIA_URL}usuarios/`, { credentials: 'include' })
      .then((response) => respuestaJson<string[]>(response))
      .then(setUsuariosAuditoria)
      .catch(() => setUsuariosAuditoria([]))
  }, [seccion, usuario])

  const visibles = contratos.filter((item) =>
    `${item.proveedor.nombre} ${item.proveedor.codigo} ${item.contrato} ${item.servicios}`
      .toLocaleLowerCase('es')
      .includes(busqueda.toLocaleLowerCase('es')),
  )
  const contratosPorProveedor = new Map<number, number>()
  contratos.forEach(({ proveedor }) => {
    contratosPorProveedor.set(proveedor.id, (contratosPorProveedor.get(proveedor.id) ?? 0) + 1)
  })

  function cambiarCampo(campo: keyof Formulario, valor: string) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
  }

  function editar(item: Contrato) {
    setFormError('')
    setEditando(item.id)
    setModalAbierto(true)
    setArchivoPdf(null)
    setFormulario({
      proveedor_id: String(item.proveedor.id),
      contrato: item.contrato,
      tarifa_mensual: item.tarifa_mensual,
      tarifa_trimestral: item.tarifa_trimestral,
      tarifa_semestral: item.tarifa_semestral,
      tarifa_anual: item.tarifa_anual,
      servicios: item.servicios,
      estado: item.estado,
    })
  }

  function cancelarEdicion() {
    setModalAbierto(false)
    setEditando(null)
    setFormulario(formularioVacio)
    setArchivoPdf(null)
    setFormError('')
  }

  async function guardar(
    event: FormEvent<HTMLFormElement>,
    nuevoProveedor: { codigo: string; nombre: string },
    codigoProveedor: string,
  ) {
    event.preventDefault()
    setGuardando(true)
    setFormError('')
    try {
      const datos = new FormData()
      Object.entries(formulario).forEach(([campo, valor]) => {
        if (campo !== 'proveedor_id') datos.append(campo, valor)
      })
      if (formulario.proveedor_id === 'nuevo') {
        datos.append('nuevo_proveedor', JSON.stringify(nuevoProveedor))
      } else if (formulario.proveedor_id) {
        datos.append('proveedor_id', formulario.proveedor_id)
        datos.append('proveedor_codigo', codigoProveedor)
      }
      ;(['tarifa_mensual', 'tarifa_trimestral', 'tarifa_semestral', 'tarifa_anual'] as const).forEach((campo) => {
        datos.set(campo, String(Number(formulario[campo])))
      })
      if (archivoPdf) datos.append('archivo_pdf', archivoPdf)
      const response = await fetch(editando ? `${CONTRATOS_URL}${editando}/` : CONTRATOS_URL, {
        method: editando ? 'PUT' : 'POST',
        credentials: 'include',
        headers: { 'X-CSRFToken': csrfToken() },
        body: datos,
      })
      await respuestaJson<Contrato>(response)
      cancelarEdicion()
      await cargarProveedores()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'No se pudo guardar el contrato.')
    } finally {
      setGuardando(false)
    }
  }

  async function eliminar(item: Contrato) {
    if (!window.confirm(`¿Eliminar el contrato ${item.contrato} de ${item.proveedor.nombre}? Esta acción no se puede deshacer.`)) return
    setError('')
    try {
      const response = await fetch(`${CONTRATOS_URL}${item.id}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'X-CSRFToken': csrfToken() },
      })
      if (!response.ok) throw new Error(`No se pudo eliminar el contrato (error ${response.status}).`)
      setContratos((actuales) => actuales.filter((contrato) => contrato.id !== item.id))
      if (editando === item.id) cancelarEdicion()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo eliminar el contrato.')
    }
  }

  async function eliminarProveedor(proveedor: Proveedor) {
    if (!window.confirm(`¿Eliminar al proveedor ${proveedor.nombre}? Esta acción no se puede deshacer.`)) return
    setEliminandoProveedorId(proveedor.id)
    setErrorEliminarProveedor('')
    try {
      const response = await fetch(`${PROVEEDORES_URL}${proveedor.id}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'X-CSRFToken': csrfToken() },
      })
      if (!response.ok) await respuestaJson<unknown>(response)
      setProveedores((actuales) => actuales.filter((item) => item.id !== proveedor.id))
    } catch (err) {
      setErrorEliminarProveedor(err instanceof Error ? err.message : 'No se pudo eliminar el proveedor.')
    } finally {
      setEliminandoProveedorId(null)
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
        <button
          className={`nav-item${seccion === 'proveedores' ? ' active' : ''}`}
          type="button"
          aria-current={seccion === 'proveedores' ? 'page' : undefined}
          onClick={() => navigate('/')}
        >
          <span aria-hidden="true">▦</span> Proveedores
        </button>
        {puede(usuario, 'view_registroauditoria') && (
          <button
            className={`nav-item${seccion === 'auditoria' ? ' active' : ''}`}
            type="button"
            aria-current={seccion === 'auditoria' ? 'page' : undefined}
            onClick={() => {
              setPaginaAuditoria(1)
              navigate('/auditoria')
            }}
          >
            <span aria-hidden="true">◷</span> Auditoría
          </button>
        )}
        <div className="sidebar-bottom">
          <span className="avatar">{usuario.username.slice(0, 2).toUpperCase()}</span>
          <span><strong>{usuario.first_name || usuario.username}</strong><small>{usuario.roles.join(', ') || (usuario.is_superuser ? 'Superusuario' : 'Sin rol')}</small></span>
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
            <span>Panel de gestión <span className="crumb">/ {seccion === 'auditoria' ? 'Auditoría' : 'Proveedores'}</span></span>
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
              <h1>{seccion === 'auditoria' ? 'Auditoría de actividad' : 'Proveedores y contratos'}</h1>
            </div>
            {seccion === 'proveedores' && puede(usuario, 'add_contrato') && <button className="button button-secondary" type="button" onClick={() => {
              cancelarEdicion()
              setFormError('')
              setModalAbierto(true)
            }}>＋ Nuevo contrato</button>}
          </div>

          <Routes>
            <Route path="/auditoria" element={puede(usuario, 'view_registroauditoria') ? (
            <AuditLogPanel
              registros={registrosAuditoria}
              total={totalAuditoria}
              pagina={paginaAuditoria}
              paginas={Math.max(1, Math.ceil(totalAuditoria / 50))}
              cargando={cargandoAuditoria}
              error={errorAuditoria}
              onRetry={() => void cargarAuditoria()}
              onCambiarPagina={setPaginaAuditoria}
              usuarios={usuariosAuditoria}
              filtroUsuario={filtroUsuarioAuditoria}
              filtroAccion={filtroAccionAuditoria}
              onCambiarFiltroUsuario={(valor) => {
                setFiltroUsuarioAuditoria(valor)
                setPaginaAuditoria(1)
              }}
              onCambiarFiltroAccion={(valor) => {
                setFiltroAccionAuditoria(valor)
                setPaginaAuditoria(1)
              }}
            />
            ) : <Navigate to="/" replace />} />
            <Route path="/" element={<>
              <ProviderSummary
                proveedores={proveedores}
                contratos={contratos}
                onManageProviders={() => {
                  setErrorEliminarProveedor('')
                  setModalProveedoresAbierto(true)
                }}
              />

              <ProviderManagementDialog
                open={modalProveedoresAbierto}
                proveedores={proveedores}
                contratosPorProveedor={contratosPorProveedor}
                eliminandoId={eliminandoProveedorId}
                puedeEliminar={puede(usuario, 'delete_proveedor')}
                error={errorEliminarProveedor}
                onClose={() => setModalProveedoresAbierto(false)}
                onDelete={(proveedor) => void eliminarProveedor(proveedor)}
              />

              {error && (
                <div className="error-banner" role="alert">
                  <span>{error}</span>
                  <button className="text-button" type="button" onClick={() => void cargarProveedores()}>Reintentar</button>
                </div>
              )}

              {(puede(usuario, 'add_contrato') || puede(usuario, 'change_contrato')) && <ProviderFormDialog
                open={modalAbierto}
                puedeCrearProveedor={puede(usuario, 'add_proveedor')}
                puedeEditarProveedor={puede(usuario, 'change_proveedor')}
                editando={editando !== null}
                proveedores={proveedores}
                formulario={formulario}
                guardando={guardando}
                archivoPdf={archivoPdf}
                error={formError}
                onChange={cambiarCampo}
                onSubmit={guardar}
                onClose={cancelarEdicion}
                onFileChange={setArchivoPdf}
                onError={setFormError}
              />}

              <ProviderTable
                contratos={contratos}
                visibles={visibles}
                cargando={cargando}
                puedeEditar={puede(usuario, 'change_contrato')}
                puedeEliminar={puede(usuario, 'delete_contrato')}
                busqueda={busqueda}
                onBusquedaChange={setBusqueda}
                onEditar={editar}
                onEliminar={(proveedor) => void eliminar(proveedor)}
              />
            </>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <footer className="page-footer">Gestión de proveedores <span>•</span> Coordinación de Logistica</footer>
          <footer className="author-footer">Elaborado por la Coordinación de Logistica</footer>
        </div>
      </section>
    </main>
  )
}

export default App
