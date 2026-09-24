import React, { useState } from 'react';
import api from '../services/api';
import { Sparkles, ArrowRight, ShieldAlert } from 'lucide-react';

export default function CareerWhatIf() {
  const [hypoSkills, setHypoSkills] = useState('');
  const [targetRole, setTargetRole] = useState('Full Stack Engineer');
  const [timeline, setTimeline] = useState(3);
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState(null);

  const handleSimulate = async (e) => {
    e.preventDefault();
    if (!hypoSkills.trim()) return;

    setSimulating(true);
    const skillsList = hypoSkills.split(',').map((s) => s.trim()).filter(Boolean);

    try {
      const res = await api.post('/career/what-if', {
        hypothetical_skills: skillsList,
        target_role: targetRole,
        timeline_months: timeline,
      });
      setResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Career What-If Simulator</h2>
        <p className="text-xs text-gray-400 mt-1">
          Explore hypothetical trajectories: "What if I learn Docker, Kubernetes, and FastAPI in 3 months?"
        </p>
      </div>

      <form onSubmit={handleSimulate} className="bg-[#111827] border border-gray-800 rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-400 mb-1">
              Hypothetical Skills (comma separated)
            </label>
            <input
              type="text"
              placeholder="e.g. Docker, Kubernetes, FastAPI, AWS"
              value={hypoSkills}
              onChange={(e) => setHypoSkills(e.target.value)}
              required
              className="w-full bg-[#0B0F17] border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-200"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Target Engineering Role</label>
            <input
              type="text"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              className="w-full bg-[#0B0F17] border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-200"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={simulating || !hypoSkills.trim()}
          className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition shadow-lg shadow-indigo-500/20"
        >
          {simulating ? 'Simulating Career Profile...' : 'Run What-If Simulation'}
        </button>
      </form>

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#111827] border border-gray-800 rounded-xl p-5 space-y-2">
              <span className="text-xs text-indigo-400 font-semibold uppercase">Simulated Role Alignment</span>
              <h3 className="text-3xl font-extrabold text-white">{result.coverage_improvement}%</h3>
              <p className="text-[11px] text-gray-400">Estimated coverage of skills required for {targetRole}.</p>
            </div>

            <div className="bg-[#111827] border border-gray-800 rounded-xl p-5 space-y-2">
              <span className="text-xs text-emerald-400 font-semibold uppercase">Combined Skill Inventory</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {result.combined_skills?.map((s) => (
                  <span key={s} className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[11px] border border-emerald-500/20">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-[#111827] border border-gray-800 rounded-xl p-6 space-y-3">
            <div className="flex items-center gap-2 border-b border-gray-800 pb-3">
              <Sparkles className="h-4 w-4 text-indigo-400" />
              <h3 className="font-semibold text-white text-sm">Strategic What-If Analysis</h3>
            </div>
            <div className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
              {result.analysis}
            </div>
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-[11px] text-amber-300 flex items-center gap-2 mt-4">
              <ShieldAlert className="h-4 w-4" />
              {result.disclaimer}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
