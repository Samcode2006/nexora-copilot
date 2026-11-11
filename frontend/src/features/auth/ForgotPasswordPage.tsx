import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { GraduationCap, Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { Button } from '../../components/common/UIComponents';
import { supabase } from '../../lib/supabaseClient';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setError('');
    setLoading(true);
    try {
      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/login`,
      });
      if (resetError) {
        setError(resetError.message);
        return;
      }
      setSubmitted(true);
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
        <p className="text-xs text-charcoal-600">Password recovery</p>
      </div>

      <div className="w-full max-w-md bg-white border border-charcoal-200 rounded-lg shadow-card p-6 md:p-8">
        {!submitted ? (
          <>
            <h2 className="text-lg font-bold text-charcoal-900 mb-1">Reset your password</h2>
            <p className="text-xs text-charcoal-600 mb-6">
              Enter the email address registered with your college placement cell, and we will send you a recovery link.
            </p>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-charcoal-700 mb-1.5">
                  College Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-charcoal-600 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="student@college.edu"
                    className="w-full bg-white border border-charcoal-200 rounded-md py-2 pl-9 pr-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500 focus:ring-1 focus:ring-steel-500"
                  />
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                disabled={loading}
              >
                {loading ? 'Sending link...' : 'Send Recovery Link'}
              </Button>
            </form>
          </>
        ) : (
          <div className="text-center py-4">
            <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-700 mx-auto flex items-center justify-center mb-3">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-sm text-charcoal-900 mb-1">Recovery link sent</h3>
            <p className="text-xs text-charcoal-600 mb-6 leading-relaxed">
              We have sent password recovery instructions to <span className="font-semibold text-charcoal-800">{email}</span>. Please check your inbox and spam folder.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSubmitted(false)}
            >
              Resend to another email
            </Button>
          </div>
        )}

        <div className="mt-6 pt-5 border-t border-charcoal-100 text-center text-xs">
          <Link to="/login" className="inline-flex items-center gap-1.5 text-steel-600 hover:underline font-medium">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to sign in</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
