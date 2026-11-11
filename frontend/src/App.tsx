import { useState, type FormEvent } from 'react'
import { useAuth } from './auth/AuthContext'
import { ApiError, getMyProfile, type Profile } from './lib/api'
import './App.css'

// Temporary auth harness for Milestone 0. Member 2 owns the real screens and routing.
function App() {
  const { user, loading, signIn, signUp, signOut } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [busy, setBusy] = useState(false)

  async function run(action: () => Promise<void>) {
    setBusy(true)
    setMessage(null)
    try {
      await action()
    } finally {
      setBusy(false)
    }
  }

  function onSignIn(e: FormEvent) {
    e.preventDefault()
    run(async () => {
      const { error } = await signIn(email, password)
      setMessage(error ?? null)
    })
  }

  function onSignUp() {
    run(async () => {
      const { error, needsEmailConfirmation } = await signUp(email, password)
      if (error) setMessage(error)
      else if (needsEmailConfirmation) setMessage('Check your email to confirm your account.')
    })
  }

  function onSignOut() {
    run(async () => {
      const { error } = await signOut()
      setProfile(null)
      setMessage(error ?? 'Signed out.')
    })
  }

  function onLoadProfile() {
    run(async () => {
      try {
        setProfile(await getMyProfile())
      } catch (err) {
        setProfile(null)
        setMessage(err instanceof ApiError ? `${err.code}: ${err.message}` : 'Could not reach the API.')
      }
    })
  }

  if (loading) return <p>Loading…</p>

  return (
    <main style={{ maxWidth: 420, margin: '3rem auto', textAlign: 'left' }}>
      <h1>NEXORA</h1>

      {user ? (
        <section>
          <p>
            Signed in as <strong>{user.email}</strong>
          </p>
          <button type="button" onClick={onLoadProfile} disabled={busy}>
            Load my profile (FastAPI)
          </button>{' '}
          <button type="button" onClick={onSignOut} disabled={busy}>
            Sign out
          </button>
          {profile && <pre>{JSON.stringify(profile, null, 2)}</pre>}
        </section>
      ) : (
        <form onSubmit={onSignIn}>
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button type="submit" disabled={busy}>
            Sign in
          </button>{' '}
          <button type="button" onClick={onSignUp} disabled={busy || !email || !password}>
            Sign up
          </button>
        </form>
      )}

      {message && <p role="status">{message}</p>}
    </main>
  )
}

export default App
