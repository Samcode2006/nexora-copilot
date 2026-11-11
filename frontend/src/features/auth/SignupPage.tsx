import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { GraduationCap, Lock, Mail, User, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Button } from '../../components/common/UIComponents';
import { useApp } from '../../context/appContextDef';
import { useAuth } from '../../auth/AuthContext';

export const SignupPage: React.FC = () => {
  const navigate = useNavigate();
  const { updateProfile } = useApp();
  const { signUp } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [error, setError] = useState('');
  const [confirmationMessage, setConfirmationMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setConfirmationMessage('');

    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (!agreeTerms) {
      setError('Please agree to the Terms of Service & Placement Integrity Policy.');
      return;
    }

    setLoading(true);
    try {
      const cleanEmail = email.trim();
      const { error: signUpError, needsEmailConfirmation } = await signUp(cleanEmail, password);
      if (signUpError) {
        setError(signUpError);
        return;
      }
      if (fullName || cleanEmail) {
        updateProfile({
          ...(fullName ? { fullName: fullName.trim() } : {}),
          ...(cleanEmail ? { email: cleanEmail } : {}),
        });
      }
      if (needsEmailConfirmation) {
        setConfirmationMessage('Check your email to confirm your account before signing in.');
        return;
      }
      navigate('/onboarding/profile', { replace: true });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F6F4] flex flex-col justify-center items-center p-4">
      <div className="mb-8 text-center">
        <Link to="/" className="inline-flex items-center gap-2 mb-2">
          <div className="w-9 h-9 rounded bg-[#263747] text-white flex items-center justify-center font-bold shadow-xs">
            <GraduationCap className="w-5 h-5" />
          </div>
          <span className="font-bold text-xl tracking-tight text-[#263747]">NEXORA</span>
        </Link>
        <p className="text-xs text-charcoal-600">Start your organized placement journey</p>
      </div>

      <div className="w-full max-w-md bg-white border border-charcoal-200 rounded-lg shadow-card p-6 md:p-8">
        <h2 className="text-lg font-bold text-charcoal-900 mb-1">Create student account</h2>
        <p className="text-xs text-charcoal-600 mb-6">
          Set up your placement profile, discover suitable roles, and manage your applications.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700">
            {error}
          </div>
        )}

        {confirmationMessage && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800 flex items-start gap-2" role="status">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>{confirmationMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-xs font-semibold text-charcoal-700 mb-1">
              Full Legal Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-charcoal-600 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                placeholder="e.g. Aarav Sharma"
                className="w-full bg-white border border-charcoal-200 rounded-md py-2 pl-9 pr-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500 focus:ring-1 focus:ring-steel-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-charcoal-700 mb-1">
              College / University Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-charcoal-600 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="student@university.edu or personal email"
                className="w-full bg-white border border-charcoal-200 rounded-md py-2 pl-9 pr-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500 focus:ring-1 focus:ring-steel-500"
              />
            </div>
            <p className="text-[11px] text-charcoal-500 mt-1">
              Open to students from any college, university, or institute.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-charcoal-700 mb-1">
              Create Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-charcoal-600 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Minimum 8 characters"
                className="w-full bg-white border border-charcoal-200 rounded-md py-2 pl-9 pr-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500 focus:ring-1 focus:ring-steel-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-charcoal-700 mb-1">
              Confirm Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-charcoal-600 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="Re-enter password"
                className="w-full bg-white border border-charcoal-200 rounded-md py-2 pl-9 pr-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500 focus:ring-1 focus:ring-steel-500"
              />
            </div>
          </div>

          <div className="pt-1">
            <label className="flex items-start gap-2 cursor-pointer text-xs text-charcoal-700">
              <input
                type="checkbox"
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                className="mt-0.5 rounded border-charcoal-300 text-navy-800 focus:ring-steel-500"
              />
              <span>
                I agree to the <span className="font-semibold text-steel-600">Placement Integrity Policy</span> and understand that Nexora will never submit applications without my explicit approval.
              </span>
            </label>
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full mt-3"
            disabled={loading}
            icon={loading ? undefined : <ArrowRight className="w-4 h-4" />}
          >
            {loading ? 'Creating account...' : 'Continue to Onboarding'}
          </Button>
        </form>

        <div className="mt-6 pt-5 border-t border-charcoal-100 text-center text-xs text-charcoal-600">
          <span>Already have an account? </span>
          <Link to="/login" className="text-steel-600 font-semibold hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
};
