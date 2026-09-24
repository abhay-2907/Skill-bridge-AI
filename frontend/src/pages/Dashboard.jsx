import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  FileText, Briefcase, SplitSquareVertical, Compass,
  HelpCircle, Sparkles, ArrowRight, CheckCircle2, TrendingUp,
  Award, Shield, Flame, Target, BookOpen, Clock
} from 'lucide-react';
import { motion } from 'framer-motion';

export default function Dashboard() {
  const { user } = useAuth();
  const [progress, setProgress] = useState(null);
  const [activeResume, setActiveResume] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [progRes, resumeRes] = await Promise.allSettled([
          api.get('/progress'),
          api.get('/resume/active')
        ]);
        if (progRes.status === 'fulfilled') setProgress(progRes.value.data);
        if (resumeRes.status === 'fulfilled') setActiveResume(resumeRes.value.data);
      } catch (e) {
        console.error("Dashboard error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.08 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Hero Banner */}
      <motion.div
        variants={itemVariants}
        className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-gradient-to-br from-[#121829] via-[#0E1320] to-[#0A0D15] p-8 md:p-10 shadow-2xl"
      >
        {/* Decorative Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293d0f_1px,transparent_1px),linear-gradient(to_bottom,#1f293d0f_1px,transparent_1px)] bg-[size:2rem_2rem] pointer-events-none" />
        <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-blue-500/20 blur-[100px] pointer-events-none" />

        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 backdrop-blur-md">
            <Sparkles className="h-3.5 w-3.5 animate-spin-slow" />
            <span>AI Career & Interview Copilot</span>
          </div>

          <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Welcome back, <span className="shimmer-text">{user?.full_name?.split(' ')[0] || 'Engineer'}</span>
          </h2>

          <p className="text-gray-300 text-sm md:text-base leading-relaxed">
            Understand your skills. Find your gaps. Prepare smarter. Benchmark your profile against top engineering requirements with grounded ML & LLM reasoning.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <Link
              to="/resume"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-lg shadow-blue-500/25 transition-all transform hover:-translate-y-0.5"
            >
              <FileText className="h-4 w-4" />
              Upload Latest Resume
            </Link>
            <Link
              to="/skills"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/[0.05] hover:bg-white/[0.09] text-gray-200 border border-white/[0.08] font-semibold text-xs transition-all backdrop-blur-md"
            >
              <SplitSquareVertical className="h-4 w-4 text-blue-400" />
              Run Skill Gap Analysis
            </Link>
          </div>
        </div>
      </motion.div>

      {/* Metrics Row */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="glass-panel-interactive rounded-2xl p-5 space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Roadmap Progress</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Compass className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <h3 className="text-2xl font-black text-white">
              {progress?.roadmap_completion_percentage || 0}%
            </h3>
            <span className="text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-md">
              {progress?.completed_roadmap_tasks || 0}/{progress?.total_roadmap_tasks || 0}
            </span>
          </div>
          <div className="w-full bg-white/[0.05] rounded-full h-1.5 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress?.roadmap_completion_percentage || 0}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
            />
          </div>
        </div>

        {/* Metric 2 */}
        <div className="glass-panel-interactive rounded-2xl p-5 space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Mock Interviews</span>
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <HelpCircle className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <h3 className="text-2xl font-black text-white">
              {progress?.completed_interviews || 0}
            </h3>
            <span className="text-xs text-gray-400">Sessions</span>
          </div>
          <p className="text-[11px] text-gray-400 flex items-center gap-1">
            <Flame className="h-3.5 w-3.5 text-orange-400" /> Adaptive follow-up active
          </p>
        </div>

        {/* Metric 3 */}
        <div className="glass-panel-interactive rounded-2xl p-5 space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Practice Score</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Award className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <h3 className="text-2xl font-black text-white">
              {progress?.average_interview_score ? `${progress.average_interview_score}` : '0.0'}
              <span className="text-xs font-medium text-gray-400 ml-1">/10</span>
            </h3>
            <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md">AI Signal</span>
          </div>
          <p className="text-[11px] text-gray-400">Deterministic scoring baseline</p>
        </div>

        {/* Metric 4 */}
        <div className="glass-panel-interactive rounded-2xl p-5 space-y-3 relative overflow-hidden">
          <div className="flex items-center justify-between text-gray-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Resume</span>
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <FileText className="h-4 w-4" />
            </div>
          </div>
          <div className="truncate">
            <h3 className="text-sm font-bold text-white truncate">
              {activeResume?.filename || 'No Resume Uploaded'}
            </h3>
            <p className="text-[11px] text-blue-400 font-semibold mt-1">
              {activeResume ? `${activeResume.extracted_skills?.length || 0} skills indexed` : 'Upload to start'}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Quick Launch Interactive Cards */}
      <motion.div variants={itemVariants} className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Target className="h-4 w-4 text-blue-400" />
            Smart Action Shortcuts
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <Link
            to="/resume"
            className="glass-panel-interactive rounded-2xl p-6 group block"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 group-hover:scale-110 transition-transform">
                <FileText className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-gray-500 group-hover:text-blue-400 group-hover:translate-x-1 transition" />
            </div>
            <h4 className="font-bold text-white text-sm group-hover:text-blue-400 transition">Resume Parser & Critique</h4>
            <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">
              Extract technical skills, verify experience duration, and obtain actionable AI coaching points.
            </p>
          </Link>

          <Link
            to="/jobs"
            className="glass-panel-interactive rounded-2xl p-6 group block"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 group-hover:scale-110 transition-transform">
                <Briefcase className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-gray-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition" />
            </div>
            <h4 className="font-bold text-white text-sm group-hover:text-indigo-400 transition">Job Description Analyzer</h4>
            <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">
              Deconstruct postings into mandatory competencies, preferred frameworks, and domain context.
            </p>
          </Link>

          <Link
            to="/interview"
            className="glass-panel-interactive rounded-2xl p-6 group block"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 group-hover:scale-110 transition-transform">
                <HelpCircle className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-gray-500 group-hover:text-purple-400 group-hover:translate-x-1 transition" />
            </div>
            <h4 className="font-bold text-white text-sm group-hover:text-purple-400 transition">Adaptive Mock Interview</h4>
            <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">
              Conduct high-fidelity practice sessions with dynamic questions targeting detected concept weaknesses.
            </p>
          </Link>
        </div>
      </motion.div>
    </motion.div>
  );
}
