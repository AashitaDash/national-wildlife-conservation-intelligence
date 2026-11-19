import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Shield,
  User,
  Mail,
  Lock,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ArrowRight,
  Info,
  Sparkles,
  Users,
  Compass,
  TreePine,
  Eye,
  EyeOff,
  Database,
  BarChart3,
  Share2,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../services/api';

type RoleType = 'public' | 'researcher' | 'officer';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { setAuthSession } = useAuth();

  // Form Fields
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [selectedRole, setSelectedRole] = useState<RoleType>('public');

  // Password visibility toggles
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Username availability state
  const [checkingUsername, setCheckingUsername] = useState(false);
  const [usernameStatus, setUsernameStatus] = useState<
    'idle' | 'checking' | 'available' | 'taken' | 'invalid'
  >('idle');
  const [usernameMsg, setUsernameMsg] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);

  // Submission & feedback states
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced real-time username availability checker
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    const trimmed = username.trim();
    if (!trimmed) {
      setUsernameStatus('idle');
      setUsernameMsg('');
      setSuggestions([]);
      setCheckingUsername(false);
      return;
    }

    if (trimmed.length < 3) {
      setUsernameStatus('invalid');
      setUsernameMsg('Username must be at least 3 characters');
      setSuggestions([]);
      setCheckingUsername(false);
      return;
    }
    if (trimmed.length > 30) {
      setUsernameStatus('invalid');
      setUsernameMsg('Username cannot exceed 30 characters');
      setSuggestions([]);
      setCheckingUsername(false);
      return;
    }
    if (!/^[a-zA-Z0-9_.-]+$/.test(trimmed)) {
      setUsernameStatus('invalid');
      setUsernameMsg('Allowed: letters, numbers, underscores, dots, hyphens');
      setSuggestions([]);
      setCheckingUsername(false);
      return;
    }

    setUsernameStatus('checking');
    setCheckingUsername(true);

    debounceTimerRef.current = setTimeout(async () => {
      try {
        const res = await authService.checkUsername(trimmed);
        if (!res.valid) {
          setUsernameStatus('invalid');
          setUsernameMsg(res.message);
          setSuggestions([]);
        } else if (res.available) {
          setUsernameStatus('available');
          setUsernameMsg('Username is available');
          setSuggestions([]);
        } else {
          setUsernameStatus('taken');
          setUsernameMsg('Username is already taken');
          setSuggestions(res.suggestions || []);
        }
      } catch (err) {
        setUsernameStatus('idle');
        setUsernameMsg('Could not verify username availability');
      } finally {
        setCheckingUsername(false);
      }
    }, 400);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [username]);

  // Form Submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    const trimmedFullName = fullName.trim();
    if (!trimmedFullName) {
      setError('Full Name is mandatory and cannot be empty or whitespace.');
      return;
    }
    if (trimmedFullName.length < 2) {
      setError('Full Name must be at least 2 characters.');
      return;
    }

    const trimmedUsername = username.trim();
    if (!trimmedUsername) {
      setError('Username is required.');
      return;
    }

    if (usernameStatus === 'taken') {
      setError('The chosen username is already taken. Please pick another or select a suggestion.');
      return;
    }
    if (usernameStatus === 'invalid') {
      setError(usernameMsg || 'Please choose a valid username.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please verify your password entry.');
      return;
    }

    if (!selectedRole) {
      setError('Please select one of the three account roles.');
      return;
    }

    setSubmitting(true);

    try {
      // Step 1: Initiate registration (dispatches verification & creates pending token)
      const initRes = await authService.initiateRegistration({
        username: trimmedUsername,
        email: email.trim(),
        password,
        full_name: trimmedFullName,
      });

      // Step 2: Auto-verify email with server-generated token/OTP to fulfill immediate activation requirement
      let verifiedToken = '';
      if (initRes.verification_token) {
        const vRes = await authService.verifyEmail({
          email: email.trim(),
          verification_token: initRes.verification_token,
        });
        verifiedToken = vRes.verified_token;
      } else if (initRes.otp_code) {
        const vRes = await authService.verifyEmail({
          email: email.trim(),
          otp_code: initRes.otp_code,
        });
        verifiedToken = vRes.verified_token;
      }

      // Step 3: Complete registration with selected non-admin role
      if (verifiedToken) {
        const authRes = await authService.completeRegistration({
          email: email.trim(),
          verified_token: verifiedToken,
          selected_account_type: selectedRole,
        });

        // Set session
        setAuthSession({
          access_token: authRes.access_token,
          user: authRes.user,
        });

        const roleTitle =
          selectedRole === 'officer'
            ? 'Forest Officer'
            : selectedRole === 'researcher'
            ? 'Researcher'
            : 'General Public';

        setSuccessMsg(`Welcome to NWCIP! Your ${roleTitle} account has been activated.`);

        // Redirect immediately to appropriate role dashboard
        setTimeout(() => {
          if (selectedRole === 'officer') {
            navigate('/officer');
          } else if (selectedRole === 'researcher') {
            navigate('/researcher');
          } else {
            navigate('/');
          }
        }, 1200);
      } else {
        // Fallback for custom SMTP environments
        setSuccessMsg('Account registered! Redirecting to login...');
        setTimeout(() => {
          navigate('/login');
        }, 1500);
      }
    } catch (err: any) {
      console.error('Registration error:', err);
      setError(
        err.response?.data?.detail ||
          (typeof err.message === 'string' ? err.message : 'Registration failed. Please check inputs.')
      );
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row" style={{ backgroundColor: '#faf8f4' }}>
      {/* ═══════════════════════════════════════════════════════════════════════
          LEFT PANEL — WILDLIFE BRANDING (42% desktop viewport)
          ═══════════════════════════════════════════════════════════════════════ */}
      <div
        className="relative lg:w-[42%] xl:w-[40%] flex flex-col justify-between p-8 sm:p-12 lg:p-14 overflow-hidden shrink-0"
        style={{
          backgroundColor: '#0c2113',
          minHeight: '420px',
        }}
      >
        {/* Background Wildlife Photographic Imagery: Chital / Spotted Deer in golden light */}
        <div
          className="absolute inset-0 w-full h-full bg-cover bg-center transition-transform duration-1000 scale-105"
          style={{
            backgroundImage: 'url(/chital-deer-bg.jpg)',
            backgroundPosition: 'center 35%',
          }}
        />

        {/* Deep forest green organic gradient overlay for crisp typography */}
        <div
          className="absolute inset-0 w-full h-full"
          style={{
            background:
              'linear-gradient(175deg, rgba(8, 28, 15, 0.78) 0%, rgba(10, 32, 17, 0.88) 50%, rgba(5, 18, 10, 0.96) 100%)',
          }}
        />

        {/* Subtle decorative topographic contour lines pattern */}
        <div
          className="absolute inset-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(ellipse at 30% 20%, rgba(134, 239, 172, 0.3) 0%, transparent 60%),
                              radial-gradient(ellipse at 70% 80%, rgba(74, 222, 128, 0.2) 0%, transparent 70%)`,
          }}
        />

        {/* Top Branding Section */}
        <div className="relative z-10 flex items-center gap-3">
          <div
            className="w-9 h-9 flex items-center justify-center shrink-0 shadow-lg border border-emerald-400/30"
            style={{
              backgroundColor: '#11682f',
              borderRadius: '6px',
            }}
          >
            <Shield className="w-5 h-5 text-emerald-200" />
          </div>
          <div>
            <span
              className="block font-mono text-[11px] font-bold tracking-[0.22em] uppercase leading-none"
              style={{ color: '#4ade80' }}
            >
              WILDLIFE INTELLIGENCE
            </span>
            <span
              className="block font-mono text-[9px] tracking-[0.14em] uppercase text-emerald-100/70 mt-1"
            >
              NATIONAL WILDLIFE CONSERVATION INTELLIGENCE PLATFORM (NWCIP)
            </span>
          </div>
        </div>

        {/* Middle Editorial Hero Section */}
        <div className="relative z-10 my-10 lg:my-auto">
          {/* Main Headline */}
          <h1
            className="font-serif text-3xl sm:text-4xl lg:text-5xl font-bold leading-[1.18] tracking-tight text-white mb-5"
            style={{ fontFamily: "'Newsreader', Georgia, serif" }}
          >
            Build a Safer, Smarter Future for{' '}
            <span
              className="inline-block relative"
              style={{
                color: '#bef264', // Subtle lime-green accent
                fontStyle: 'italic',
                fontWeight: 600,
              }}
            >
              Our Wildlife
            </span>
          </h1>

          {/* Supporting Text */}
          <p className="text-sm leading-relaxed text-emerald-100/85 max-w-md font-sans mb-10">
            Join NWCIP to access intelligence tools, research insights and conservation
            resources in a unified platform.
          </p>

          {/* Feature Highlights with elegant icons */}
          <div className="space-y-4 max-w-sm">
            <div className="flex items-start gap-3.5 group">
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 border border-emerald-400/25 bg-emerald-950/60 shadow-sm"
              >
                <Database className="w-4 h-4 text-emerald-300" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white tracking-wide uppercase font-mono">
                  Access Conservation Data
                </h4>
                <p className="text-xs text-emerald-200/70 mt-0.5 leading-snug">
                  Real-time insights and analytics
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3.5 group">
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 border border-emerald-400/25 bg-emerald-950/60 shadow-sm"
              >
                <BarChart3 className="w-4 h-4 text-emerald-300" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white tracking-wide uppercase font-mono">
                  Explore & Monitor
                </h4>
                <p className="text-xs text-emerald-200/70 mt-0.5 leading-snug">
                  Species, habitats and threats
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3.5 group">
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 border border-emerald-400/25 bg-emerald-950/60 shadow-sm"
              >
                <Share2 className="w-4 h-4 text-emerald-300" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white tracking-wide uppercase font-mono">
                  Contribute & Collaborate
                </h4>
                <p className="text-xs text-emerald-200/70 mt-0.5 leading-snug">
                  Support wildlife protection efforts
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Attribution */}
        <div className="relative z-10 pt-6 border-t border-emerald-800/40 flex items-center justify-between text-[10px] font-mono tracking-wider text-emerald-300/60">
          <span>MINISTRY OF ENVIRONMENT & FORESTS</span>
          <span>SECURE REPOSITORY</span>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════════
          RIGHT PANEL — REGISTRATION CARD
          ═══════════════════════════════════════════════════════════════════════ */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-8 lg:p-12 overflow-y-auto">
        <div
          className="w-full max-w-xl p-6 sm:p-10 rounded-2xl border shadow-xl relative"
          style={{
            backgroundColor: 'rgba(255, 255, 255, 0.94)',
            backdropFilter: 'blur(12px)',
            borderColor: '#e8e4dc',
            boxShadow: '0 20px 40px -15px rgba(26, 42, 30, 0.08), 0 1px 3px rgba(0, 0, 0, 0.03)',
          }}
        >
          {/* Card Header */}
          <div className="mb-6">
            <h2
              className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-[#1a1916] mb-1.5"
              style={{ fontFamily: "'Newsreader', Georgia, serif" }}
            >
              Create Your Account
            </h2>
            <p className="text-xs sm:text-sm text-[#66635b]">
              Register for secure access to the NWCIP conservation network.
            </p>
          </div>

          {/* Informational Banner */}
          <div
            className="flex items-start gap-2.5 p-3.5 mb-6 text-xs leading-relaxed rounded-lg border"
            style={{
              backgroundColor: '#f3f8f4',
              borderColor: '#cce5d3',
              color: '#1b4d29',
            }}
          >
            <Info className="w-4 h-4 shrink-0 mt-0.5 text-[#11682f]" />
            <div className="text-[11.5px] sm:text-xs">
              <strong>Account Access:</strong> Choose your role to access the relevant
              conservation intelligence tools and dashboards. Your account will be activated
              immediately after successful registration.
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              className="flex items-start gap-2.5 p-3.5 mb-5 text-xs rounded-lg border animate-fadeIn"
              style={{
                backgroundColor: '#fff1f0',
                borderColor: '#fca5a5',
                color: '#b91c1c',
              }}
            >
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Success Banner */}
          {successMsg && (
            <div
              className="flex items-start gap-2.5 p-3.5 mb-5 text-xs rounded-lg border animate-fadeIn"
              style={{
                backgroundColor: '#f0fdf4',
                borderColor: '#86efac',
                color: '#166534',
              }}
            >
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
            {/* ─────────────────────────────────────────────────────────────
                ROW 1: Full Name | Username
                ───────────────────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Full Name */}
              <div>
                <label className="block font-mono text-[10px] font-semibold tracking-wider uppercase mb-1.5 text-[#5e5b54]">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-[#9c998e]">
                    <User className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Dr. Salim Ali"
                    required
                    className="w-full pl-10 pr-3.5 py-2.5 text-xs sm:text-sm rounded-lg border outline-none transition-all duration-200"
                    style={{
                      backgroundColor: '#ffffff',
                      borderColor: '#ddd8cf',
                      color: '#1a1916',
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#11682f';
                      e.target.style.boxShadow = '0 0 0 3px rgba(17, 104, 47, 0.12)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#ddd8cf';
                      e.target.style.boxShadow = 'none';
                    }}
                  />
                </div>
              </div>

              {/* Username with Real-time Availability & Suggestions */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block font-mono text-[10px] font-semibold tracking-wider uppercase text-[#5e5b54]">
                    Username <span className="text-red-500">*</span>
                  </label>
                  {usernameStatus === 'checking' && (
                    <span className="flex items-center gap-1 text-[10px] font-mono text-[#77746c]">
                      <Loader2 className="w-3 h-3 animate-spin text-[#11682f]" />
                      Checking...
                    </span>
                  )}
                  {usernameStatus === 'available' && (
                    <span className="flex items-center gap-1 text-[10px] font-mono text-[#11682f] font-semibold">
                      <CheckCircle2 className="w-3 h-3" />
                      Available
                    </span>
                  )}
                  {usernameStatus === 'taken' && (
                    <span className="flex items-center gap-1 text-[10px] font-mono text-[#dc2626] font-semibold">
                      <AlertCircle className="w-3 h-3" />
                      Taken
                    </span>
                  )}
                  {usernameStatus === 'invalid' && (
                    <span className="flex items-center gap-1 text-[10px] font-mono text-[#d97706]">
                      <AlertCircle className="w-3 h-3" />
                      Invalid
                    </span>
                  )}
                </div>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-[#9c998e]">
                    <User className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="salim_ali"
                    required
                    minLength={3}
                    maxLength={30}
                    className="w-full pl-10 pr-3.5 py-2.5 text-xs sm:text-sm font-mono rounded-lg border outline-none transition-all duration-200"
                    style={{
                      backgroundColor: '#ffffff',
                      borderColor:
                        usernameStatus === 'available'
                          ? '#16a34a'
                          : usernameStatus === 'taken'
                          ? '#dc2626'
                          : usernameStatus === 'invalid'
                          ? '#d97706'
                          : '#ddd8cf',
                      color: '#1a1916',
                    }}
                    onFocus={(e) => {
                      e.target.style.boxShadow = '0 0 0 3px rgba(17, 104, 47, 0.12)';
                    }}
                    onBlur={(e) => {
                      e.target.style.boxShadow = 'none';
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Username Suggestions Pill List when Taken */}
            {usernameStatus === 'taken' && suggestions.length > 0 && (
              <div className="p-2.5 bg-amber-50/70 border border-amber-200/80 rounded-lg text-xs">
                <div className="flex items-center gap-1.5 text-[11px] font-mono font-semibold text-amber-900 mb-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                  <span>Available Suggestions (Click to apply):</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {suggestions.map((sug) => (
                    <button
                      key={sug}
                      type="button"
                      onClick={() => setUsername(sug)}
                      className="px-2.5 py-0.5 text-xs font-mono font-medium rounded-md border border-amber-300 bg-white text-amber-900 hover:bg-amber-100 transition-colors"
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* ─────────────────────────────────────────────────────────────
                ROW 2: Email Address (full width)
                ───────────────────────────────────────────────────────────── */}
            <div>
              <label className="block font-mono text-[10px] font-semibold tracking-wider uppercase mb-1.5 text-[#5e5b54]">
                Email Address <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-[#9c998e]">
                  <Mail className="w-4 h-4" />
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="salim.ali@bnhs.org"
                  required
                  className="w-full pl-10 pr-3.5 py-2.5 text-xs sm:text-sm rounded-lg border outline-none transition-all duration-200"
                  style={{
                    backgroundColor: '#ffffff',
                    borderColor: '#ddd8cf',
                    color: '#1a1916',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#11682f';
                    e.target.style.boxShadow = '0 0 0 3px rgba(17, 104, 47, 0.12)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#ddd8cf';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>
            </div>

            {/* ─────────────────────────────────────────────────────────────
                ROW 3: Select Your Role (Three visual interactive cards)
                ───────────────────────────────────────────────────────────── */}
            <div>
              <label className="block font-mono text-[10px] font-semibold tracking-wider uppercase mb-2 text-[#5e5b54]">
                Select Your Role <span className="text-red-500">*</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* CARD 1: GENERAL PUBLIC */}
                <div
                  onClick={() => setSelectedRole('public')}
                  role="button"
                  tabIndex={0}
                  className="relative p-3.5 sm:p-4 rounded-xl border text-left cursor-pointer transition-all duration-200 group flex flex-col justify-between"
                  style={{
                    backgroundColor: selectedRole === 'public' ? '#f2f9f4' : '#ffffff',
                    borderColor: selectedRole === 'public' ? '#11682f' : '#e4e0d7',
                    boxShadow:
                      selectedRole === 'public'
                        ? '0 0 0 1.5px #11682f, 0 4px 12px rgba(17, 104, 47, 0.08)'
                        : '0 1px 3px rgba(0,0,0,0.02)',
                  }}
                  onKeyDown={(e) => {
                    if (e.key === ' ' || e.key === 'Enter') setSelectedRole('public');
                  }}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
                        style={{
                          backgroundColor: selectedRole === 'public' ? '#11682f' : '#f4f2ec',
                          color: selectedRole === 'public' ? '#ffffff' : '#4a4842',
                        }}
                      >
                        <Users className="w-4 h-4" />
                      </div>
                      <div
                        className="w-4 h-4 rounded-full border flex items-center justify-center"
                        style={{
                          borderColor: selectedRole === 'public' ? '#11682f' : '#c8c4bb',
                          backgroundColor: selectedRole === 'public' ? '#11682f' : 'transparent',
                        }}
                      >
                        {selectedRole === 'public' && (
                          <div className="w-1.5 h-1.5 bg-white rounded-full" />
                        )}
                      </div>
                    </div>
                    <div className="font-bold text-xs sm:text-sm text-[#1a1916]">
                      General Public
                    </div>
                    <p className="text-[11px] text-[#6b675e] mt-1 leading-relaxed">
                      Explore data, learn and stay informed.
                    </p>
                  </div>
                </div>

                {/* CARD 2: RESEARCHER */}
                <div
                  onClick={() => setSelectedRole('researcher')}
                  role="button"
                  tabIndex={0}
                  className="relative p-3.5 sm:p-4 rounded-xl border text-left cursor-pointer transition-all duration-200 group flex flex-col justify-between"
                  style={{
                    backgroundColor: selectedRole === 'researcher' ? '#f2f9f4' : '#ffffff',
                    borderColor: selectedRole === 'researcher' ? '#11682f' : '#e4e0d7',
                    boxShadow:
                      selectedRole === 'researcher'
                        ? '0 0 0 1.5px #11682f, 0 4px 12px rgba(17, 104, 47, 0.08)'
                        : '0 1px 3px rgba(0,0,0,0.02)',
                  }}
                  onKeyDown={(e) => {
                    if (e.key === ' ' || e.key === 'Enter') setSelectedRole('researcher');
                  }}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
                        style={{
                          backgroundColor: selectedRole === 'researcher' ? '#11682f' : '#f4f2ec',
                          color: selectedRole === 'researcher' ? '#ffffff' : '#4a4842',
                        }}
                      >
                        <Compass className="w-4 h-4" />
                      </div>
                      <div
                        className="w-4 h-4 rounded-full border flex items-center justify-center"
                        style={{
                          borderColor: selectedRole === 'researcher' ? '#11682f' : '#c8c4bb',
                          backgroundColor: selectedRole === 'researcher' ? '#11682f' : 'transparent',
                        }}
                      >
                        {selectedRole === 'researcher' && (
                          <div className="w-1.5 h-1.5 bg-white rounded-full" />
                        )}
                      </div>
                    </div>
                    <div className="font-bold text-xs sm:text-sm text-[#1a1916]">
                      Researcher
                    </div>
                    <p className="text-[11px] text-[#6b675e] mt-1 leading-relaxed">
                      Analyze data, conduct studies and contribute insights.
                    </p>
                  </div>
                </div>

                {/* CARD 3: FOREST OFFICER */}
                <div
                  onClick={() => setSelectedRole('officer')}
                  role="button"
                  tabIndex={0}
                  className="relative p-3.5 sm:p-4 rounded-xl border text-left cursor-pointer transition-all duration-200 group flex flex-col justify-between"
                  style={{
                    backgroundColor: selectedRole === 'officer' ? '#f2f9f4' : '#ffffff',
                    borderColor: selectedRole === 'officer' ? '#11682f' : '#e4e0d7',
                    boxShadow:
                      selectedRole === 'officer'
                        ? '0 0 0 1.5px #11682f, 0 4px 12px rgba(17, 104, 47, 0.08)'
                        : '0 1px 3px rgba(0,0,0,0.02)',
                  }}
                  onKeyDown={(e) => {
                    if (e.key === ' ' || e.key === 'Enter') setSelectedRole('officer');
                  }}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
                        style={{
                          backgroundColor: selectedRole === 'officer' ? '#11682f' : '#f4f2ec',
                          color: selectedRole === 'officer' ? '#ffffff' : '#4a4842',
                        }}
                      >
                        <TreePine className="w-4 h-4" />
                      </div>
                      <div
                        className="w-4 h-4 rounded-full border flex items-center justify-center"
                        style={{
                          borderColor: selectedRole === 'officer' ? '#11682f' : '#c8c4bb',
                          backgroundColor: selectedRole === 'officer' ? '#11682f' : 'transparent',
                        }}
                      >
                        {selectedRole === 'officer' && (
                          <div className="w-1.5 h-1.5 bg-white rounded-full" />
                        )}
                      </div>
                    </div>
                    <div className="font-bold text-xs sm:text-sm text-[#1a1916]">
                      Forest Officer
                    </div>
                    <p className="text-[11px] text-[#6b675e] mt-1 leading-relaxed">
                      Monitor wildlife, manage field intelligence and support enforcement.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* ─────────────────────────────────────────────────────────────
                ROW 4: Password | Confirm Password
                ───────────────────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Password */}
              <div>
                <label className="block font-mono text-[10px] font-semibold tracking-wider uppercase mb-1.5 text-[#5e5b54]">
                  Password (Min 8 chars) <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-[#9c998e]">
                    <Lock className="w-4 h-4" />
                  </span>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    minLength={8}
                    className="w-full pl-10 pr-10 py-2.5 text-xs sm:text-sm rounded-lg border outline-none transition-all duration-200"
                    style={{
                      backgroundColor: '#ffffff',
                      borderColor: '#ddd8cf',
                      color: '#1a1916',
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#11682f';
                      e.target.style.boxShadow = '0 0 0 3px rgba(17, 104, 47, 0.12)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#ddd8cf';
                      e.target.style.boxShadow = 'none';
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9c998e] hover:text-[#4a4842]"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block font-mono text-[10px] font-semibold tracking-wider uppercase mb-1.5 text-[#5e5b54]">
                  Confirm Password <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-[#9c998e]">
                    <Lock className="w-4 h-4" />
                  </span>
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    minLength={8}
                    className="w-full pl-10 pr-10 py-2.5 text-xs sm:text-sm rounded-lg border outline-none transition-all duration-200"
                    style={{
                      backgroundColor: '#ffffff',
                      borderColor: '#ddd8cf',
                      color: '#1a1916',
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#11682f';
                      e.target.style.boxShadow = '0 0 0 3px rgba(17, 104, 47, 0.12)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#ddd8cf';
                      e.target.style.boxShadow = 'none';
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9c998e] hover:text-[#4a4842]"
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* ─────────────────────────────────────────────────────────────
                PRIMARY ACTION: Full-width Deep-Green Button
                ───────────────────────────────────────────────────────────── */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={submitting || checkingUsername || usernameStatus === 'taken'}
                className="w-full flex items-center justify-center gap-2 py-3 px-6 text-sm font-semibold tracking-wide rounded-xl shadow-md transition-all duration-200"
                style={{
                  backgroundColor: '#11682f',
                  color: '#ffffff',
                  opacity:
                    submitting || checkingUsername || usernameStatus === 'taken' ? 0.7 : 1,
                  cursor:
                    submitting || checkingUsername || usernameStatus === 'taken'
                      ? 'not-allowed'
                      : 'pointer',
                }}
                onMouseEnter={(e) => {
                  if (!submitting && usernameStatus !== 'taken') {
                    (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#0d5425';
                    (e.currentTarget as HTMLButtonElement).style.boxShadow =
                      '0 6px 20px rgba(17, 104, 47, 0.25)';
                  }
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#11682f';
                  (e.currentTarget as HTMLButtonElement).style.boxShadow = 'none';
                }}
                onMouseDown={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.transform = 'scale(0.99)';
                }}
                onMouseUp={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)';
                }}
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                    <span>CREATING ACCOUNT...</span>
                  </>
                ) : (
                  <>
                    <span>Create Account</span>
                    <ArrowRight className="w-4 h-4 text-emerald-200" />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Footer Navigation Link */}
          <p className="mt-6 text-center text-xs text-[#7d7a71]">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-semibold transition-colors duration-150"
              style={{ color: '#11682f' }}
            >
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
