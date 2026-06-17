'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiService } from '../../services/api';
import {
  Lock,
  Mail,
  User as UserIcon,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  Loader2,
  Eye,
  EyeOff
} from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();

  
  const [mode, setMode] = useState<'login' | 'signup'>('login');

  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');

  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  
  useEffect(() => {
    if (apiService.isAuthenticated()) {
      router.push('/');
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    if (mode === 'signup' && password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (mode === 'login') {
        await apiService.login(email, password);
      } else {
        await apiService.signup(email, password, fullName || undefined);
      }

      
      window.dispatchEvent(new Event('auth-change'));
      router.push('/');
      router.refresh();
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center py-10 relative">
      
      <div className="ambient-glow top-[10%] left-[25%] bg-violet-600/10" />
      <div className="ambient-glow bottom-[10%] right-[25%] bg-fuchsia-600/10" />

      <div className="w-full max-w-md">
        
        <div className="text-center mb-8 space-y-2">
          <div className="inline-flex w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-fuchsia-500 items-center justify-center p-2 shadow-[0_0_20px_rgba(139,92,246,0.4)]">
            <svg className="w-full h-full text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mt-3">
            RepoMind <span className="text-violet-400">AI</span>
          </h1>
          <p className="text-zinc-500 text-xs tracking-wider uppercase font-semibold">
            Multi-Agent Automated Repository Audits
          </p>
        </div>

        
        <div className="glass-panel p-8 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-zinc-800/80 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-violet-600 via-fuchsia-500 to-indigo-600 opacity-60" />

          
          <div className="grid grid-cols-2 p-1 bg-zinc-950/80 border border-zinc-900 rounded-xl mb-6 text-sm">
            <button
              onClick={() => {
                setMode('login');
                setError(null);
                setShowPassword(false);
              }}
              className={`py-2 px-3 rounded-lg font-medium transition-all ${mode === 'login'
                ? 'bg-zinc-900 text-white shadow'
                : 'text-zinc-500 hover:text-zinc-300'
                }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setMode('signup');
                setError(null);
                setShowPassword(false);
              }}
              className={`py-2 px-3 rounded-lg font-medium transition-all ${mode === 'signup'
                ? 'bg-zinc-900 text-white shadow'
                : 'text-zinc-500 hover:text-zinc-300'
                }`}
            >
              Register
            </button>
          </div>

          
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'signup' && (
              <div className="space-y-1">
                <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block">Full Name</label>
                <div className="relative flex items-center">
                  <UserIcon className="absolute left-4 w-4 h-4 text-zinc-500" />
                  <input
                    type="text"
                    placeholder="Enter you full name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 bg-zinc-950/80 border border-zinc-800 rounded-xl text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50 transition-all font-sans text-sm"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block">Email Address</label>
              <div className="relative flex items-center">
                <Mail className="absolute left-4 w-4 h-4 text-zinc-500" />
                <input
                  type="email"
                  required
                  placeholder="Enter your email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-zinc-950/80 border border-zinc-800 rounded-xl text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50 transition-all font-sans text-sm"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block">Password</label>
              <div className="relative flex items-center">
                <Lock className="absolute left-4 w-4 h-4 text-zinc-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-12 py-3 bg-zinc-950/80 border border-zinc-800 rounded-xl text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50 transition-all font-sans text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 text-zinc-500 hover:text-zinc-300 focus:outline-none cursor-pointer"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-xs font-medium flex items-start gap-2">
                <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white font-semibold rounded-xl flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:shadow-[0_0_30px_rgba(139,92,246,0.5)] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {mode === 'login' ? 'Logging in...' : 'Registering...'}
                </>
              ) : (
                <>
                  {mode === 'login' ? 'Sign In' : 'Create Account'}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          
          <div className="mt-6 text-center text-[10px] text-zinc-500">
            <Sparkles className="w-3.5 h-3.5 inline mr-1 text-violet-400" />
            Secured using JWT hashing.
          </div>
        </div>
      </div>
    </div>
  );
}
