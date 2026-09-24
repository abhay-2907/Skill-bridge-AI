import React, { useState } from 'react';
import api from '../services/api';
import {
  HelpCircle, Send, CheckCircle2, AlertCircle, Sparkles,
  Award, RefreshCw, Zap, BookOpen, Brain, Terminal
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';

export default function MockInterview() {
  const [interviewType, setInterviewType] = useState('python');
  const [difficulty, setDifficulty] = useState('intermediate');
  const [session, setSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [answerText, setAnswerText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [isComplete, setIsComplete] = useState(false);

  const handleStart = async () => {
    try {
      const res = await api.post('/interview/start', {
        interview_type: interviewType,
        difficulty: difficulty,
      });
      setSession(res.data);
      setCurrentQuestion(res.data.question);
      setFeedback(null);
      setIsComplete(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSubmitAnswer = async (e) => {
    e.preventDefault();
    if (!answerText.trim() || submitting) return;

    setSubmitting(true);
    try {
      const res = await api.post(`/interview/${session.interview_id}/answer`, {
        answer_text: answerText,
      });
      setFeedback(res.data.feedback);
      if (res.data.is_complete) {
        setIsComplete(true);
        confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
      } else {
        setCurrentQuestion(res.data.next_question);
      }
      setAnswerText('');
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl md:text-3xl font-black text-white tracking-tight flex items-center gap-2.5">
            <Brain className="h-7 w-7 text-purple-400" />
            Adaptive Mock Interview
          </h2>
          <p className="text-xs md:text-sm text-gray-400 mt-1">
            Simulate realistic engineering interviews powered by IBM Granite & RAG with adaptive follow-ups targeting detected weaknesses.
          </p>
        </div>

        {session && (
          <button
            onClick={() => setSession(null)}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-xs font-semibold text-gray-300 border border-white/[0.08] transition"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Reset Session
          </button>
        )}
      </div>

      {!session ? (
        /* Configuration Modal/Card */
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-panel rounded-3xl p-8 max-w-xl mx-auto space-y-6 border border-white/[0.08] shadow-2xl relative overflow-hidden"
        >
          <div className="space-y-1 text-center">
            <div className="h-12 w-12 mx-auto rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mb-3">
              <Terminal className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Interview Configuration</h3>
            <p className="text-xs text-gray-400">Select your specialization track and target seniority level</p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Specialization Track</label>
              <select
                value={interviewType}
                onChange={(e) => setInterviewType(e.target.value)}
                className="w-full bg-[#07090E] border border-white/[0.08] rounded-xl px-4 py-3 text-xs text-gray-200 focus:outline-none focus:border-purple-500/50"
              >
                <option value="python">Python Backend Architecture & GIL</option>
                <option value="ai_ml">Machine Learning & Neural Architectures</option>
                <option value="genai">Generative AI, Prompting & Fine-Tuning</option>
                <option value="rag">Retrieval-Augmented Generation & FAISS</option>
                <option value="sql">Relational Databases & SQL Optimization</option>
                <option value="system_design">High-Scale System Design Basics</option>
                <option value="behavioral">Behavioral, Conflict & Leadership</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Seniority Level</label>
              <div className="grid grid-cols-3 gap-2.5">
                {[
                  { id: 'beginner', label: 'Entry Level' },
                  { id: 'intermediate', label: 'Mid-Level' },
                  { id: 'advanced', label: 'Senior Lead' },
                ].map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => setDifficulty(d.id)}
                    className={`py-2.5 px-3 rounded-xl text-xs font-semibold border transition ${
                      difficulty === d.id
                        ? 'bg-purple-600/20 text-purple-300 border-purple-500/50 shadow-sm'
                        : 'bg-[#07090E] text-gray-400 border-white/[0.06] hover:bg-white/[0.02]'
                    }`}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <button
            onClick={handleStart}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs transition shadow-lg shadow-purple-500/25 flex items-center justify-center gap-2"
          >
            <Zap className="h-4 w-4" />
            Launch Interactive Interview
          </button>
        </motion.div>
      ) : (
        /* Active Interview Space */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Question & Answer Column */}
          <div className="lg:col-span-7 space-y-6">
            {!isComplete && currentQuestion && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel rounded-2xl p-6 md:p-8 space-y-5 border border-purple-500/20 relative overflow-hidden"
              >
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-1 rounded-md bg-purple-500/10 text-purple-300 font-bold text-[10px] uppercase tracking-wider border border-purple-500/20">
                    Question {currentQuestion.order_index + 1}
                  </span>
                  {currentQuestion.is_followup && (
                    <span className="text-[11px] font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-md flex items-center gap-1">
                      <Zap className="h-3 w-3" /> Adaptive Target: {currentQuestion.topic}
                    </span>
                  )}
                </div>

                <h3 className="text-base md:text-lg font-bold text-white leading-relaxed">
                  {currentQuestion.question_text}
                </h3>

                <form onSubmit={handleSubmitAnswer} className="space-y-4 pt-2">
                  <div className="relative">
                    <textarea
                      rows={5}
                      placeholder="Formulate your detailed technical response..."
                      value={answerText}
                      onChange={(e) => setAnswerText(e.target.value)}
                      className="w-full bg-[#07090E] border border-white/[0.08] focus:border-purple-500/50 rounded-xl p-4 text-xs md:text-sm text-gray-200 focus:outline-none transition leading-relaxed font-sans"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={!answerText.trim() || submitting}
                    className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-bold text-xs flex items-center justify-center gap-2 transition shadow-md shadow-purple-500/20"
                  >
                    <Send className="h-3.5 w-3.5" />
                    {submitting ? 'Synthesizing Evaluation...' : 'Submit Response'}
                  </button>
                </form>
              </motion.div>
            )}

            {isComplete && (
              <div className="glass-panel rounded-2xl p-8 text-center space-y-4 border border-emerald-500/30">
                <div className="h-12 w-12 mx-auto rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
                  <CheckCircle2 className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-white">Interview Session Completed</h3>
                <p className="text-xs text-gray-400 max-w-md mx-auto">
                  You have successfully answered all allocated practice questions. Review your feedback analysis on the right panel.
                </p>
              </div>
            )}
          </div>

          {/* Feedback & Score Column */}
          <div className="lg:col-span-5 space-y-6">
            <AnimatePresence mode="wait">
              {feedback ? (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  className="glass-panel rounded-2xl p-6 space-y-5 border border-white/[0.08]"
                >
                  <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-purple-400" />
                      <h4 className="font-bold text-sm text-white">AI Evaluation Score</h4>
                    </div>
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20">
                      <span className="text-xs font-black text-purple-400">{feedback.ai_score}</span>
                      <span className="text-[10px] text-gray-400">/ 10</span>
                    </div>
                  </div>

                  <div className="space-y-4 text-xs">
                    <div className="space-y-1.5 p-3 rounded-xl bg-emerald-500/[0.04] border border-emerald-500/20">
                      <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Strengths Demonstrated
                      </span>
                      <p className="text-gray-300 leading-relaxed pl-5">{feedback.what_was_correct}</p>
                    </div>

                    <div className="space-y-1.5 p-3 rounded-xl bg-amber-500/[0.04] border border-amber-500/20">
                      <span className="text-amber-400 font-bold flex items-center gap-1.5">
                        <AlertCircle className="h-3.5 w-3.5" /> Gaps & Missing Depth
                      </span>
                      <p className="text-gray-300 leading-relaxed pl-5">{feedback.what_was_missing}</p>
                    </div>

                    <div className="space-y-1.5 p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                      <span className="text-blue-400 font-bold flex items-center gap-1.5">
                        <BookOpen className="h-3.5 w-3.5" /> Model Answer
                      </span>
                      <p className="text-gray-300 leading-relaxed mt-1 font-mono text-[11px]">{feedback.better_answer}</p>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <div className="glass-panel rounded-2xl p-8 text-center space-y-3 border border-dashed border-white/[0.06]">
                  <HelpCircle className="h-8 w-8 text-gray-600 mx-auto" />
                  <p className="text-xs text-gray-400">Submit a response to trigger instant AI evaluation and coaching feedback.</p>
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  );
}
