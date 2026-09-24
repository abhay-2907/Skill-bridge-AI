import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  SplitSquareVertical, CheckCircle2, XCircle, AlertTriangle,
  ArrowRight, Sparkles, Sliders, ChevronDown, Check, Zap, Target
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

export default function SkillGap() {
  const [activeResume, setActiveResume] = useState(null);
  const [recentJDs, setRecentJDs] = useState([]);
  const [selectedJdId, setSelectedJdId] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [gapResult, setGapResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [resResume, resJds] = await Promise.all([
          api.get('/resume/active'),
          api.get('/jobs')
        ]);
        setActiveResume(resResume.data);
        setRecentJDs(resJds.data);
        if (resJds.data.length > 0) setSelectedJdId(resJds.data[0].id);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, []);

  const handleRunGap = async () => {
    if (!activeResume || !selectedJdId) return;
    setAnalyzing(true);
    setError('');

    try {
      const res = await api.post('/skills/analyze', {
        resume_id: activeResume.id,
        job_description_id: parseInt(selectedJdId)
      });
      setGapResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to execute skill gap comparison.');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h2 className="text-2xl md:text-3xl font-black text-white tracking-tight flex items-center gap-2.5">
          <SplitSquareVertical className="h-7 w-7 text-blue-400" />
          Skill Gap Intelligence Engine
        </h2>
        <p className="text-xs md:text-sm text-gray-400 mt-1">
          Deterministic Python set intersections + character n-gram TF-IDF cosine similarity for semantic matching.
        </p>
      </div>

      {/* Control Selector Bar */}
      <div className="glass-panel rounded-2xl p-6 flex flex-col md:flex-row gap-5 items-center justify-between border border-white/[0.08]">
        <div className="w-full md:w-3/5 space-y-1.5">
          <label className="block text-xs font-semibold text-gray-300">Target Role / Job Posting</label>
          <div className="relative">
            <select
              value={selectedJdId}
              onChange={(e) => setSelectedJdId(e.target.value)}
              className="w-full bg-[#07090E] border border-white/[0.08] rounded-xl px-4 py-3 text-xs text-gray-200 focus:outline-none focus:border-blue-500/50 appearance-none font-medium"
            >
              {recentJDs.length === 0 && <option value="">No analyzed JDs found. Analyze one in JD Analyzer first!</option>}
              {recentJDs.map((jd) => (
                <option key={jd.id} value={jd.id}>
                  {jd.extracted_title || jd.title || `Job #${jd.id}`} {jd.company ? `— ${jd.company}` : ''}
                </option>
              ))}
            </select>
            <ChevronDown className="h-4 w-4 text-gray-500 absolute right-4 top-3.5 pointer-events-none" />
          </div>
        </div>

        <button
          onClick={handleRunGap}
          disabled={!activeResume || !selectedJdId || analyzing}
          className="w-full md:w-auto px-7 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 text-white font-bold text-xs transition shadow-lg shadow-blue-500/25 whitespace-nowrap"
        >
          {analyzing ? 'Computing TF-IDF & Cosine Similarity...' : 'Run Skill Gap Analysis'}
        </button>
      </div>

      {gapResult && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Score Banner */}
          <div className="relative overflow-hidden rounded-3xl border border-blue-500/30 bg-gradient-to-r from-blue-900/30 via-indigo-900/20 to-purple-900/30 p-8 shadow-xl">
            <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-blue-400 uppercase tracking-widest bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded-full">
                  Skill Alignment Index
                </span>
                <div className="flex items-baseline gap-3">
                  <h3 className="text-4xl md:text-5xl font-black text-white">{gapResult.match_score}%</h3>
                  <span className="text-xs text-gray-400">Match Benchmark</span>
                </div>
                <p className="text-xs text-gray-400 max-w-xl leading-relaxed">
                  Formula: (Exact Matches + 0.5 × Semantic Partial Matches) / Total Required Skills. Grounded educational indicator.
                </p>
              </div>

              <Link
                to="/roadmap"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition shadow-lg shadow-blue-500/20 shrink-0"
              >
                Synthesize Learning Roadmap
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>

          {/* Three Columns: Matched / Partial / Missing */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Column 1: Matched */}
            <div className="glass-panel rounded-2xl p-6 space-y-4 border border-emerald-500/20">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 text-emerald-400 font-bold text-xs uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4" /> Matched Skills
                </span>
                <span className="bg-emerald-500/10 px-2 py-0.5 rounded text-[10px]">
                  {gapResult.matched_skills?.length || 0}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {gapResult.matched_skills?.map((s) => (
                  <span key={s} className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/25 text-xs font-medium">
                    {s}
                  </span>
                ))}
                {gapResult.matched_skills?.length === 0 && <span className="text-xs text-gray-500">None detected</span>}
              </div>
            </div>

            {/* Column 2: Partial */}
            <div className="glass-panel rounded-2xl p-6 space-y-4 border border-amber-500/20">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 text-amber-400 font-bold text-xs uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4" /> Related (Partial)
                </span>
                <span className="bg-amber-500/10 px-2 py-0.5 rounded text-[10px]">
                  {gapResult.partial_skills?.length || 0}
                </span>
              </div>
              <div className="space-y-2">
                {gapResult.partial_skills?.map((p, i) => (
                  <div key={i} className="text-xs p-2.5 rounded-xl bg-amber-500/[0.03] border border-amber-500/20 text-gray-300 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-amber-300">{p.resume_skill}</span>
                      <span className="text-[10px] text-gray-400 bg-black/40 px-1.5 py-0.5 rounded">
                        {Math.round(p.similarity * 100)}% similarity
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-400">Related to target: <span className="text-white font-semibold">{p.jd_skill}</span></p>
                  </div>
                ))}
                {gapResult.partial_skills?.length === 0 && <span className="text-xs text-gray-500">No related variants found</span>}
              </div>
            </div>

            {/* Column 3: Missing */}
            <div className="glass-panel rounded-2xl p-6 space-y-4 border border-rose-500/20">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 text-rose-400 font-bold text-xs uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <XCircle className="h-4 w-4" /> Missing Competencies
                </span>
                <span className="bg-rose-500/10 px-2 py-0.5 rounded text-[10px]">
                  {gapResult.missing_skills?.length || 0}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {gapResult.missing_skills?.map((s) => (
                  <span key={s} className="px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/25 text-xs font-medium">
                    {s}
                  </span>
                ))}
                {gapResult.missing_skills?.length === 0 && <span className="text-xs text-gray-500">Zero gaps! Perfect alignment.</span>}
              </div>
            </div>
          </div>

          {/* AI Grounded Coaching */}
          <div className="glass-panel rounded-3xl p-8 space-y-3 border border-white/[0.08]">
            <div className="flex items-center gap-2 border-b border-white/[0.06] pb-3 text-blue-400">
              <Sparkles className="h-4 w-4" />
              <h3 className="font-bold text-sm text-white">Strategic Learning Advice (IBM Granite RAG)</h3>
            </div>
            <div className="text-xs md:text-sm text-gray-300 leading-relaxed whitespace-pre-wrap pt-1 font-sans">
              {gapResult.ai_explanation || 'No explanation generated.'}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
