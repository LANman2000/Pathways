import { useEffect, useState, type FormEvent } from 'react';
type User = { name: string; email: string };
function Mark() { return <svg viewBox="0 0 80 80" fill="none" aria-hidden="true"><path d="M14 65V43c0-12 6-20 19-20h3c13 0 20-8 20-20m0 0L41 19M56 3l16 16" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" /></svg>; }
async function api(path: string, data?: object) {
  const response = await fetch(`/api/${path}`, { method: data ? 'POST' : 'GET', headers: data ? { 'Content-Type': 'application/json' } : {}, body: data ? JSON.stringify(data) : undefined });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || 'Something went wrong. Please try again.');
  return body;
}
// Scope ends at authenticated account confirmation. See docs/HANDOFF.md.
export default function AccountFlow() {
  const [view, setView] = useState<'welcome'|'signup'|'login'>('welcome');
  const [user, setUser] = useState<User|null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => { api('session').then(b => setUser(b.user)).catch(() => setError('Unable to connect to sign-in. Please try again.')).finally(() => setBusy(false)); }, []);
  function navigate(next: typeof view) { setError(''); setView(next); }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return; setBusy(true); setError('');
    const fields = new FormData(event.currentTarget);
    // Handoff point: the host application can route after this server-confirmed success.
    // The next workflow belongs to the onboarding team; no onboarding fields live here.
    try { const body = await api(view === 'signup' ? 'signup' : 'login', Object.fromEntries(fields)); setUser(body.user); }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to sign in.'); }
    finally { setBusy(false); }
  }
  async function logout() { setBusy(true); setError(''); try { await api('logout', {}); setUser(null); setView('welcome'); } catch { setError('Unable to sign out. Please try again.'); } finally { setBusy(false); } }
  return <div className="app"><header><a className="wordmark" href="/" aria-label="Pathways home"><Mark/>Pathways</a><span>Student career explorer</span></header>
    <main><section className="intro"><div className="logo-orbit"><Mark/></div><p className="eyebrow">CAREER EXPLORATION FOR STUDENTS</p><h1>Find your next step.</h1><p className="description">Explore careers based on what you study,<br className="desktop-break"/> what you enjoy, and what you want to try.</p><p className="journey">Build your profile → Explore pathways → Save a next step</p></section>
    <section className="card" aria-label="Pathways account">
      {user ? <><h2>You’re signed in</h2><p className="subtitle">Welcome, {user.name}.</p><p className="account-email">{user.email}</p><p role="status">Your account is ready. Career profile setup will connect here.</p><button disabled={busy} onClick={logout}>Sign out</button></> : view === 'welcome' ? <><h2>Welcome to Pathways</h2><p className="subtitle">Get started or pick up where you left off.</p><div className="welcome-option"><p>New to Pathways?</p><button disabled={busy} onClick={() => navigate('signup')}>Sign up</button></div><div className="welcome-option divided"><p>Already have an account?</p><button className="secondary" disabled={busy} onClick={() => navigate('login')}>Sign in</button></div></> : <>
        <button className="text-button back" disabled={busy} onClick={() => navigate('welcome')}>← Back to welcome</button><h2>{view === 'signup' ? 'Create your account' : 'Sign in to Pathways'}</h2><p className="subtitle">{view === 'signup' ? 'Use your school email to get started.' : 'Welcome back. Sign in to continue.'}</p>
        <form onSubmit={submit} key={view}>
          {view === 'signup' && <label>Full name<input name="name" autoComplete="name" placeholder="Jordan Morgan" required maxLength={100}/></label>}
          <label>School email<input name="email" type="email" autoComplete="username" placeholder="you@uakron.edu" required maxLength={254}/></label>
          <label>Password<input name="password" type="password" autoComplete={view === 'signup' ? 'new-password' : 'current-password'} placeholder={view === 'signup' ? 'Enter a password' : 'Enter your password'} minLength={view === 'signup' ? 8 : undefined} maxLength={128} required/></label>
          {view === 'signup' && <p className="hint">Use at least 8 characters.</p>}
          <button disabled={busy} type="submit">{busy ? 'Please wait…' : view === 'signup' ? 'Create account' : 'Sign in'}</button>
        </form><p className="switch divided">{view === 'signup' ? 'Already have an account?' : 'New to Pathways?'} <button className="text-button" disabled={busy} onClick={() => navigate(view === 'signup' ? 'login' : 'signup')}>{view === 'signup' ? 'Sign in' : 'Sign up'}</button></p>
      </>}{error && <p className="error" role="alert">{error}</p>}
    </section></main></div>;
}
