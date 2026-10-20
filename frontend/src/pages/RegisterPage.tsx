import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, User, Mail, Lock, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const inputStyle = {
  backgroundColor: '#ffffff',
  border: '1px solid #ddd8cf',
  borderRadius: '3px',
  color: '#1a1916',
  fontFamily: 'inherit',
};

const InputField: React.FC<{
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
  minLength?: number;
  icon: React.ReactNode;
}> = ({ label, type = 'text', value, onChange, placeholder, required, minLength, icon }) => (
  <div>
    <label
      className="block font-mono text-[10px] font-semibold tracking-widest uppercase mb-1.5"
      style={{ color: '#5e5b54' }}
    >
      {label}
    </label>
    <div className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: '#b5b3a9' }}>
        {icon}
      </span>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        minLength={minLength}
        className="w-full pl-9 pr-4 py-2.5 text-sm outline-none transition-all"
        style={inputStyle}
        onFocus={e => { e.target.style.borderColor = '#1fa34a'; e.target.style.boxShadow = '0 0 0 2px rgba(31,163,74,0.15)'; }}
        onBlur={e  => { e.target.style.borderColor = '#ddd8cf'; e.target.style.boxShadow = 'none'; }}
      />
    </div>
  </div>
);

export const RegisterPage: React.FC = () => {
  const [username, setUsername]   = useState('');
  const [email, setEmail]         = useState('');
  const [fullName, setFullName]   = useState('');
  const [password, setPassword]   = useState('');
  const [error, setError]         = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { register } = useAuth();
  const navigate     = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register({ username, email, password, full_name: fullName });
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please check inputs.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ backgroundColor: '#faf8f4' }}>
      <div className="w-full max-w-sm">
        {/* Brand */}
        <div className="flex items-center gap-2.5 mb-8">
          <div
            className="w-8 h-8 flex items-center justify-center shrink-0"
            style={{ backgroundColor: '#11682f', borderRadius: '3px' }}
          >
            <Shield className="w-4 h-4 text-white" />
          </div>
          <div>
            <span className="block font-mono text-[10px] tracking-widest uppercase font-semibold" style={{ color: '#13843a' }}>
              WILDLIFE INTELLIGENCE
            </span>
            <span className="block font-mono text-[9px] tracking-widest uppercase" style={{ color: '#94918a' }}>
              CONSERVATION DECISION SUPPORT
            </span>
          </div>
        </div>

        <h1
          className="font-serif text-3xl font-bold mb-1"
          style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}
        >
          Create Account
        </h1>
        <p className="text-sm mb-7" style={{ color: '#77746c' }}>
          Register for access to the conservation intelligence platform.
        </p>

        {error && (
          <div
            className="flex items-start gap-2.5 p-3 mb-5 text-xs"
            style={{ backgroundColor: '#fff1f0', border: '1px solid #fca5a5', borderRadius: '3px', color: '#b91c1c' }}
          >
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <InputField
            label="Username"
            value={username}
            onChange={setUsername}
            placeholder="Choose username"
            required
            icon={<User className="w-3.5 h-3.5" />}
          />
          <InputField
            label="Email Address"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="user@conservation.org"
            required
            icon={<Mail className="w-3.5 h-3.5" />}
          />
          <InputField
            label="Full Name (Optional)"
            value={fullName}
            onChange={setFullName}
            placeholder="Dr. Jane Goodall"
            icon={<User className="w-3.5 h-3.5" />}
          />
          <InputField
            label="Password (Min 8 chars)"
            type="password"
            value={password}
            onChange={setPassword}
            placeholder="••••••••"
            required
            minLength={8}
            icon={<Lock className="w-3.5 h-3.5" />}
          />

          <button
            type="submit"
            disabled={submitting}
            className="w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold tracking-wide mt-2"
            style={{
              backgroundColor: '#11682f',
              color: '#ffffff',
              borderRadius: '3px',
              opacity: submitting ? 0.8 : 1,
              cursor: submitting ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? 'CREATING ACCOUNT...' : 'CREATE ACCOUNT'}
            {!submitting && <ArrowRight className="w-4 h-4" />}
          </button>
        </form>

        <p className="mt-6 text-center text-xs" style={{ color: '#94918a' }}>
          Already have an account?{' '}
          <Link to="/login" className="font-medium" style={{ color: '#13843a' }}>
            Sign in here
          </Link>
        </p>
      </div>
    </div>
  );
};
