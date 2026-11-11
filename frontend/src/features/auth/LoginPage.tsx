import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { GraduationCap, Eye, EyeOff, Lock, Mail, ArrowRight, ArrowLeft } from 'lucide-react';
import { Button } from '../../components/common/UIComponents';
import { useAuth } from '../../auth/AuthContext';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname || '/app/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please provide both your college email and password.');
      return;
    }

    setLoading(true);
    try {
      const { error: signInError } = await signIn(email.trim(), password);
      if (signInError) {
        setError(signInError);
        return;
      }
      navigate(from, { replace: true });
    } finally {
      setLoading(false);
    }
  };

  const handleSsoClick = () => {
    setError('University SSO is not enabled yet. Please sign in with your email and password.');
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex">
      {/* Left Column: Form Section */}
      <div className="w-full lg:w-1/2 flex flex-col justify-between p-6 sm:p-10 md:p-12 lg:p-16">
        {/* Top Navigation */}
        <div className="flex items-center justify-between">
          <Link to="/" className="inline-flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-sm bg-[#162232] text-white flex items-center justify-center font-bold shadow-xs">
              <GraduationCap className="w-4 h-4 text-coral-400" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-display font-black text-xl tracking-tight text-slate-900">NEXORA</span>
              <span className="text-[10px] text-slate-500 font-mono tracking-wider uppercase">
                Co-pilot
              </span>
            </div>
          </Link>

          <Link 
            to="/" 
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to website</span>
          </Link>
        </div>

        {/* Center Content Box */}
        <div className="max-w-md w-full mx-auto my-auto py-8">
          <div className="mb-6">
            <h1 className="font-display text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Welcome back
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-1.5">
              Enter your student credentials to continue your placement pipeline.
            </p>
          </div>

          {/* Quick SSO Button (Dribbble-style institutional auth) */}
          <button
            type="button"
            onClick={handleSsoClick}
            disabled={loading}
            className="w-full py-2.5 px-4 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-bold text-slate-700 shadow-xs flex items-center justify-center gap-2.5 transition-all hover:border-slate-300"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
            </svg>
            <span>Continue with University SSO / Google</span>
          </button>

          {/* Divider */}
          <div className="relative my-5 text-center text-xs text-slate-400">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <span className="relative bg-[#F8F9FA] px-3 font-medium uppercase tracking-wider text-[10px] text-slate-400">
              or sign in with email
            </span>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                College / University Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="your.email@university.edu"
                  className="w-full bg-white border border-slate-200 rounded-lg py-2.5 pl-9 pr-3 text-xs text-slate-900 focus:outline-none focus:border-coral-500 focus:ring-2 focus:ring-coral-500/10 transition-all"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-slate-700">
                  Password
                </label>
                <Link to="/forgot-password" className="text-xs text-coral-600 hover:underline font-medium">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••••••"
                  className="w-full bg-white border border-slate-200 rounded-lg py-2.5 pl-9 pr-10 text-xs text-slate-900 focus:outline-none focus:border-coral-500 focus:ring-2 focus:ring-coral-500/10 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-slate-700">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-slate-300 text-coral-600 focus:ring-coral-500"
                />
                <span>Remember me on this device</span>
              </label>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full mt-2 py-3 bg-coral-500 hover:bg-coral-600 text-white font-bold text-xs uppercase tracking-wider rounded-lg shadow-card hover:shadow-float transition-all"
              disabled={loading}
              icon={loading ? undefined : <ArrowRight className="w-4 h-4" />}
            >
              {loading ? 'Signing in...' : 'Sign in to Nexora'}
            </Button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-200 text-center text-xs text-slate-600">
            <span>Don't have an account yet? </span>
            <Link to="/signup" className="text-coral-600 font-semibold hover:underline">
              Create an account
            </Link>
          </div>
        </div>

        {/* Footer info */}
        <div className="text-xs text-slate-400 flex items-center justify-between pt-4">
          <span>Nexora © 2026</span>
          <span className="font-mono text-[11px] text-slate-400">Open to Students Worldwide</span>
        </div>
      </div>

      {/* Right Column: Seamless Blended Illustration (No separate rectangle box) */}
      <div className="hidden lg:flex lg:w-1/2 bg-white items-center justify-center p-8 sm:p-12 md:p-16 border-l border-slate-200/60 relative overflow-hidden">
        {/* Soft Ambient Radial Tint matching illustration tones */}
        <div className="absolute w-[480px] h-[480px] rounded-full bg-sky-50/60 blur-3xl pointer-events-none" />

        {/* User's Exact High-Res Illustration Seamlessly Blended */}
        <img
          src="/images/interview-illustration.png"
          alt="Placement Interview"
          className="w-full h-auto max-h-[82vh] max-w-xl object-contain mix-blend-multiply select-none relative z-10"
        />
      </div>
    </div>
  );
};
