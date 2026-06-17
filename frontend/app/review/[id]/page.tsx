'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiService, Review, Finding } from '../../../services/api';
import { 
  ShieldAlert, 
  Code2, 
  Layers, 
  Terminal, 
  Download, 
  ExternalLink,
  ChevronRight,
  Sparkles,
  RefreshCw,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  FileText
} from 'lucide-react';

export default function ReviewDetailPage() {
  const router = useRouter();
  const params = useParams();
  const reviewId = params.id ? (params.id as string) : null;

  const [review, setReview] = useState<Review | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'quality' | 'security' | 'architecture' | 'devops' | 'report'>('overview');
  
  
  const mermaidRef = useRef<HTMLDivElement>(null);
  const [mermaidSvg, setMermaidSvg] = useState<string>('');

  useEffect(() => {
    if (!reviewId) return;
    fetchDetail();
  }, [reviewId]);

  const fetchDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      if (reviewId) {
        const data = await apiService.getReviewDetail(reviewId);
        setReview(data);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load review details.');
    } finally {
      setLoading(false);
    }
  };

  
  useEffect(() => {
    if (!review || !review.mermaid_diagram || activeTab !== 'architecture') return;

    
    const renderDiagram = async () => {
      try {
        
        if (typeof window !== 'undefined') {
          const w = window as any;
          if (!w.mermaid) {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
            script.async = true;
            script.onload = () => {
              initializeMermaid(w.mermaid);
            };
            document.body.appendChild(script);
          } else {
            initializeMermaid(w.mermaid);
          }
        }
      } catch (err) {
        console.error('Mermaid render error:', err);
      }
    };

    const initializeMermaid = async (m: any) => {
      try {
        m.initialize({
          startOnLoad: false,
          theme: 'dark',
          securityLevel: 'loose',
          fontFamily: 'var(--font-geist-sans)',
          suppressErrorRendering: true
        });
        
        const elementId = `mermaid-svg-${Date.now()}`;
        
        // Pre-validate diagram syntax first to avoid console errors/crashes
        let isValid = false;
        try {
          const parseResult = await m.parse(review.mermaid_diagram, { suppressErrors: true });
          isValid = parseResult === true || (parseResult && parseResult.retval === true);
        } catch (e) {
          isValid = false;
        }

        if (!isValid) {
          setMermaidSvg(
            `<div class="text-center p-6 border border-rose-500/20 bg-rose-500/5 rounded-xl space-y-2 max-w-md mx-auto">
              <p class="text-sm font-semibold text-rose-400">Failed to render architecture diagram</p>
              <p class="text-xs text-zinc-500">The generated diagram contains syntax/layout constraints that could not be parsed.</p>
            </div>`
          );
          return;
        }

        m.render(elementId, review.mermaid_diagram)
          .then((result: any) => {
            setMermaidSvg(result.svg);
          })
          .catch((err: any) => {
            console.warn('Mermaid render promise rejected:', err);
            
            setMermaidSvg(
              `<div class="text-center p-6 border border-rose-500/20 bg-rose-500/5 rounded-xl space-y-2 max-w-md mx-auto">
                <p class="text-sm font-semibold text-rose-400">Failed to render architecture diagram</p>
                <p class="text-xs text-zinc-500">The generated diagram contains syntax/layout constraints that could not be parsed.</p>
              </div>`
            );
            
            const errorElement = document.getElementById(`d${elementId}`);
            if (errorElement) {
              errorElement.remove();
            }
            
            const generalError = document.querySelector('body > svg[id^="mermaid-"]');
            if (generalError) {
              generalError.remove();
            }
          });
      } catch (e) {
        console.warn('Mermaid init error:', e);
      }
    };

    renderDiagram();
  }, [review, activeTab]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-zinc-400">
        <RefreshCw className="w-8 h-8 animate-spin text-violet-500 mb-2" />
        <p>Loading codebase report...</p>
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-zinc-400 text-center max-w-md mx-auto space-y-4">
        <XCircle className="w-12 h-12 text-rose-500" />
        <h2 className="text-lg font-bold text-white">Failed to Load Report</h2>
        <p className="text-sm">{error || 'Review details could not be found.'}</p>
        <button 
          onClick={() => router.push('/')}
          className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-300 hover:text-white"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'border-zinc-800 text-zinc-500';
    if (score >= 80) return 'border-emerald-500/30 text-emerald-400 bg-emerald-500/5';
    if (score >= 60) return 'border-amber-500/30 text-amber-400 bg-amber-500/5';
    return 'border-rose-500/30 text-rose-400 bg-rose-500/5';
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500 text-white uppercase">Critical</span>;
      case 'high':
        return <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/20 uppercase">High</span>;
      case 'medium':
        return <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/20 uppercase">Medium</span>;
      default:
        return <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-semibold bg-zinc-800 text-zinc-400 border border-zinc-800 uppercase">Low</span>;
    }
  };

  
  const renderMarkdownText = (md: string) => {
    const lines = md.split('\n');
    return lines.map((line, idx) => {
      if (line.startsWith('# ')) {
        return <h1 key={idx} className="text-2xl font-bold text-white mt-6 mb-3 border-b border-zinc-800 pb-2">{line.replace('# ', '')}</h1>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={idx} className="text-xl font-bold text-zinc-100 mt-5 mb-2.5">{line.replace('## ', '')}</h2>;
      }
      if (line.startsWith('### ')) {
        return <h3 key={idx} className="text-lg font-semibold text-zinc-200 mt-4 mb-2">{line.replace('### ', '')}</h3>;
      }
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return <li key={idx} className="text-zinc-400 ml-4 list-disc mb-1 leading-relaxed">{line.replace(/^[-*]\s+/, '')}</li>;
      }
      if (line.startsWith('|')) {
        
        if (line.includes('---')) return null; 
        const cells = line.split('|').map(c => c.trim()).filter((c, i, a) => i > 0 && i < a.length - 1);
        return (
          <div key={idx} className="grid grid-cols-3 gap-4 py-2 border-b border-zinc-900 text-sm font-mono text-zinc-400">
            {cells.map((cell, cidx) => (
              <span key={cidx} className={cidx === 0 ? "font-semibold text-zinc-300" : ""}>{cell}</span>
            ))}
          </div>
        );
      }
      if (line.trim() === '---') {
        return <hr key={idx} className="my-6 border-zinc-900" />;
      }
      if (!line.trim()) return <div key={idx} className="h-2" />;
      
      return <p key={idx} className="text-zinc-400 text-sm leading-relaxed mb-2.5">{line}</p>;
    });
  };

  const findings = review.findings || {};
  const codeFindings = findings.code_quality || [];
  const secFindings = findings.security || [];
  const devopsFindings = findings.devops || [];
  const archComponents = findings.architecture || {};
  const languages = findings.languages || {};
  const frameworks = findings.frameworks || [];

  
  const checks = [
    { name: 'Dockerfile Configuration', pass: !devopsFindings.some(f => f.type === 'Containerization Gap') },
    { name: 'CI/CD Pipeline Automation', pass: !devopsFindings.some(f => f.type === 'CI/CD Orchestration Gap') },
    { name: 'Container Run Security (Non-Root User)', pass: !devopsFindings.some(f => f.type === 'Container Security') },
  ];

  return (
    <div className="space-y-8">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <button
          onClick={() => router.push('/')}
          className="flex items-center gap-1.5 text-zinc-400 hover:text-white transition-colors text-sm cursor-pointer font-medium"
        >
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </button>

        <a
          href={apiService.getReportDownloadUrl(review.id)}
          download
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white text-sm font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all cursor-pointer"
        >
          <Download className="w-4 h-4" /> Download Report
        </a>
      </div>

      
      <div className="glass-panel p-6 rounded-2xl border border-zinc-900 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="text-[10px] font-bold text-violet-400 uppercase tracking-wider flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5" /> Multi-Agent Audit Complete
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            {review.repository.owner}/{review.repository.name}
          </h1>
          <div className="text-zinc-500 text-xs flex items-center gap-3">
            <span>Branch: <span className="font-mono text-zinc-400">{review.repository.default_branch}</span></span>
            <span>•</span>
            <a 
              href={review.repository.url} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-zinc-400 hover:text-white flex items-center gap-1 inline-flex transition-colors"
            >
              Source Repo <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Overall Health Score</div>
            <div className="text-xs text-zinc-400 font-medium mt-0.5">
              {review.overall_score && review.overall_score >= 80 ? 'Healthy Posture' : review.overall_score && review.overall_score >= 60 ? 'Needs Upgrades' : 'Risky State'}
            </div>
          </div>
          <div className="w-16 h-16 rounded-full bg-zinc-950 border-4 border-violet-500 flex items-center justify-center font-bold text-xl text-white shadow-[0_0_20px_rgba(139,92,246,0.3)]">
            {review.overall_score}
          </div>
        </div>
      </div>

      
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        
        <div className={`glass-panel p-4 rounded-xl border flex flex-col justify-between h-28 ${getScoreColor(review.security_score)}`}>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Security</span>
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold">{review.security_score}/100</div>
            <div className="text-[10px] mt-0.5 text-zinc-500">
              {review.security_score && review.security_score >= 85 ? 'Secure configs' : review.security_score && review.security_score >= 60 ? 'Weak points' : 'Critical faults'}
            </div>
          </div>
        </div>

        
        <div className={`glass-panel p-4 rounded-xl border flex flex-col justify-between h-28 ${getScoreColor(review.code_quality_score)}`}>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Code Quality</span>
            <Code2 className="w-4 h-4" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold">{review.code_quality_score}/100</div>
            <div className="text-[10px] mt-0.5 text-zinc-500">
              {review.code_quality_score && review.code_quality_score >= 80 ? 'Optimal code' : review.code_quality_score && review.code_quality_score >= 60 ? 'Smell warnings' : 'Refactoring needed'}
            </div>
          </div>
        </div>

        
        <div className={`glass-panel p-4 rounded-xl border flex flex-col justify-between h-28 ${getScoreColor(review.architecture_score)}`}>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Architecture</span>
            <Layers className="w-4 h-4" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold">{review.architecture_score}/100</div>
            <div className="text-[10px] mt-0.5 text-zinc-500">
              {review.architecture_score && review.architecture_score >= 80 ? 'Modular design' : review.architecture_score && review.architecture_score >= 60 ? 'Tight coupling' : 'Unstructured grid'}
            </div>
          </div>
        </div>

        
        <div className={`glass-panel p-4 rounded-xl border flex flex-col justify-between h-28 ${getScoreColor(review.devops_score)}`}>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">DevOps</span>
            <Terminal className="w-4 h-4" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold">{review.devops_score}/100</div>
            <div className="text-[10px] mt-0.5 text-zinc-500">
              {review.devops_score && review.devops_score >= 80 ? 'Automated run' : review.devops_score && review.devops_score >= 60 ? 'Partial setup' : 'No automation'}
            </div>
          </div>
        </div>
      </div>

      
      <div className="flex border-b border-zinc-900 overflow-x-auto gap-4 font-medium text-sm text-zinc-500">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'quality', label: `Code Quality (${codeFindings.length})` },
          { id: 'security', label: `Security (${secFindings.length})` },
          { id: 'architecture', label: 'Architecture Map' },
          { id: 'devops', label: `DevOps Audit (${devopsFindings.length})` },
          { id: 'report', label: 'Full Report' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`py-3 px-1 border-b-2 font-semibold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === tab.id 
                ? 'border-violet-500 text-white' 
                : 'border-transparent hover:text-zinc-300 hover:border-zinc-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      
      <div className="min-h-[300px]">
        
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {review.findings && review.findings.summary && (
              <div className="md:col-span-3 glass-panel p-6 rounded-2xl border border-zinc-900 space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-violet-400" /> AI Project Summary
                </h3>
                <p className="text-zinc-300 text-sm leading-relaxed font-sans">
                  {review.findings.summary}
                </p>
              </div>
            )}
            
            <div className="md:col-span-2 space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-zinc-900 space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Language Composition</h3>
                
                
                <div className="w-full h-4 rounded-full bg-zinc-900 overflow-hidden flex">
                  {Object.entries(languages).map(([name, data], idx) => {
                    const colors = ['bg-violet-500', 'bg-indigo-500', 'bg-fuchsia-500', 'bg-sky-500', 'bg-emerald-500', 'bg-amber-500'];
                    const color = colors[idx % colors.length];
                    return (
                      <div 
                        key={name}
                        style={{ width: `${data.percentage}%` }}
                        className={`${color} h-full`}
                        title={`${name}: ${data.percentage}%`}
                      />
                    );
                  })}
                </div>

                
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2">
                  {Object.entries(languages).map(([name, data], idx) => {
                    const colors = ['bg-violet-500', 'bg-indigo-500', 'bg-fuchsia-500', 'bg-sky-500', 'bg-emerald-500', 'bg-amber-500'];
                    const color = colors[idx % colors.length];
                    return (
                      <div key={name} className="flex items-center gap-2 text-sm">
                        <span className={`w-3 h-3 rounded-sm ${color}`} />
                        <div>
                          <span className="font-semibold text-zinc-300">{name}</span>
                          <span className="text-xs text-zinc-500 ml-1.5">{data.percentage}%</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              
              <div className="glass-panel p-6 rounded-2xl border border-zinc-900 space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Source Tree Mapped</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto font-mono text-xs text-zinc-400">
                  {review.findings && review.findings.logs && (
                    <div className="text-[10px] text-zinc-500 border-b border-zinc-900 pb-2 mb-2">
                      Total scanned files: {review.findings.logs.length > 5 ? 'Cataloged in indexing model' : ''}
                    </div>
                  )}
                  {review.findings && review.findings.logs ? (
                    
                    review.findings.logs.slice(2, 12).map((logLine, idx) => {
                      if (logLine.includes('Cloned') || logLine.includes('Found')) return null;
                      return (
                        <div key={idx} className="flex items-center gap-2">
                          <ChevronRight className="w-3.5 h-3.5 text-zinc-600" />
                          <span className="truncate">{logLine.replace('Found ', '').replace('files', 'files indexed')}</span>
                        </div>
                      );
                    })
                  ) : (
                    <div>Source cataloged successfully.</div>
                  )}
                </div>
              </div>
            </div>

            
            <div className="space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-zinc-900 space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Detected Core Tech Stack</h3>
                <div className="flex flex-wrap gap-2">
                  {frameworks.length === 0 ? (
                    <span className="text-zinc-500 text-xs">No framework indicator files found.</span>
                  ) : (
                    frameworks.map((fw) => (
                      <span 
                        key={fw} 
                        className="px-3 py-1.5 bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-lg text-xs font-semibold hover:border-violet-500 transition-colors"
                      >
                        {fw}
                      </span>
                    ))
                  )}
                </div>
              </div>

              <div className="glass-panel p-6 rounded-2xl border border-zinc-900 space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Audit Metadata</h3>
                <div className="space-y-2.5 text-xs text-zinc-400">
                  <div className="flex justify-between">
                    <span>Scanner Version</span>
                    <span className="font-mono text-zinc-300">v1.2.0-mcp</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Audit Model</span>
                    <span className="font-mono text-zinc-300">Gemini 1.5 Flash</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Cloning Type</span>
                    <span className="font-mono text-zinc-300">Shallow (Depth 1)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        
        {activeTab === 'quality' && (
          <div className="space-y-4">
            {codeFindings.length === 0 ? (
              <div className="glass-panel p-12 text-center rounded-2xl text-zinc-500 border border-zinc-900">
                No major code smells or quality violations detected. Coding patterns follow architectural standards.
              </div>
            ) : (
              codeFindings.map((fnd, idx) => (
                <div key={idx} className="glass-panel p-5 rounded-2xl border border-zinc-900 hover:border-zinc-800 transition-all space-y-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        {getSeverityBadge(fnd.severity)}
                        <span className="font-bold text-white text-sm">{fnd.type || 'Code Smells'}</span>
                      </div>
                      <div className="font-mono text-zinc-500 text-xs mt-1">
                        File: <span className="text-zinc-300">{fnd.file_path}</span> {fnd.line_number > 0 && `(Line ${fnd.line_number})`}
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-zinc-400 leading-relaxed">{fnd.description}</p>
                  {fnd.suggestion && (
                    <div className="p-3 bg-violet-500/5 border border-violet-500/10 rounded-lg text-xs text-violet-300">
                      <span className="font-bold block mb-1">Refactoring Guidance:</span>
                      {fnd.suggestion}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        
        {activeTab === 'security' && (
          <div className="space-y-4">
            {secFindings.length === 0 ? (
              <div className="glass-panel p-12 text-center rounded-2xl text-zinc-500 border border-zinc-900">
                No exposed API credentials, SQL injection routes, or severe security failures detected in local files.
              </div>
            ) : (
              secFindings.map((fnd, idx) => (
                <div 
                  key={idx} 
                  className={`glass-panel p-5 rounded-2xl border transition-all space-y-3 ${
                    fnd.severity.toLowerCase() === 'critical' || fnd.severity.toLowerCase() === 'high' 
                      ? 'border-rose-500/20 bg-rose-500/[0.01]' 
                      : 'border-zinc-900'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        {getSeverityBadge(fnd.severity)}
                        <span className="font-bold text-white text-sm">{fnd.vulnerability_type || 'Security Flag'}</span>
                      </div>
                      <div className="font-mono text-zinc-500 text-xs mt-1">
                        File: <span className="text-zinc-300">{fnd.file_path}</span> {fnd.line_number > 0 && `(Line ${fnd.line_number})`}
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-zinc-400 leading-relaxed">{fnd.description}</p>
                  
                  {fnd.code_snippet && (
                    <div className="p-3 bg-zinc-950 border border-zinc-900 rounded-lg overflow-x-auto">
                      <pre className="font-mono text-xs text-rose-400/90 whitespace-pre">{fnd.code_snippet}</pre>
                    </div>
                  )}
                  
                  {fnd.recommendation && (
                    <div className="p-3 bg-emerald-500/5 border border-emerald-500/10 rounded-lg text-xs text-emerald-300">
                      <span className="font-bold block mb-1">Mitigation Recommendation:</span>
                      {fnd.recommendation}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        
        {activeTab === 'architecture' && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            
            <div className="md:col-span-3 glass-panel p-6 rounded-2xl border border-zinc-900 flex flex-col space-y-4 min-h-[400px]">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">System Design Visualization</h3>
                <span className="text-[10px] text-zinc-500 uppercase font-mono">Rendered client-side</span>
              </div>

              {review.mermaid_diagram ? (
                <div className="flex-1 flex items-center justify-center p-4 bg-zinc-950/50 rounded-xl overflow-x-auto border border-zinc-900">
                  {mermaidSvg ? (
                    <div 
                      ref={mermaidRef} 
                      className="w-full text-center scale-95 md:scale-100" 
                      dangerouslySetInnerHTML={{ __html: mermaidSvg }} 
                    />
                  ) : (
                    <div className="text-xs text-zinc-500 animate-pulse flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-violet-500" />
                      Parsing system structure graph...
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-zinc-500 text-xs">
                  No structural diagram available.
                </div>
              )}
            </div>

            
            <div className="space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-zinc-900 space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Model Components</h3>
                
                <div className="space-y-4 text-xs">
                  <div>
                    <span className="text-zinc-500 block uppercase font-semibold mb-1">Routers & Routes</span>
                    <span className="text-zinc-300 font-mono block">
                      {archComponents.routes && archComponents.routes.length > 0 
                        ? archComponents.routes.map(r => r.split('/').pop()).join(', ') 
                        : 'None identified'}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-500 block uppercase font-semibold mb-1">Controllers / Handlers</span>
                    <span className="text-zinc-300 font-mono block">
                      {archComponents.controllers && archComponents.controllers.length > 0 
                        ? archComponents.controllers.map(c => c.split('/').pop()).join(', ') 
                        : 'None identified'}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-500 block uppercase font-semibold mb-1">Database Layer / Schemes</span>
                    <span className="text-zinc-300 font-mono block">
                      {archComponents.databases && archComponents.databases.length > 0 
                        ? archComponents.databases.map(d => d.split('/').pop()).join(', ') 
                        : 'None identified'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        
        {activeTab === 'devops' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <div className="space-y-4 md:col-span-1">
              <div className="glass-panel p-6 rounded-2xl border border-zinc-900 space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">DevOps Compliance</h3>
                <div className="space-y-3.5">
                  {checks.map((chk, idx) => (
                    <div key={idx} className="flex items-center gap-3 text-sm">
                      {chk.pass ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                      ) : (
                        <XCircle className="w-5 h-5 text-rose-500 shrink-0" />
                      )}
                      <span className={chk.pass ? 'text-zinc-300' : 'text-zinc-500 line-through'}>{chk.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            
            <div className="md:col-span-2 space-y-4">
              {devopsFindings.length === 0 ? (
                <div className="glass-panel p-12 text-center rounded-2xl text-zinc-500 border border-zinc-900">
                  Full Docker containerization and automated CI testing structures detected in workspace. DevOps posture compliant.
                </div>
              ) : (
                devopsFindings.map((fnd, idx) => (
                  <div key={idx} className="glass-panel p-5 rounded-2xl border border-zinc-900 hover:border-zinc-800 transition-all space-y-3">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          {getSeverityBadge(fnd.severity)}
                          <span className="font-bold text-white text-sm">{fnd.type || 'DevOps Recommendation'}</span>
                        </div>
                        <div className="font-mono text-zinc-500 text-xs mt-1">
                          Target File: <span className="text-zinc-300">{fnd.file_path}</span>
                        </div>
                      </div>
                    </div>
                    <p className="text-sm text-zinc-400 leading-relaxed">{fnd.description}</p>
                    {fnd.recommendation ? (
                      <div className="p-3 bg-violet-500/5 border border-violet-500/10 rounded-lg text-xs text-violet-300">
                        <span className="font-bold block mb-1">Upgrade Guidance:</span>
                        {fnd.recommendation}
                      </div>
                    ) : null}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        
        {activeTab === 'report' && (
          <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-zinc-900 shadow-2xl space-y-4 bg-zinc-950/30">
            <div className="flex items-center gap-2 border-b border-zinc-900 pb-3 mb-4">
              <FileText className="w-5 h-5 text-violet-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Markdown Audit Document</h3>
            </div>
            
            {review.report ? (
              <div className="prose prose-invert max-w-none text-zinc-300 font-sans">
                {renderMarkdownText(review.report.content_md)}
              </div>
            ) : (
              <div className="text-zinc-500 text-sm py-12 text-center">
                Report document could not be compiled.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
