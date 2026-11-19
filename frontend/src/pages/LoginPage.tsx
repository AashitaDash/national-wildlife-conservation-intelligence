import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Lock, User, AlertCircle, ArrowRight, Eye } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { RoleName } from '../types';

const CAPABILITIES = [
  { label: 'FIELD OBSERVATIONS',   icon: '◉' },
  { label: 'THREAT ANALYSIS',      icon: '◈' },
  { label: 'SPECIES INTELLIGENCE', icon: '◆' },
  { label: 'SPATIAL MONITORING',   icon: '◎' },
];

const DEMO_USERS: { username: string; role: RoleName; label: string; password: string }[] = [
  { username: 'citizen@gmail.com',         role: 'CITIZEN',        label: 'PUBLIC',     password: 'Citizen@123' },
  { username: 'researcher@wildlife.gov.in', role: 'RESEARCHER',    label: 'RESEARCHER', password: 'Researcher@123' },
  { username: 'officer@forest.gov.in',     role: 'FOREST_OFFICER', label: 'OFFICER',    password: 'Officer@123' },
  { username: 'admin@wildlife.gov.in',     role: 'ADMIN',          label: 'ADMIN',      password: 'Admin@123' },
];

export const LoginPage: React.FC = () => {
  const [username, setUsername]   = useState('');
  const [password, setPassword]   = useState('');
  const [showPass, setShowPass]   = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate  = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const loggedInUser = await login(username, password);
      const roles = loggedInUser.roles?.map(r => r.name) || [];
      if (roles.includes('ADMIN')) {
        navigate('/admin');
      } else if (roles.includes('FOREST_OFFICER')) {
        navigate('/officer');
      } else if (roles.includes('RESEARCHER')) {
        navigate('/researcher');
      } else {
        navigate('/');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Check credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const applyDemo = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
    setError(null);
  };

  return (
    <div className="min-h-screen flex" style={{ fontFamily: "'Instrument Sans', sans-serif" }}>
      {/* ══════════ LEFT — editorial dark panel ══════════ */}
      <div
        className="hidden lg:flex flex-col w-1/2 p-12 relative overflow-hidden"
        style={{ backgroundColor: '#0f0e0c' }}
      >
        {/* Cinematic Wildlife Background */}
        <div
          className="absolute inset-0 w-full h-full bg-cover bg-center"
          style={{
            backgroundImage: 'url(/login-bg.jpg)',
            backgroundPosition: 'center 40%',
            opacity: 0.6
          }}
        />
        {/* Gradient overlay to ensure text readability */}
        <div
          className="absolute inset-0 w-full h-full"
          style={{
            background: 'linear-gradient(180deg, rgba(15,14,12,0.3) 0%, rgba(15,14,12,0.9) 100%)'
          }}
        />

        {/* Top-left brand */}
        <div className="flex items-center gap-2.5 relative z-10">
          <div
            className="w-7 h-7 flex items-center justify-center shrink-0"
            style={{ backgroundColor: '#11682f', borderRadius: '2px' }}
          >
            <Shield className="w-3.5 h-3.5 text-white" />
          </div>
          <span
            className="font-mono text-[10px] font-semibold tracking-[0.2em] uppercase"
            style={{ color: '#3fc067' }}
          >
            SECURE PORTAL
          </span>
        </div>

        {/* Main editorial heading */}
        <div className="flex-1 flex flex-col justify-center relative z-10">
          <h1
            className="font-serif text-7xl font-bold leading-none mb-8"
            style={{ color: '#faf8f4', fontFamily: "'Newsreader', Georgia, serif" }}
          >
            WILDLIFE<br />
            <span style={{ color: '#f0ede6', fontWeight: 300, fontStyle: 'italic' }}>
              CONSERVATION
            </span><br />
            INTELLIGENCE
          </h1>

          {/* Accent line + tagline */}
          <div className="flex items-start gap-4 mb-12">
            <div className="w-0.5 h-12 mt-1 shrink-0" style={{ backgroundColor: '#1fa34a' }} />
            <p
              className="text-sm leading-relaxed"
              style={{ color: '#5e5b54', maxWidth: '280px' }}
            >
              Evidence-driven intelligence for wildlife monitoring, research and conservation.
            </p>
          </div>

          {/* Capability labels */}
          <div className="space-y-2">
            {CAPABILITIES.map(({ label, icon }) => (
              <div
                key={label}
                className="flex items-center gap-3"
              >
                <span
                  className="font-mono text-xs"
                  style={{ color: '#1fa34a' }}
                >
                  {icon}
                </span>
                <span
                  className="font-mono text-[10px] tracking-[0.18em] uppercase"
                  style={{ color: '#3a3a35' }}
                >
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom attribution */}
        <p
          className="font-mono text-[9px] tracking-widest uppercase relative z-10"
          style={{ color: '#2a2924' }}
        >
          NATIONAL WILDLIFE CONSERVATION AUTHORITY
        </p>
      </div>

      {/* ══════════ RIGHT — cream login panel ══════════ */}
      <div
        className="flex-1 lg:w-1/2 flex items-center justify-center p-8 lg:p-16"
        style={{ backgroundColor: '#faf8f4' }}
      >
        <div className="w-full max-w-sm">
          {/* Heading */}
          <div className="mb-8">
            {/* Mobile-only brand */}
            <div className="lg:hidden flex items-center gap-2 mb-6">
              <div
                className="w-7 h-7 flex items-center justify-center"
                style={{ backgroundColor: '#11682f', borderRadius: '2px' }}
              >
                <Shield className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="font-mono text-[10px] tracking-widest uppercase" style={{ color: '#1fa34a' }}>
                WILDLIFE INTELLIGENCE
              </span>
            </div>

            <h2
              className="font-serif text-3xl font-bold mb-2"
              style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}
            >
              Welcome back
            </h2>
            <p className="text-sm" style={{ color: '#77746c' }}>
              Sign in to the conservation intelligence platform.
            </p>
          </div>

          {/* Error */}
          {error && (
            <div
              className="flex items-start gap-2.5 p-3 mb-5 text-xs"
              style={{
                backgroundColor: '#fff1f0',
                border: '1px solid #fca5a5',
                borderRadius: '3px',
                color: '#b91c1c',
              }}
            >
              <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label
                className="block font-mono text-[10px] font-semibold tracking-widest uppercase mb-1.5"
                style={{ color: '#5e5b54' }}
              >
                USERNAME
              </label>
              <div className="relative">
                <User
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none"
                  style={{ color: '#b5b3a9' }}
                />
                <input
                  type="text"
                  required
                  autoComplete="username"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  placeholder="Enter username"
                  className="w-full pl-9 pr-4 py-2.5 text-sm transition-all outline-none"
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #ddd8cf',
                    borderRadius: '3px',
                    color: '#1a1916',
                    fontFamily: 'inherit',
                  }}
                  onFocus={e => { e.target.style.borderColor = '#1fa34a'; e.target.style.boxShadow = '0 0 0 2px rgba(31,163,74,0.15)'; }}
                  onBlur={e  => { e.target.style.borderColor = '#ddd8cf'; e.target.style.boxShadow = 'none'; }}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                className="block font-mono text-[10px] font-semibold tracking-widest uppercase mb-1.5"
                style={{ color: '#5e5b54' }}
              >
                PASSWORD
              </label>
              <div className="relative">
                <Lock
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none"
                  style={{ color: '#b5b3a9' }}
                />
                <input
                  type={showPass ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-10 py-2.5 text-sm transition-all outline-none"
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #ddd8cf',
                    borderRadius: '3px',
                    color: '#1a1916',
                    fontFamily: 'inherit',
                  }}
                  onFocus={e => { e.target.style.borderColor = '#1fa34a'; e.target.style.boxShadow = '0 0 0 2px rgba(31,163,74,0.15)'; }}
                  onBlur={e  => { e.target.style.borderColor = '#ddd8cf'; e.target.style.boxShadow = 'none'; }}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  style={{ color: '#b5b3a9' }}
                >
                  <Eye className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold tracking-wide transition-all"
              style={{
                backgroundColor: submitting ? '#13843a' : '#11682f',
                color: '#ffffff',
                borderRadius: '3px',
                opacity: submitting ? 0.8 : 1,
                cursor: submitting ? 'not-allowed' : 'pointer',
              }}
              onMouseEnter={e => { if (!submitting) (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#0f5126'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#11682f'; }}
            >
              {submitting ? 'AUTHENTICATING...' : 'SIGN IN'}
              {!submitting && <ArrowRight className="w-4 h-4" />}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px" style={{ backgroundColor: '#e5e0d8' }} />
            <span className="font-mono text-[9px] tracking-widest uppercase" style={{ color: '#b5b3a9' }}>
              DEMO PRESET ROLES
            </span>
            <div className="flex-1 h-px" style={{ backgroundColor: '#e5e0d8' }} />
          </div>

          {/* Demo buttons */}
          <div className="grid grid-cols-3 gap-2">
            {DEMO_USERS.map(({ username: u, label, password: p }) => (
              <button
                key={u}
                type="button"
                onClick={() => applyDemo(u, p)}
                className="py-2 text-[10px] font-mono font-semibold tracking-widest uppercase transition-all"
                style={{
                  backgroundColor: '#f5f1ea',
                  border: '1px solid #ddd8cf',
                  borderRadius: '3px',
                  color: '#484640',
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#eae5db'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#f5f1ea'; }}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Register link */}
          <p className="mt-6 text-center text-xs" style={{ color: '#94918a' }}>
            Don't have an account?{' '}
            <Link
              to="/register"
              className="font-medium transition-colors"
              style={{ color: '#13843a' }}
            >
              Register here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
