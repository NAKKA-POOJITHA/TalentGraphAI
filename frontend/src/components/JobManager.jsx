import React, { useState, useEffect } from 'react';
import ApiService from '../utils/api';
import { Briefcase, Plus, FileText, CheckCircle2, ChevronRight, Loader2, Award, X } from 'lucide-react';

export default function JobManager({ activeJob, onSelectJob }) {
  const [jobs, setJobs] = useState([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [error, setError] = useState('');

  const fetchJobs = async () => {
    setFetching(true);
    try {
      const data = await ApiService.getJobs();
      setJobs(data);
      if (data.length > 0 && !activeJob) {
        onSelectJob(data[0]); // default select first job
      }
    } catch (err) {
      console.error("Error fetching jobs:", err);
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleDeleteJob = async (e, jobId) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this job description? This will also delete all ranking history associated with it.")) {
      return;
    }
    try {
      await ApiService.deleteJob(jobId);
      const updatedJobs = jobs.filter(j => j.id !== jobId);
      setJobs(updatedJobs);
      if (activeJob?.id === jobId) {
        onSelectJob(null);
      }
    } catch (err) {
      setError(err.message || 'Failed to delete job');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;
    
    setLoading(true);
    setError('');
    try {
      const newJob = await ApiService.createJob(title, description);
      setJobs([newJob, ...jobs]);
      onSelectJob(newJob);
      setTitle('');
      setDescription('');
      setShowAddForm(false);
    } catch (err) {
      setError(err.message || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2 font-sans">
          <Briefcase className="w-5 h-5 text-brand-500" />
          Job Descriptions
        </h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-brand-600/80 hover:bg-brand-500 text-white text-xs font-semibold px-3 py-2 rounded-lg flex items-center gap-1.5 transition active:scale-95 glass-panel-light"
        >
          <Plus className="w-4 h-4" />
          {showAddForm ? 'Cancel' : 'New Job'}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleSubmit} className="glass-panel p-5 rounded-xl space-y-4 animate-fade-in">
          {error && <div className="text-red-400 text-xs">{error}</div>}
          
          <div>
            <label className="block text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1.5">
              Job Title
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Senior Full Stack Engineer"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="glass-input w-full px-3 py-2 rounded-lg text-sm"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1.5">
              Description / Requirements
            </label>
            <textarea
              required
              rows={6}
              placeholder="Paste job details, tech stack, responsibilities, and experience requirements..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="glass-input w-full px-3 py-2 rounded-lg text-sm resize-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold py-2.5 rounded-lg transition duration-150 flex items-center justify-center gap-1.5"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                AI Parsing JD...
              </>
            ) : (
              'Parse & Save Job'
            )}
          </button>
        </form>
      )}

      {/* Jobs List */}
      <div className="space-y-3">
        {fetching ? (
          <div className="flex justify-center py-6">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
          </div>
        ) : jobs.length === 0 ? (
          <p className="text-xs text-slate-500 italic text-center py-4">No jobs uploaded yet</p>
        ) : (
          <div className="max-h-60 overflow-y-auto pr-1 space-y-2">
            {jobs.map((job) => {
              const isActive = activeJob?.id === job.id;
              return (
                <div
                  key={job.id}
                  onClick={() => onSelectJob(job)}
                  className={`p-3 rounded-lg flex items-center justify-between cursor-pointer transition ${
                    isActive
                      ? 'bg-brand-600/20 border border-brand-500/50 shadow-md shadow-brand-500/5'
                      : 'bg-slate-900/40 border border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <FileText className={`w-4.5 h-4.5 ${isActive ? 'text-brand-400' : 'text-slate-500'}`} />
                    <div className="text-left min-w-0">
                      <p className="text-sm font-semibold truncate text-slate-200">{job.title}</p>
                      <p className="text-2xs text-slate-400 mt-0.5 truncate">
                        {job.extracted_metadata?.seniority || 'Unknown'} • {job.extracted_metadata?.experience_years || 'No exp specified'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={(e) => handleDeleteJob(e, job.id)}
                      className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-red-400 transition cursor-pointer active:scale-95"
                      title="Delete Job Description"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                    <ChevronRight className={`w-4 h-4 ${isActive ? 'text-brand-400' : 'text-slate-600'}`} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Selected Job Metadata Display */}
      {activeJob && activeJob.extracted_metadata && (
        <div className="glass-panel p-4 rounded-xl space-y-4 text-left border-l-2 border-brand-500">
          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Role Target</h4>
            <p className="text-base font-bold text-slate-200 mt-1">{activeJob.title}</p>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs border-t border-slate-800/80 pt-3">
            <div>
              <span className="text-slate-400 font-medium">Seniority</span>
              <p className="font-semibold text-slate-200 mt-0.5">{activeJob.extracted_metadata.seniority || 'N/A'}</p>
            </div>
            <div>
              <span className="text-slate-400 font-medium">Experience Target</span>
              <p className="font-semibold text-slate-200 mt-0.5">{activeJob.extracted_metadata.experience_years || 'N/A'}</p>
            </div>
          </div>

          {activeJob.extracted_metadata.skills_classification && (
            <div className="border-t border-slate-800/80 pt-3 space-y-2">
              <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block">Target Skill Hierarchy</span>
              
              {activeJob.extracted_metadata.skills_classification.mandatory?.length > 0 && (
                <div>
                  <span className="text-2xs font-semibold text-red-400 uppercase tracking-wide flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-red-500" />
                    Mandatory ({activeJob.extracted_metadata.skills_classification.mandatory.length})
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {activeJob.extracted_metadata.skills_classification.mandatory.slice(0, 8).map((skill, idx) => (
                      <span key={idx} className="bg-red-500/10 border border-red-500/20 text-red-300 text-2xs px-2 py-0.5 rounded-full">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {activeJob.extracted_metadata.skills_classification.preferred?.length > 0 && (
                <div className="pt-1">
                  <span className="text-2xs font-semibold text-blue-400 uppercase tracking-wide flex items-center gap-1">
                    <Award className="w-3 h-3 text-blue-500" />
                    Preferred ({activeJob.extracted_metadata.skills_classification.preferred.length})
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {activeJob.extracted_metadata.skills_classification.preferred.slice(0, 8).map((skill, idx) => (
                      <span key={idx} className="bg-blue-500/10 border border-blue-500/20 text-blue-300 text-2xs px-2 py-0.5 rounded-full">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
