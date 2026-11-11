import { Component, StrictMode } from 'react'
import type { ReactNode, ErrorInfo } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/index.css'
import App from './App.tsx'
import { AuthProvider } from './auth/AuthProvider.tsx'

// ── Startup Error Boundary ────────────────────────────────────────────────────
// Catches module-level errors (e.g. missing env vars) before React mounts,
// and shows a human-readable message instead of a blank screen.
class StartupErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[Nexora] Startup error:', error, info)
  }

  render() {
    const { error } = this.state
    if (error) {
      return (
        <div style={{
          minHeight: '100vh', display: 'flex', alignItems: 'center',
          justifyContent: 'center', background: '#F5F6F4', padding: '1.5rem',
          fontFamily: 'system-ui, sans-serif',
        }}>
          <div style={{
            maxWidth: 480, background: '#fff', border: '1px solid #e2e5e9',
            borderRadius: 12, padding: '2rem', boxShadow: '0 2px 8px rgba(0,0,0,.08)',
          }}>
            <h2 style={{ margin: '0 0 .5rem', color: '#c0392b', fontSize: '1rem' }}>
              ⚠ App failed to start
            </h2>
            <p style={{ margin: '0 0 1rem', color: '#555', fontSize: '.85rem' }}>
              {error.message}
            </p>
            <p style={{ margin: 0, color: '#888', fontSize: '.8rem' }}>
              Make sure <code>frontend/.env.local</code> exists with your real{' '}
              <code>VITE_SUPABASE_URL</code> and{' '}
              <code>VITE_SUPABASE_PUBLISHABLE_KEY</code> values, then restart{' '}
              <code>npm run dev</code>.
            </p>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <StartupErrorBoundary>
      <AuthProvider>
        <App />
      </AuthProvider>
    </StartupErrorBoundary>
  </StrictMode>,
)
