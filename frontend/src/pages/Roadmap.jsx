import React, { useState } from 'react';
import api from '../services/api';
import { Compass, CheckCircle2, Clock, Sparkles } from 'lucide-react';

export default function Roadmap() {
  const [duration, setDuration] = useState(30);
  const [hours, setHours] = useState(10);
  const [generating, setGenerating] = useState(false);
  const [roadmap, setRoadmap] = useState(null);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await api.post('/roadmap/generate', {
        skill_gap_id: 1, // Connects to most recent gap
        duration_days: duration,
        available_hours_per_week: hours,
      });
      setRoadmap(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleTask = async (taskId, currentStatus) => {
    const nextStatus = currentStatus === 'completed' ? 'pending' : 'completed';
    try {
      await api.patch(`/roadmap/${roadmap.id}/tasks/${taskId}`, { status: nextStatus });
      setRoadmap((prev) => ({
        ...prev,
        tasks: prev.tasks.map((t) => (t.id === taskId ? { ...t, status: nextStatus } : t)),
      }));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Personalized Learning Roadmap</h2>
        <p className="text-xs text-gray-400 mt-1">Generate a structured multi-week schedule targeting your specific missing competencies.</p>
      </div>

      {/* Generator Controls */}
      <div className="bg-[#111827] border border-gray-800 rounded-xl p-6 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="flex gap-4 w-full md:w-auto">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Time Horizon</label>
            <select
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              className="bg-[#0B0F17] border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-200"
            >
              <option value={30}>30 Days (Fast Track)</option>
              <option value={60}>60 Days (Balanced)</option>
              <option value={90}>90 Days (Comprehensive)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Study Hours / Week</label>
            <input
              type="number"
              value={hours}
              onChange={(e) => setHours(parseInt(e.target.value))}
              className="bg-[#0B0F17] border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-200 w-24"
            />
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating}
          className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs transition shadow-lg shadow-blue-500/20"
        >
          {generating ? 'Synthesizing with IBM Granite...' : 'Generate Adaptive Roadmap'}
        </button>
      </div>

      {/* Roadmap Tasks View */}
      {roadmap && (
        <div className="space-y-4">
          <h3 className="font-bold text-white text-base">{roadmap.title}</h3>
          <div className="space-y-3">
            {roadmap.tasks?.map((task) => (
              <div
                key={task.id}
                className={`bg-[#111827] border rounded-xl p-5 transition flex items-start gap-4 ${
                  task.status === 'completed' ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-gray-800'
                }`}
              >
                <button
                  onClick={() => handleToggleTask(task.id, task.status)}
                  className={`mt-0.5 p-1 rounded-full transition ${
                    task.status === 'completed' ? 'text-emerald-400' : 'text-gray-600 hover:text-gray-400'
                  }`}
                >
                  <CheckCircle2 className="h-5 w-5" />
                </button>

                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">
                      Week {task.week_number}
                    </span>
                    <span className="text-[10px] text-gray-500 bg-gray-800 px-2 py-0.5 rounded">{task.skill}</span>
                    <span className="text-xs font-semibold text-white">{task.topic}</span>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed">{task.task_description}</p>
                  {task.practice_task && (
                    <p className="text-[11px] text-indigo-300 font-medium">Practice: {task.practice_task}</p>
                  )}
                </div>

                <div className="text-right text-[11px] text-gray-400 whitespace-nowrap">
                  <span className="flex items-center gap-1 justify-end">
                    <Clock className="h-3 w-3" />
                    {task.estimated_hours || 5}h
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
