'use client';
sa
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiService, User } from '../services/api';
import { LogOut, User as UserIcon } from 'lucide-react';

export default function Header() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  const checkAuth = () => {
    if (apiService.isAuthenticated()) {
      setUser(apiService.getCurrentUser());
    } else {
      setUser(null);
    }
  };

  useEffect(() => {
    checkAuth();
    
    
    window.addEventListener('auth-change', checkAuth);
    return () => {
      window.removeEventListener('auth-change', checkAuth);
    };
  }, []);

  const handleLogout = () => {
    apiService.logout();
    setUser(null);
    window.dispatchEvent(new Event('auth-change'));
    router.push('/login');
    router.refresh();
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-zinc-800/50 bg-[#09090b]/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-fuchsia-500 flex items-center justify-between p-1.5 shadow-[0_0_15px_rgba(139,92,246,0.5)] group-hover:scale-105 transition-transform">
            <svg className="w-full h-full text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent group-hover:text-white transition-colors">
            RepoMind <span className="text-violet-400">AI</span>
          </span>
        </Link>

        
        <nav className="flex items-center gap-4 sm:gap-6 text-sm font-medium text-zinc-400">
          {user && (
            <Link href="/" className="hover:text-zinc-100 transition-colors">
              Dashboard
            </Link>
          )}
          
          {user ? (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5 text-zinc-300">
                <UserIcon className="w-4 h-4 text-violet-400" />
                <span className="max-w-[120px] truncate hidden sm:inline-block">
                  {user.full_name || user.email}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 text-rose-400 hover:text-rose-300 transition-colors text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 px-3 py-1.5 rounded-lg border border-rose-500/20 cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                Logout
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-1.5 text-violet-400 hover:text-violet-300 transition-colors text-xs font-semibold bg-violet-500/10 hover:bg-violet-500/20 px-3 py-1.5 rounded-lg border border-violet-500/20"
            >
              Sign In
            </Link>
          )}
          
          <span className="text-zinc-800">|</span>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full border border-violet-500/30 bg-violet-500/10 text-violet-400 text-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
            <span className="hidden xs:inline">Multi-Agent</span> Active
          </div>
        </nav>
      </div>
    </header>
  );
}
