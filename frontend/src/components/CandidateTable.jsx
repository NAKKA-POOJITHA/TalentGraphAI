import React, { useState, useMemo } from 'react';
import { Search, Filter, SlidersHorizontal, ArrowUpDown, Award, TrendingUp, ShieldAlert, X } from 'lucide-react';

export default function CandidateTable({ candidates, onSelectCandidate, selectedCandidate, isRanked, onDeleteCandidate }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [growthFilter, setGrowthFilter] = useState('All');
  const [minScore, setMinScore] = useState(0);
  const [minExp, setMinExp] = useState(0);
  const [recFilter, setRecFilter] = useState('All');

  // Filter candidates
  const filteredCandidates = useMemo(() => {
    return candidates.filter(cand => {
      // 1. Search term check (name, email, skills, strengths, or gaps)
      const strengths = cand.explainability?.strengths || [];
      const gaps = cand.explainability?.gaps || [];
      const skills = cand.full_eval?.profile_actual?.skills || cand.skills || [];
      
      const matchesSearch = 
        cand.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (cand.email && cand.email.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (skills.some(s => s.toLowerCase().includes(searchTerm.toLowerCase()))) ||
        (strengths.some(s => s.toLowerCase().includes(searchTerm.toLowerCase()))) ||
        (gaps.some(g => g.toLowerCase().includes(searchTerm.toLowerCase())));

      // 2. Growth filter
      const matchesGrowth = !isRanked || growthFilter === 'All' || cand.growth_category === growthFilter;

      // 3. Min Score check
      const matchesScore = !isRanked || cand.overall_score >= minScore;

      // 4. Experience check (retrieve from full_eval.profile_actual.experience_years or metadata)
      const expYears = cand.full_eval?.profile_actual?.experience_years || cand.experience_years || cand.growth_score / 10 || 0; // fallback
      const matchesExp = expYears >= minExp;

      // 5. Recommendation filter
      const matchesRec = !isRanked || recFilter === 'All' || cand.recommendation === recFilter;

      return matchesSearch && matchesGrowth && matchesScore && matchesExp && matchesRec;
    });
  }, [candidates, searchTerm, growthFilter, minScore, minExp, recFilter, isRanked]);

  const getGrowthBadge = (category) => {
    switch (category) {
      case 'High':
        return <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs px-2 py-0.5 rounded-full font-semibold flex items-center gap-1 w-fit"><TrendingUp className="w-3.5 h-3.5" /> High</span>;
      case 'Medium':
        return <span className="bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs px-2 py-0.5 rounded-full font-semibold flex items-center gap-1 w-fit">Medium</span>;
      default:
        return <span className="bg-slate-500/10 border border-slate-500/20 text-slate-400 text-xs px-2 py-0.5 rounded-full font-semibold flex items-center gap-1 w-fit">Low</span>;
    }
  };

  const getRecommendationBadge = (rec) => {
    switch (rec) {
      case 'Highly Recommended':
        return <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-2xs uppercase tracking-wider px-2 py-1 rounded font-bold flex items-center gap-1 w-fit"><Award className="w-3 h-3" /> Highly Rec</span>;
      case 'Recommended':
        return <span className="bg-blue-500/20 text-blue-300 border border-blue-500/30 text-2xs uppercase tracking-wider px-2 py-1 rounded font-bold w-fit">Recommended</span>;
      case 'Consider with Gaps':
        return <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-2xs uppercase tracking-wider px-2 py-1 rounded font-bold w-fit">Consider</span>;
      default:
        return <span className="bg-red-500/20 text-red-300 border border-red-500/30 text-2xs uppercase tracking-wider px-2 py-1 rounded font-bold flex items-center gap-1 w-fit"><ShieldAlert className="w-3.5 h-3.5" /> Avoid</span>;
    }
  };

  return (
    <div className="space-y-4 text-left">
      {/* Search & Filters Panel */}
      <div className="glass-panel p-4 rounded-xl grid grid-cols-1 md:grid-cols-5 gap-4">
        {/* Search */}
        <div className={`relative ${isRanked ? 'col-span-1 md:col-span-2' : 'col-span-1 md:col-span-4'}`}>
          <Search className="absolute left-3 top-2.5 w-4.5 h-4.5 text-slate-500" />
          <input
            type="text"
            placeholder={isRanked ? "Search candidates, skills, strengths..." : "Search candidates, skills..."}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="glass-input w-full pl-9 pr-4 py-2 rounded-lg text-sm"
          />
        </div>

        {isRanked && (
          <>
            {/* Growth filter */}
            <div className="relative">
              <select
                value={growthFilter}
                onChange={(e) => setGrowthFilter(e.target.value)}
                className="glass-input w-full px-3 py-2 rounded-lg text-sm appearance-none cursor-pointer"
              >
                <option value="All">All Growth Velocity</option>
                <option value="High">High Velocity</option>
                <option value="Medium">Medium Velocity</option>
                <option value="Low">Low Velocity</option>
              </select>
            </div>

            {/* Recommendation filter */}
            <div className="relative">
              <select
                value={recFilter}
                onChange={(e) => setRecFilter(e.target.value)}
                className="glass-input w-full px-3 py-2 rounded-lg text-sm appearance-none cursor-pointer"
              >
                <option value="All">All Recommendations</option>
                <option value="Highly Recommended">Highly Recommended</option>
                <option value="Recommended">Recommended</option>
                <option value="Consider with Gaps">Consider with Gaps</option>
                <option value="Not Recommended">Not Recommended</option>
              </select>
            </div>
          </>
        )}

        {/* Filters Toggle or Info */}
        <div className="flex items-center justify-between text-xs text-slate-400 font-semibold px-2">
          <span>Match: {filteredCandidates.length} of {candidates.length}</span>
        </div>
      </div>

      {/* Advanced sliders */}
      <div className={`glass-panel p-4 rounded-xl grid grid-cols-1 ${isRanked ? 'md:grid-cols-2' : 'md:grid-cols-1'} gap-6 text-xs text-slate-400 font-semibold`}>
        {isRanked && (
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Minimum Match Score: {minScore}%</span>
              <span className="text-brand-400">Filter out low matches</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-full accent-brand-500 bg-slate-800 rounded-lg cursor-pointer h-1.5"
            />
          </div>
        )}

        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Minimum Experience: {minExp} Years</span>
            <span className="text-brand-400">Experience baseline</span>
          </div>
          <input
            type="range"
            min="0"
            max="15"
            value={minExp}
            onChange={(e) => setMinExp(Number(e.target.value))}
            className="w-full accent-brand-500 bg-slate-800 rounded-lg cursor-pointer h-1.5"
          />
        </div>
      </div>

      {/* Candidate List Table */}
      <div className="glass-panel rounded-xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="bg-slate-900/60 border-b border-slate-800 text-slate-400 font-semibold text-2xs uppercase tracking-wider">
                {isRanked ? (
                  <>
                    <th className="py-3 px-4 text-center w-14">Rank</th>
                    <th className="py-3 px-4">Candidate Profile</th>
                    <th className="py-3 px-4 text-center">Semantic Match</th>
                    <th className="py-3 px-4 text-center">Growth Velocity</th>
                    <th className="py-3 px-4 text-center">Overall Fit</th>
                    <th className="py-3 px-4 text-center">Recommendation</th>
                  </>
                ) : (
                  <>
                    <th className="py-3 px-4">Candidate Profile</th>
                    <th className="py-3 px-4 text-center">Experience</th>
                    <th className="py-3 px-4">Top Skills</th>
                    <th className="py-3 px-4">Certifications</th>
                    <th className="py-3 px-4 text-center">Date Uploaded</th>
                  </>
                )}
                <th className="py-3 px-4 text-center w-12">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm">
              {filteredCandidates.length === 0 ? (
                <tr>
                  <td colSpan={isRanked ? 7 : 6} className="py-8 text-center text-slate-500 italic">
                    {isRanked 
                      ? "No ranked candidates match the selected filters. Try matching resumes." 
                      : "No indexed resumes found. Upload resumes to populate your database."}
                  </td>
                </tr>
              ) : (
                filteredCandidates.map((cand, idx) => {
                  const isSelected = selectedCandidate?.candidate_id === cand.candidate_id || selectedCandidate?.id === cand.id;
                  const expYears = cand.full_eval?.profile_actual?.experience_years || cand.experience_years || 0;
                  const skills = cand.full_eval?.profile_actual?.skills || cand.skills || [];
                  const certs = cand.certifications || [];
                  const dateStr = cand.created_at ? new Date(cand.created_at).toLocaleDateString() : 'N/A';
                  
                  return (
                    <tr
                      key={cand.candidate_id || cand.id}
                      onClick={() => onSelectCandidate(cand)}
                      className={`hover:bg-slate-900/30 transition-colors cursor-pointer ${
                        isSelected ? 'bg-brand-600/10 border-l-2 border-l-brand-500 font-medium' : ''
                      }`}
                    >
                      {isRanked ? (
                        <>
                          {/* Rank */}
                          <td className="py-4 px-4 text-center">
                            <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full font-bold text-xs ${
                              cand.rank === 1
                                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                : cand.rank === 2
                                ? 'bg-slate-300/20 text-slate-200 border border-slate-300/30'
                                : cand.rank === 3
                                ? 'bg-amber-700/20 text-amber-600 border border-amber-700/30'
                                : 'text-slate-400'
                            }`}>
                              {cand.rank}
                            </span>
                          </td>

                          {/* Info */}
                          <td className="py-4 px-4">
                            <div>
                              <p className="font-bold text-slate-200">{cand.name}</p>
                              <p className="text-2xs text-slate-500 truncate mt-0.5 max-w-xs md:max-w-md">
                                {cand.email || 'N/A'} • {expYears}y exp • {skills.slice(0, 5).join(', ')}...
                              </p>
                            </div>
                          </td>

                          {/* Semantic Match */}
                          <td className="py-4 px-4 text-center">
                            <span className="font-mono font-semibold text-slate-300 text-xs">
                              {cand.semantic_score}%
                            </span>
                          </td>

                          {/* Growth Index */}
                          <td className="py-4 px-4 text-center flex justify-center mt-2.5">
                            {getGrowthBadge(cand.growth_category)}
                          </td>

                          {/* Overall Fit */}
                          <td className="py-4 px-4 text-center">
                            <div className="flex flex-col items-center justify-center gap-1">
                              <span className={`font-mono font-bold text-base ${
                                cand.overall_score >= 80 ? 'text-emerald-400' : cand.overall_score >= 60 ? 'text-blue-400' : 'text-slate-400'
                              }`}>
                                {cand.overall_score}%
                              </span>
                              {/* Mini Progress Bar */}
                              <div className="w-16 bg-slate-800 rounded-full h-1">
                                <div
                                  className={`h-1 rounded-full ${
                                    cand.overall_score >= 80 ? 'bg-emerald-500' : cand.overall_score >= 60 ? 'bg-blue-500' : 'bg-slate-600'
                                  }`}
                                  style={{ width: `${cand.overall_score}%` }}
                                ></div>
                              </div>
                            </div>
                          </td>

                          {/* Recommendation */}
                          <td className="py-4 px-4 text-center">
                            <div className="flex justify-center">
                              {getRecommendationBadge(cand.recommendation)}
                            </div>
                          </td>
                        </>
                      ) : (
                        <>
                          {/* Profile */}
                          <td className="py-4 px-4">
                            <div>
                              <p className="font-bold text-slate-200">{cand.name}</p>
                              <p className="text-2xs text-slate-500 truncate mt-0.5 max-w-xs md:max-w-md">
                                {cand.email || 'N/A'}
                              </p>
                            </div>
                          </td>
                          {/* Experience */}
                          <td className="py-4 px-4 text-center font-mono font-semibold text-slate-300">
                            {expYears}y
                          </td>
                          {/* Top Skills */}
                          <td className="py-4 px-4 max-w-xs md:max-w-sm">
                            <div className="flex flex-wrap gap-1">
                              {skills.slice(0, 3).map((skill, sIdx) => (
                                <span key={sIdx} className="bg-slate-800 text-slate-300 text-3xs px-2 py-0.5 rounded font-medium border border-slate-700/50">
                                  {skill}
                                </span>
                              ))}
                              {skills.length > 3 && (
                                <span className="text-3xs text-slate-500 font-semibold pl-1">
                                  +{skills.length - 3} more
                                </span>
                              )}
                              {skills.length === 0 && <span className="text-2xs text-slate-600 italic">None</span>}
                            </div>
                          </td>
                          {/* Certifications */}
                          <td className="py-4 px-4 text-slate-300 max-w-xs truncate">
                            {certs.length > 0 ? (
                              <span className="text-xs">{certs.slice(0, 2).join(', ')}</span>
                            ) : (
                              <span className="text-2xs text-slate-600 italic">None</span>
                            )}
                          </td>
                          {/* Date Uploaded */}
                          <td className="py-4 px-4 text-center text-xs text-slate-500">
                            {dateStr}
                          </td>
                        </>
                      )}
                      
                      {/* Delete Cross Action */}
                      <td className="py-4 px-4 text-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm(`Are you sure you want to delete ${cand.name}'s resume? This will permanently delete the candidate and its vector indexing.`)) {
                              onDeleteCandidate(cand.candidate_id || cand.id);
                            }
                          }}
                          className="p-1.5 rounded hover:bg-slate-800 text-slate-500 hover:text-red-400 transition cursor-pointer active:scale-95"
                          title="Delete Resume"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
