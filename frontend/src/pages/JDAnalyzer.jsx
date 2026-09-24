import React, { useState } from 'react';
import api from '../services/api';
import { Briefcase, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';

export default function JDAnalyzer() {
  const [jdText, setJdText] = useState('');
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!jdText.trim()) return;

    setAnalyzing(true);
    setError('');

    try {
      const res = await api.post('/jobs/analyze', {
        raw_text: jdText,
        title: title || undefined,
        company: company || undefined,
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze job description.');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Job Description Analyzer</h2>
        <p className="text-xs text-gray-400 mt-1">Paste a target job posting to break down mandatory vs preferred technical skills and domain context.</p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleAnalyze} className="bg-[#111827] border border-gray-800 rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Target Role Title (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Senior Backend Engineer"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-[#0B0F17] border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Company (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Acme Tech"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="w-full bg-[#0B0F17] border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-300 mb-1">Job Description Content</label>
          <textarea
            rows={8}
            placeholder="Paste the full job description text here..."
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            required
            className="w-full bg-[#0B0F17] border border-gray-800 rounded-lg p-3 text-xs text-gray-200 focus:outline-none focus:border-blue-500 leading-relaxed font-mono"
          />
        </div>

        <button
          type="submit"
          disabled={!jdText.trim() || analyzing}
          className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition shadow-lg shadow-indigo-500/20"
        >
          {analyzing ? 'Extracting Requirements with NLP...' : 'Analyze Job Description'}
        </button>
      </form>

      {/* Results View */}
      {result && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1 bg-[#111827] border border-gray-800 rounded-xl p-6 space-y-4">
            <h3 className="font-semibold text-white text-sm border-b border-gray-800 pb-3">Detected Classification</h3>
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-gray-400">Classified Role Domain:</span>
                <p className="font-medium text-indigo-400">{result.extracted_domain || 'General'}</p>
              </div>
              <div>
                <span className="text-gray-400">Experience Requirement:</span>
                <p className="font-medium text-gray-200">{result.extracted_experience_required || 'Not specified'}</p>
              </div>
              <div>
                <span className="text-gray-400">Extracted Skills ({result.extracted_technologies?.length || 0}):</span>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {result.extracted_technologies?.map((s) => (
                    <span key={s} className="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[11px]">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="md:col-span-2 bg-[#111827] border border-gray-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-2 border-b border-gray-800 pb-3">
              <Sparkles className="h-4 w-4 text-indigo-400" />
              <h3 className="font-semibold text-white text-sm">Role Analysis Breakdown</h3>
            </div>
            <div className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
              {result.ai_analysis || 'No detailed analysis generated.'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
