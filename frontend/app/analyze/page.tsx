'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiService, StatusResponse } from '../../services/api';
import { 
  Loader2, 
  Terminal, 
  CheckCircle2, 
  AlertCircle, 
  GitPullRequest, 
  ShieldAlert, 
  Code2, 
  Layers, 
  Tv, 
  Check
} from 'lucide-react';

function AnalyzePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const reviewId = searchParams.get('id');

  const [status, setStatus] = useState<'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'>('PENDING');
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  
  useEffect(() => {
    if (!reviewId) {
      setError('Missing review ID parameter.');
      return;
    }

    let intervalId: NodeJS.Timeout;

    const pollStatus = async () => {
      try {
        const data = await apiService.getReviewStatus(reviewId);
        setStatus(data.status);
        setLogs(data.logs || []);
        
        if (data.status === 'COMPLETED') {
          clearInterval(intervalId);
          
          setTimeout(() => {
            router.push(`/review/${reviewId}`);
          }, 1500);
        } else if (data.status === 'FAILED') {
          clearInterval(intervalId);
          setError(data.error || 'The multi-agent analysis failed. Please verify the repository URL.');
        }
      } catch (err: any) {
        console.error('Polling error:', err);
        
      }
    };

    
    pollStatus();
    
    
    intervalId = setInterval(pollStatus, 2000);

    return () => clearInterval(intervalId);
  }, [reviewId, router]);

  
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  
  const logStr = logs.join('\n').toLowerCase();
  
  const getAgentState = (agentName: string) => {
    if (status === 'COMPLETED') return 'completed';
    if (status === 'FAILED') return 'failed';

    switch (agentName) {
      case 'repo':
        if (logStr.includes('analyzing directory structure') || logStr.includes('found')) return 'completed';
        if (logStr.includes('starting repository analysis') || logStr.includes('cloning')) return 'active';
        return 'pending';
      case 'quality':
        if (logStr.includes('code quality agent complete')) return 'completed';
        if (logStr.includes('code quality agent:')) return 'active';
        return 'pending';
      case 'security':
        if (logStr.includes('security agent complete')) return 'completed';
        if (logStr.includes('security agent:')) return 'active';
        return 'pending';
      case 'arch':
        if (logStr.includes('architecture agent complete')) return 'completed';
        if (logStr.includes('architecture agent:')) return 'active';
        return 'pending';
      case 'devops':
        if (logStr.includes('devops agent complete')) return 'completed';
        if (logStr.includes('devops agent:')) return 'active';
        return 'pending';
      case 'report':
        if (logStr.includes('report agent complete') || logStr.includes('audit compiled')) return 'completed';
        if (logStr.includes('report agent:')) return 'active';
        return 'pending';
      default:
        return 'pending';
    }
  };

  const getAgentBadge = (agentState: 'pending' | 'active' | 'completed' | 'failed') => {
    switch (agentState) {
      case 'completed':
        return (
          <div className="w-6 h-6 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Check className="w-3.5 h-3.5" />
          </div>
        );
      case 'active':
        return (
          <div className="w-6 h-6 rounded-full bg-violet-500/15 border border-violet-500/40 flex items-center justify-center text-violet-400">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          </div>
        );
      case 'failed':
        return (
          <div className="w-6 h-6 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 font-bold text-xs">
            !
          </div>
        );
      default:
        return (
          <div className="w-6 h-6 rounded-full bg-zinc-950 border border-zinc-800 flex items-center justify-center text-zinc-600 text-xs font-semibold">
            -
          </div>
        );
    }
  };

  const agents = [
    { id: 'repo', name: 'Repository Agent', desc: 'Cloning & cataloging file structures', icon: GitPullRequest },
    { id: 'quality', name: 'Code Quality Agent', desc: 'Analyzing AST complexity & code smells', icon: Code2 },
    { id: 'security', name: 'Security Agent', desc: 'OWASP vulnerability & secrets audit', icon: ShieldAlert },
    { id: 'arch', name: 'Architecture Agent', desc: 'Mapping system components & routing', icon: Layers },
    { id: 'devops', name: 'DevOps Agent', desc: 'Auditing Docker & CI/CD deployment configurations', icon: Terminal },
    { id: 'report', name: 'Report Aggregator Agent', desc: 'Compiling scores and review roadmaps', icon: Tv },
  ];

  if (!reviewId) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center text-zinc-400">
        <AlertCircle className="w-12 h-12 text-rose-500 mb-2" />
        <p>Invalid Request. Review ID is required.</p>
        <button onClick={() => router.push('/')} className="mt-4 px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm hover:bg-zinc-800">
          Go back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto pt-4">
      
      <div className="text-center space-y-2">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center justify-center gap-3">
          {status !== 'COMPLETED' && status !== 'FAILED' && (
            <Loader2 className="w-6 h-6 animate-spin text-violet-500" />
          )}
          {status === 'COMPLETED' && <CheckCircle2 className="w-7 h-7 text-emerald-400" />}
          {status === 'FAILED' && <AlertCircle className="w-7 h-7 text-rose-500" />}
          Analyzing Repository
        </h1>
        <p className="text-zinc-400 text-sm max-w-md mx-auto">
          {status === 'COMPLETED' 
            ? 'Audit completed successfully! Preparing your dashboard...' 
            : status === 'FAILED' 
            ? 'Analysis terminated due to an error.' 
            : 'Collaborating agents are analyzing file tree metrics...'}
        </p>
      </div>

      
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        
        <div className="md:col-span-2 space-y-3">
          <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider pl-1">Agent Workflow Grid</div>
          <div className="space-y-2">
            {agents.map((agent) => {
              const aState = getAgentState(agent.id);
              const Icon = agent.icon;
              return (
                <div 
                  key={agent.id}
                  className={`glass-panel p-4 rounded-xl border flex items-center justify-between transition-all ${
                    aState === 'active' 
                      ? 'border-violet-500/40 bg-violet-500/5 shadow-[0_0_20px_rgba(139,92,246,0.05)]' 
                      : aState === 'completed'
                      ? 'border-emerald-500/10'
                      : 'border-zinc-900'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg bg-zinc-900 border ${
                      aState === 'active' 
                        ? 'border-violet-500/30 text-violet-400' 
                        : aState === 'completed'
                        ? 'border-emerald-500/20 text-emerald-400'
                        : 'border-zinc-800 text-zinc-500'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className={`text-xs font-semibold ${
                        aState === 'active' ? 'text-violet-400' : aState === 'completed' ? 'text-zinc-300' : 'text-zinc-500'
                      }`}>
                        {agent.name}
                      </div>
                      <div className="text-[10px] text-zinc-500 mt-0.5 max-w-[200px] leading-tight">
                        {agent.desc}
                      </div>
                    </div>
                  </div>
                  {getAgentBadge(aState)}
                </div>
              );
            })}
          </div>
        </div>

        
        <div className="md:col-span-3 flex flex-col space-y-3 h-full">
          <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider pl-1 flex items-center justify-between">
            <span>Agent Terminal Feed</span>
            <span className="text-[10px] text-zinc-500 font-mono">Job ID: {reviewId}</span>
          </div>

          <div className="flex-1 min-h-[350px] max-h-[480px] bg-zinc-950 border border-zinc-900 rounded-2xl p-4 font-mono text-xs overflow-y-auto space-y-2.5 flex flex-col shadow-2xl">
            
            <div className="flex items-center gap-1.5 pb-2 border-b border-zinc-900/50 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500/60" />
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500/60" />
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
              <span className="text-[10px] text-zinc-600 ml-2">repomind-audit-runner.sh</span>
            </div>

            
            <div className="flex-1 space-y-1.5 overflow-y-auto pr-1">
              {logs.map((log, index) => (
                <div key={index} className="text-zinc-400 leading-relaxed">
                  <span className="text-violet-400 select-none mr-2">&gt;</span>
                  {log}
                </div>
              ))}
              {status !== 'COMPLETED' && status !== 'FAILED' && (
                <div className="text-zinc-600 flex items-center gap-1.5 animate-pulse mt-2">
                  <span className="w-1.5 h-3 bg-zinc-600 inline-block animate-pulse" />
                  <span>Agent thread listening...</span>
                </div>
              )}
              <div ref={terminalEndRef} />
            </div>

            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-xs font-mono whitespace-pre-wrap leading-relaxed mt-auto">
                <span className="font-bold uppercase tracking-wider flex items-center gap-1.5 mb-1.5">
                  <AlertCircle className="w-4 h-4" /> Execution Fail:
                </span>
                {error}
              </div>
            )}
          </div>

          {status === 'FAILED' && (
            <button 
              onClick={() => router.push('/')}
              className="w-full py-3 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 font-semibold rounded-xl text-sm transition-colors cursor-pointer"
            >
              Return to Dashboard
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center p-12 text-center text-zinc-400">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500 mb-2" />
        <p>Loading analysis runner...</p>
      </div>
    }>
      <AnalyzePageContent />
    </Suspense>
  );
}
