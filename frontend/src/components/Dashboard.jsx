import React, { useState, useEffect } from 'react';
import ApiService from '../utils/api';
import JobManager from './JobManager';
import ResumeUploader from './ResumeUploader';
import CandidateTable from './CandidateTable';
import CandidateDetails from './CandidateDetails';
import { LogOut, RefreshCw, Layers, Award, Target, Users, Search, AlertCircle, Compass, X } from 'lucide-react';

export default function Dashboard({ onLogout }) {
  const [activeJob, setActiveJob] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [allCandidates, setAllCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [recruiter, setRecruiter] = useState(null);
  const [error, setError] = useState('');

  const fetchAllCandidates = async () => {
    try {
      const data = await ApiService.getCandidates();
      setAllCandidates(data || []);
    } catch (err) {
      console.error("Failed to fetch all candidates:", err);
    }
  };

  const fetchProfile = async () => {
    try {
      const data = await ApiService.getMe();
      setRecruiter(data);
    } catch (err) {
      console.error("Failed to fetch profile:", err);
      onLogout();
    }
  };

  const handleDiscover = async () => {
    if (!activeJob) {
      setError("Please select or create a Job Description first.");
      return;
    }
    setLoading(true);
    setError('');
    setSelectedCandidate(null);
    try {
      const result = await ApiService.discoverCandidates(activeJob.id);
      setCandidates(result.candidates || []);
      fetchAllCandidates();
    } catch (err) {
      setError(err.message || "Candidate matching failed. Please ensure resumes are uploaded.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCandidate = async (candidateId) => {
    try {
      await ApiService.deleteCandidate(candidateId);
      // Remove from states dynamically
      setCandidates(prev => prev.filter(c => c.candidate_id !== candidateId && c.id !== candidateId));
      setAllCandidates(prev => prev.filter(c => c.id !== candidateId && c.candidate_id !== candidateId));
      if (selectedCandidate?.candidate_id === candidateId || selectedCandidate?.id === candidateId) {
        setSelectedCandidate(null);
      }
    } catch (err) {
      setError(err.message || 'Failed to delete candidate');
    }
  };

  const fetchHistory = async () => {
    if (!activeJob) return;
    setLoading(true);
    setError('');
    try {
      const data = await ApiService.getRankingHistory(activeJob.id);
      setCandidates(data || []);
    } catch (err) {
      console.error("Failed to fetch historical rankings:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
    fetchAllCandidates();
  }, []);

  useEffect(() => {
    if (activeJob) {
      fetchHistory();
    }
  }, [activeJob]);

  // Calculate statistics
  const stats = React.useMemo(() => {
    if (candidates.length === 0) {
      return { total: 0, topScore: 0, average: 0 };
    }
    const scores = candidates.map(c => c.overall_score);
    const total = candidates.length;
    const topScore = Math.max(...scores);
    const average = Math.round(scores.reduce((a, b) => a + b, 0) / total);
    return { total, topScore, average };
  }, [candidates]);

  return (
    <div className="min-h-screen flex flex-col relative text-left">
      {/* Header NavBar */}
      <header className="glass-panel border-b border-slate-800 sticky top-0 z-40 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-6 h-6 text-brand-500" />
          <h1 className="text-xl font-bold font-sans tracking-tight text-gradient">
            TalentGraph AI
          </h1>
          <span className="bg-slate-900 border border-slate-800 text-3xs text-slate-400 font-semibold px-2 py-0.5 rounded">
            MVP
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:block text-right">
            <p className="text-xs font-semibold text-slate-200">{recruiter?.full_name || 'Recruiter'}</p>
            <p className="text-3xs text-slate-400">{recruiter?.email}</p>
          </div>
          <button
            onClick={() => {
              ApiService.logout();
              onLogout();
            }}
            className="p-2 rounded-lg bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-red-400 hover:border-red-500/20 transition cursor-pointer active:scale-95"
            title="Log Out"
          >
            <LogOut className="w-4.5 h-4.5" />
          </button>
        </div>
      </header>

      {/* Main Workspace Body */}
      <main className="flex-1 flex flex-col lg:flex-row relative">
        {/* Left SideBar: JobManager & ResumeUploader */}
        <section className="w-full lg:w-80 shrink-0 border-r border-slate-800 bg-slate-950/40 p-6 space-y-6 lg:h-[calc(100vh-73px)] lg:overflow-y-auto">
          <JobManager activeJob={activeJob} onSelectJob={(job) => { if (activeJob?.id === job.id) { setActiveJob(null); setCandidates([]); } else { setActiveJob(job); setCandidates([]); } }} />
          <hr className="border-slate-800/80" />
          <ResumeUploader onUploadComplete={() => { fetchAllCandidates(); if (activeJob) fetchHistory(); }} />
        </section>

        {/* Center Panel: Candidates Dashboard */}
        <section className="flex-1 p-6 space-y-6 lg:h-[calc(100vh-73px)] lg:overflow-y-auto">
          
          {/* Top Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="glass-panel p-4 rounded-xl flex items-center justify-between gap-4">
              <div className="flex items-center gap-4 min-w-0 text-left">
                <div className="p-3 bg-brand-500/10 border border-brand-500/20 text-brand-400 rounded-lg shrink-0">
                  <Target className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <span className="text-3xs font-bold text-slate-400 uppercase tracking-wider block">Active Target Job</span>
                  <p className="text-sm font-bold text-slate-200 mt-0.5 truncate" title={activeJob?.title || 'No Job Selected'}>
                    {activeJob?.title || 'No Job Selected'}
                  </p>
                </div>
              </div>
              {activeJob && (
                <button
                  onClick={() => {
                    setActiveJob(null);
                    setCandidates([]);
                  }}
                  className="p-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-850 hover:text-red-400 text-slate-400 transition cursor-pointer active:scale-95 shrink-0"
                  title="Deselect Active Job"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            <div className="glass-panel p-4 rounded-xl flex items-center gap-4 text-left">
              <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg shrink-0">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <span className="text-3xs font-bold text-slate-400 uppercase tracking-wider block">Total Resumes Indexed</span>
                <p className="text-lg font-bold text-slate-200 mt-0.5">{allCandidates.length} candidates</p>
              </div>
            </div>

            <div className="glass-panel p-4 rounded-xl flex items-center gap-4 text-left">
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg shrink-0">
                <Award className="w-5 h-5" />
              </div>
              <div>
                <span className="text-3xs font-bold text-slate-400 uppercase tracking-wider block">Top Fit Match Score</span>
                <p className="text-lg font-bold text-slate-200 mt-0.5">{stats.topScore}% (Avg: {stats.average}%)</p>
              </div>
            </div>
          </div>

          {activeJob && allCandidates.length > 0 && candidates.length === 0 && (
            <div className="p-3.5 rounded-lg bg-blue-950/20 border border-blue-500/20 text-blue-300 text-xs flex items-center gap-2 animate-fade-in text-left">
              <Compass className="w-4 h-4 text-blue-400 animate-pulse shrink-0" />
              <span>
                You have {allCandidates.length} resume(s) uploaded. Click <strong>Match & Rank Resumes</strong> on the right to evaluate and rank candidates for this job description.
              </span>
            </div>
          )}

          {/* Action Row */}
          <div className="flex items-center justify-between border-b border-slate-900 pb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-200 font-sans">
                {activeJob ? "Ranked Match Discovery" : "All Indexed Resumes"}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {activeJob 
                  ? "AI semantic evaluation matching resumes against job specifications." 
                  : "Manage your database of uploaded resume files. Select a target job on the left to match & rank."}
              </p>
            </div>
            
            <button
              onClick={handleDiscover}
              disabled={loading || !activeJob}
              className="bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs px-4 py-2.5 rounded-lg transition duration-200 flex items-center gap-2 disabled:opacity-50 disabled:pointer-events-none shadow-lg shadow-brand-500/10 active:scale-95"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Reranking...
                </>
              ) : (
                <>
                  <Compass className="w-4 h-4" />
                  Match & Rank Resumes
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/20 text-red-200 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          )}

          {/* Candidate Discover Dashboard Table */}
          {loading ? (
            <div className="py-24 text-center space-y-4">
              <RefreshCw className="w-10 h-10 text-brand-500 animate-spin mx-auto" />
              <div className="space-y-1">
                <p className="text-sm font-bold text-slate-200">Executing Ranking Engine...</p>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Performing semantic search in ChromaDB, reducing bias, and computing professional growth scores.
                </p>
              </div>
            </div>
          ) : (
            <CandidateTable
              candidates={activeJob ? candidates : allCandidates}
              onSelectCandidate={(cand) => setSelectedCandidate(cand)}
              selectedCandidate={selectedCandidate}
              isRanked={Boolean(activeJob)}
              onDeleteCandidate={handleDeleteCandidate}
            />
          )}
        </section>

        {/* Right Drawer Panel: Candidate Details & Explainability */}
        {selectedCandidate && (
          <div className="fixed inset-y-0 right-0 z-50 w-full lg:static lg:z-auto lg:h-[calc(100vh-73px)] shrink-0">
            <div 
              className="fixed inset-0 bg-black/60 backdrop-blur-sm lg:hidden"
              onClick={() => setSelectedCandidate(null)}
            ></div>
            <CandidateDetails
              candidate={selectedCandidate}
              onClose={() => setSelectedCandidate(null)}
            />
          </div>
        )}
      </main>
    </div>
  );
}
