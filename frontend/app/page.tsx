'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiService, ReviewSummary } from '../services/api';
import {
  GitBranch,
  ShieldAlert,
  Code2,
  Layers,
  Terminal,
  Search,
  ArrowRight,
  RefreshCw,
  FolderLock
} from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const [repoUrl, setRepoUrl] = useState('');
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reviews, setReviews] = useState<ReviewSummary[]>([]);
  const [fetchingHistory, setFetchingHistory] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);


  useEffect(() => {
    if (!apiService.isAuthenticated()) {
      router.push('/login');
    } else {
      setIsAuthenticated(true);
      fetchHistory();
    }
  }, [router]);

  const fetchHistory = async () => {
    setFetchingHistory(true);
    try {
      const data = await apiService.getReviews();
      setReviews(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setFetchingHistory(false);
    }
  };

  const handleAuditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl) return;

    setLoading(true);
    setError(null);

    try {
      const result = await apiService.analyzeRepository(repoUrl, token || undefined);

      router.push(`/analyze?id=${result.review_id}`);
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Please check the URL and try again.');
      setLoading(false);
    }
  };


  const totalAudits = reviews.length;
  const completedReviews = reviews.filter(r => r.status === 'COMPLETED');
  const avgScore = completedReviews.length > 0
    ? Math.round(completedReviews.reduce((sum, r) => sum + (r.overall_score || 0), 0) / completedReviews.length)
    : 0;

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-zinc-500 bg-zinc-900/50 border-zinc-800';
    if (score >= 80) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (score >= 60) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Completed</span>;
      case 'RUNNING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-violet-500/10 text-violet-400 border border-violet-500/20">
            <RefreshCw className="w-3 h-3 animate-spin" /> Analyzing
          </span>
        );
      case 'FAILED':
        return <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold">Failed</span>;
      default:
        return <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-zinc-500/10 text-zinc-400 border border-zinc-800">Pending</span>;
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-zinc-500 text-sm">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-violet-500" />
        Checking session...
      </div>
    );
  }

  return (
    <div className="space-y-12">

      <div className="text-center max-w-3xl mx-auto space-y-4 pt-4">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
          AI-Powered Repository Audits
        </h1>
        <p className="text-zinc-400 text-lg sm:text-xl font-light">
          Transform code reviews with collaborative AI agents that detect vulnerabilities, analyze code quality, assess software architecture, and optimize DevOps workflows.
        </p>
      </div>


      <div className="max-w-3xl mx-auto">
        <div className="glass-panel p-6 sm:p-8 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.4)] border border-zinc-800/80 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-violet-600 via-fuchsia-500 to-indigo-600 opacity-60" />

          <form onSubmit={handleAuditSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block">GitHub Repository URL</label>
              <div className="relative flex items-center">
                <Search className="absolute left-4 w-5 h-5 text-zinc-500" />
                <input
                  type="url"
                  placeholder="https://github.com/owner/repository"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  required
                  className="w-full pl-12 pr-4 py-3.5 bg-zinc-950/80 border border-zinc-800 rounded-xl text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50 transition-all font-sans text-sm"
                />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block">
                  GitHub Personal Access Token (PAT)
                </label>
                <span className="text-[10px] text-zinc-500">Only required for private repositories</span>
              </div>
              <div className="relative flex items-center">
                <FolderLock className="absolute left-4 w-5 h-5 text-zinc-500" />
                <input
                  type="password"
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxx"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  className="w-full pl-12 pr-4 py-3.5 bg-zinc-950/80 border border-zinc-800 rounded-xl text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50 transition-all font-sans text-sm"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-xs font-medium">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !repoUrl}
              className="w-full py-4 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white font-medium rounded-xl flex items-center justify-center gap-2 shadow-[0_0_30px_rgba(139,92,246,0.3)] hover:shadow-[0_0_40px_rgba(139,92,246,0.5)] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  Initializing Review Agents...
                </>
              ) : (
                <>
                  Analyze Codebase
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>


      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-5xl mx-auto">

        <div className="glass-panel p-6 rounded-2xl border border-zinc-900 shadow-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-violet-400 shadow-md">
            <GitBranch className="w-6 h-6" />
          </div>
          <div>
            <div className="text-zinc-500 text-xs uppercase font-semibold tracking-wider">Repositories Audited</div>
            <div className="text-2xl font-bold text-white mt-0.5">{totalAudits}</div>
          </div>
        </div>


        <div className="glass-panel p-6 rounded-2xl border border-zinc-900 shadow-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-emerald-400 shadow-md">
            <Code2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-zinc-500 text-xs uppercase font-semibold tracking-wider">Average Health Score</div>
            <div className="text-2xl font-bold text-white mt-0.5">{avgScore > 0 ? `${avgScore}/100` : 'N/A'}</div>
          </div>
        </div>


        <div className="glass-panel p-6 rounded-2xl border border-zinc-900 shadow-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-fuchsia-400 shadow-md">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="text-zinc-500 text-xs uppercase font-semibold tracking-wider">Agent Collaborations</div>
            <div className="text-2xl font-bold text-white mt-0.5">{totalAudits * 6} node executions</div>
          </div>
        </div>
      </div>


      <div className="max-w-5xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Terminal className="w-5 h-5 text-violet-400" />
            Audit Review History
          </h2>
          <button
            onClick={fetchHistory}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-white rounded-lg text-xs transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>

        <div className="glass-panel rounded-2xl overflow-hidden border border-zinc-900 shadow-2xl">
          {fetchingHistory ? (
            <div className="p-12 text-center text-zinc-500 text-sm">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-violet-500" />
              Loading history...
            </div>
          ) : reviews.length === 0 ? (
            <div className="p-12 text-center text-zinc-500 text-sm">
              No repositories analyzed yet. Submit a URL above to start!
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-zinc-800/80 bg-zinc-950/40 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    <th className="px-6 py-4">Repository</th>
                    <th className="px-6 py-4">Analyzed On</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-center">Score</th>
                    <th className="px-6 py-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900 text-sm">
                  {reviews.map((rev) => (
                    <tr key={rev.id} className="hover:bg-zinc-900/30 transition-colors">
                      <td className="px-6 py-4 font-medium text-white">
                        <div className="font-semibold text-zinc-200">
                          {rev.repository.owner}/{rev.repository.name}
                        </div>
                        <div className="text-xs text-zinc-500 truncate max-w-xs mt-0.5">
                          {rev.repository.url}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-zinc-400">
                        {new Date(rev.created_at).toLocaleDateString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td className="px-6 py-4">
                        {getStatusBadge(rev.status)}
                      </td>
                      <td className="px-6 py-4 text-center">
                        {rev.status === 'COMPLETED' ? (
                          <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full font-bold border text-xs ${getScoreColor(rev.overall_score)}`}>
                            {rev.overall_score}
                          </span>
                        ) : rev.status === 'FAILED' ? (
                          <span className="text-zinc-600 font-medium text-xs">Error</span>
                        ) : (
                          <span className="text-zinc-500 text-xs animate-pulse">Running</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => {
                            if (rev.status === 'RUNNING' || rev.status === 'PENDING') {
                              router.push(`/analyze?id=${rev.id}`);
                            } else {
                              router.push(`/review/${rev.id}`);
                            }
                          }}
                          className="px-3.5 py-1.5 bg-zinc-900 hover:bg-violet-600 hover:text-white border border-zinc-800 hover:border-violet-500 rounded-lg text-xs text-zinc-300 font-medium transition-all cursor-pointer"
                        >
                          View Report
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
