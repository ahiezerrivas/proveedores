import { useState, type FormEvent } from 'react'

type LoginPageProps = {
  onLogin: (username: string, password: string) => Promise<void>
  busy: boolean
  error: string
}

export default function LoginPage({ onLogin, busy, error }: LoginPageProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void onLogin(username, password)
  }

  return (
    <main className="login-screen">
      <section className="login-card">
        <span>Proveedores</span>
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
