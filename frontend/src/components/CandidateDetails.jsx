import React, { useState, useEffect } from 'react';
import { X, Award, Eye, ShieldAlert, Sparkles, User, Briefcase, GraduationCap, CheckCircle, FileText, Activity } from 'lucide-react';

export default function CandidateDetails({ candidate, onClose }) {
  const [activeTab, setActiveTab] = useState('eval'); // 'eval' | 'resume' | 'bias'
  
  useEffect(() => {
    if (candidate) {
      const ranked = candidate.overall_score !== undefined && candidate.overall_score !== null;
      setActiveTab(ranked ? 'eval' : 'resume');
    }
  }, [candidate]);

  if (!candidate) return null;

  const isRanked = candidate.overall_score !== undefined && candidate.overall_score !== null;
  const actualProfile = candidate.full_eval?.profile_actual || {
    skills: candidate.skills || [],
    experience_years: candidate.experience_years || 0,
    education: candidate.education || [],
    companies: candidate.companies || [],
    certifications: candidate.certifications || [],
    projects: candidate.projects || [],
    achievements: candidate.achievements || [],
  };
  const expDetails = candidate.full_eval?.growth_details || {};
  const explain = candidate.explainability || {};
  const anonymizedProfile = candidate.bias_free_eval?.profile_sent || {};

  return (
    <div className="glass-panel w-full lg:max-w-2xl h-screen overflow-y-auto flex flex-col border-l border-slate-800 shadow-2xl relative animate-fade-in text-left">
      {/* Header */}
      <div className="p-6 border-b border-slate-800 flex items-center justify-between">
        <div>
          <span className="text-2xs font-bold uppercase tracking-wider text-brand-400">
            {isRanked ? `Rank #${candidate.rank} Candidate Detail` : "Indexed Resume Detail"}
          </span>
          <h2 className="text-2xl font-bold text-slate-100 mt-1">{candidate.name}</h2>
          <p className="text-xs text-slate-400 mt-0.5">{candidate.email || 'No email available'}</p>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-slate-200 transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Tabs */}
      {isRanked && (
        <div className="flex border-b border-slate-800 px-6 bg-slate-950/20">
          <button
            onClick={() => setActiveTab('eval')}
            className={`py-3 px-4 text-xs font-semibold uppercase tracking-wider border-b-2 transition ${
              activeTab === 'eval'
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            AI Evaluation & Explanation
          </button>
          <button
            onClick={() => setActiveTab('resume')}
            className={`py-3 px-4 text-xs font-semibold uppercase tracking-wider border-b-2 transition ${
              activeTab === 'resume'
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Parsed Resume Profile
          </button>
          <button
            onClick={() => setActiveTab('bias')}
            className={`py-3 px-4 text-xs font-semibold uppercase tracking-wider border-b-2 transition ${
              activeTab === 'bias'
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Bias Reduction Audit
          </button>
        </div>
      )}

      {/* Content Area */}
      <div className="flex-1 p-6 space-y-6">
        
        {/* TAB 1: EVALUATION AND EXPLAINABILITY */}
        {activeTab === 'eval' && (
          <div className="space-y-6 animate-fade-in">
            {/* Top Score Summary Cards */}
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-panel-light p-4 rounded-xl text-center space-y-1">
                <span className="text-2xs uppercase tracking-wider text-slate-400 font-bold block">Overall AI Fit</span>
                <p className="text-4xl font-extrabold text-brand-400 font-sans">{candidate.overall_score}%</p>
                <div className="flex justify-center mt-1">
                  <span className="bg-brand-500/10 border border-brand-500/20 text-brand-300 text-2xs px-2 py-0.5 rounded-full font-semibold">
                    Recommendation: {explain.recommendation}
                  </span>
                </div>
              </div>

              <div className="glass-panel-light p-4 rounded-xl text-center space-y-1">
                <span className="text-2xs uppercase tracking-wider text-slate-400 font-bold block">Confidence Level</span>
                <p className="text-4xl font-extrabold text-purple-400 font-sans">{explain.confidence || 90}%</p>
                <span className="text-2xs text-slate-400 block mt-1">AI assessment confidence</span>
              </div>
            </div>

            {/* Score Breakdown Progress Bars */}
            <div className="glass-panel p-5 rounded-xl space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5 border-b border-slate-800 pb-2">
                <Activity className="w-4 h-4 text-brand-500" /> Match Dimensions
              </h3>
              
              <div className="space-y-3.5">
                {[
                  { label: "Semantic Score", val: explain.semantic_match, desc: "Relevance of accomplishments to JD responsibilities", color: "bg-blue-500" },
                  { label: "Technical Score", val: explain.technical_match, desc: "Required tech stack skill completeness", color: "bg-emerald-500" },
                  { label: "Domain/Industry Fit", val: explain.domain_match, desc: "Alignment with industry sector requirements", color: "bg-indigo-500" },
                  { label: "Growth Velocity Score", val: explain.growth_velocity_score, desc: "Velocity based on career growth metrics", color: "bg-purple-500" }
                ].map((item, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-200">{item.label}</span>
                      <span className="text-slate-300">{item.val}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2">
                      <div className={`h-2 rounded-full ${item.color}`} style={{ width: `${item.val}%` }}></div>
                    </div>
                    <span className="text-3xs text-slate-400 block">{item.desc}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Reasoning Panel */}
            <div className="glass-panel p-5 rounded-xl space-y-2 border-l-2 border-brand-500 bg-slate-900/20">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">AI Evaluation Reason</h3>
              <p className="text-sm leading-relaxed text-slate-200">{explain.reasoning || "No explanation provided"}</p>
            </div>

            {/* Strengths & Gaps */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="glass-panel p-5 rounded-xl border-l-2 border-emerald-500 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Key Strengths</h4>
                {explain.strengths?.length > 0 ? (
                  <ul className="text-xs space-y-2 text-slate-300">
                    {explain.strengths.map((str, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="text-emerald-400 mt-0.5 shrink-0">✓</span>
                        <span>{str}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500 italic">No specific strengths listed</p>
                )}
              </div>

              <div className="glass-panel p-5 rounded-xl border-l-2 border-amber-500 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Skill Gaps</h4>
                {explain.gaps?.length > 0 ? (
                  <ul className="text-xs space-y-2 text-slate-300">
                    {explain.gaps.map((gap, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="text-amber-500 mt-0.5 shrink-0">⚠</span>
                        <span>{gap}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500 italic">No significant missing skills identified</p>
                )}
              </div>
            </div>

            {/* Growth Velocity Breakdown */}
            <div className="glass-panel p-5 rounded-xl space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5 border-b border-slate-800 pb-2">
                <Sparkles className="w-4 h-4 text-purple-400" /> Growth Velocity index
              </h3>
              
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 text-center">
                {[
                  { label: "Promotion", val: expDetails.promotion_frequency, weight: "30%" },
                  { label: "Skills", val: expDetails.skill_expansion, weight: "25%" },
                  { label: "Complexity", val: expDetails.project_complexity, weight: "20%" },
                  { label: "Certifications", val: expDetails.certification_growth, weight: "15%" },
                  { label: "Leadership", val: expDetails.leadership, weight: "10%" }
                ].map((score, idx) => (
                  <div key={idx} className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
                    <span className="text-3xs text-slate-400 uppercase tracking-wide block truncate">{score.label}</span>
                    <span className="font-mono font-bold text-slate-200 mt-1 block">{score.val}%</span>
                    <span className="text-3xs text-slate-500 mt-0.5 block">Wt: {score.weight}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-300 italic bg-slate-900/30 p-3 rounded border border-slate-800/40">
                {explain.growth_explanation}
              </p>
            </div>
          </div>
        )}

        {/* TAB 2: PARSED RESUME DETAILS */}
        {activeTab === 'resume' && (
          <div className="space-y-6 animate-fade-in">
            {/* Timeline info */}
            <div className="glass-panel p-5 rounded-xl space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
                <Briefcase className="w-4 h-4 text-brand-500" /> Work History & Timeline
              </h3>
              
              {actualProfile.projects?.length > 0 ? (
                <div className="space-y-4 relative border-l border-slate-800 pl-4 mt-2">
                  {actualProfile.projects.map((proj, idx) => (
                    <div key={idx} className="relative">
                      <div className="absolute -left-[20.5px] top-1.5 w-3 h-3 bg-brand-500 rounded-full border border-slate-950"></div>
                      <div className="space-y-1">
                        <span className="text-2xs text-brand-400 font-bold">{proj.role || "Developer"}</span>
                        <h4 className="text-sm font-bold text-slate-200">{proj.title}</h4>
                        <p className="text-xs text-slate-400 leading-relaxed">{proj.description}</p>
                        {proj.skills?.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {proj.skills.map((skill, sIdx) => (
                              <span key={sIdx} className="bg-slate-900 border border-slate-800 text-slate-300 text-3xs px-2 py-0.5 rounded">
                                {skill}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">No project timeline records available</p>
              )}
            </div>

            {/* Skills & Certs */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="glass-panel p-5 rounded-xl space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Technical Skills Toolkit</h3>
                <div className="flex flex-wrap gap-1.5">
                  {actualProfile.skills?.length > 0 ? (
                    actualProfile.skills.map((skill, idx) => (
                      <span key={idx} className="bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs px-2.5 py-0.5 rounded-full">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500 italic">No skills listed</span>
                  )}
                </div>
              </div>

              <div className="glass-panel p-5 rounded-xl space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Certifications</h3>
                {actualProfile.certifications?.length > 0 ? (
                  <ul className="text-xs space-y-2 text-slate-300">
                    {actualProfile.certifications.map((cert, idx) => (
                      <li key={idx} className="flex items-center gap-1.5">
                        <CheckCircle className="w-3.5 h-3.5 text-brand-400" />
                        <span>{cert}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500 italic">No certifications listed</p>
                )}
              </div>
            </div>

            {/* Education */}
            <div className="glass-panel p-5 rounded-xl space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
                <GraduationCap className="w-4.5 h-4.5 text-brand-500" /> Education
              </h3>
              {actualProfile.education?.length > 0 ? (
                <div className="grid grid-cols-1 gap-3.5">
                  {actualProfile.education.map((edu, idx) => (
                    <div key={idx} className="text-xs">
                      <p className="font-bold text-slate-200">{edu.degree}</p>
                      <p className="text-slate-400 mt-0.5">{edu.institution} • {edu.year || "N/A"}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">No education details parsed</p>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: BIAS REDUCTION MODULE COMPARE LOGS */}
        {activeTab === 'bias' && (
          <div className="space-y-6 animate-fade-in text-xs text-slate-300 leading-relaxed">
            <div className="glass-panel-light p-4 rounded-xl border-l-2 border-brand-500 space-y-1.5">
              <h4 className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
                <Eye className="w-4.5 h-4.5 text-brand-400" /> Bias Reduction Audit Trail
              </h4>
              <p className="text-slate-400">
                To guarantee equal opportunity screening, candidates are stripped of PII (Name, Email, Institutions name, locations, phone numbers) BEFORE being evaluated by the Gemini Engine. Compare the logs below to audit the sanitization.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Actual Log */}
              <div className="glass-panel p-4 rounded-xl space-y-3 bg-slate-900/30">
                <h4 className="text-xs uppercase font-bold tracking-wider text-slate-400">Full Profile (De-anonymized)</h4>
                
                <div className="space-y-2.5 font-mono text-2xs bg-slate-950/60 p-3 rounded max-h-96 overflow-y-auto">
                  <div>
                    <span className="text-brand-400">Candidate Name:</span> {candidate.name}
                  </div>
                  <div>
                    <span className="text-brand-400">Email:</span> {candidate.email || 'N/A'}
                  </div>
                  <div>
                    <span className="text-brand-400">Educations:</span>
                    <pre className="text-slate-400 mt-1 whitespace-pre-wrap">
                      {JSON.stringify(actualProfile.education, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <span className="text-brand-400">Projects Sample:</span>
                    <pre className="text-slate-400 mt-1 whitespace-pre-wrap">
                      {JSON.stringify(actualProfile.projects?.slice(0, 1), null, 2)}
                    </pre>
                  </div>
                </div>
              </div>

              {/* Anonymized Log */}
              <div className="glass-panel p-4 rounded-xl space-y-3 bg-slate-900/30">
                <h4 className="text-xs uppercase font-bold tracking-wider text-slate-400">Sanitized Profile (Sent to AI)</h4>
                
                <div className="space-y-2.5 font-mono text-2xs bg-slate-950/60 p-3 rounded max-h-96 overflow-y-auto">
                  <div>
                    <span className="text-brand-400">Candidate Name:</span> {anonymizedProfile.name || 'ANONYMOUS_CANDIDATE'}
                  </div>
                  <div>
                    <span className="text-brand-400">Email:</span> {anonymizedProfile.email || 'HIDDEN@TALENTGRAPH.AI'}
                  </div>
                  <div>
                    <span className="text-brand-400">Educations:</span>
                    <pre className="text-slate-400 mt-1 whitespace-pre-wrap">
                      {JSON.stringify(anonymizedProfile.education, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <span className="text-brand-400">Projects Sample:</span>
                    <pre className="text-slate-400 mt-1 whitespace-pre-wrap">
                      {JSON.stringify(anonymizedProfile.projects?.slice(0, 1), null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
