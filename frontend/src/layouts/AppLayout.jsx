import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, FileText, Briefcase, SplitSquareVertical,
  Compass, Lightbulb, MessageSquare, HelpCircle,
  TrendingUp, LogOut, Sparkles, ChevronRight, Bell, Search, ShieldCheck
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, badge: null },
  { name: 'Resume Analyzer', href: '/resume', icon: FileText, badge: 'NLP' },
  { name: 'JD Analyzer', href: '/jobs', icon: Briefcase, badge: 'Parser' },
  { name: 'Skill Gap Engine', href: '/skills', icon: SplitSquareVertical, badge: 'ML' },
  { name: 'Learning Roadmap', href: '/roadmap', icon: Compass, badge: 'Adaptive' },
  { name: 'Mock Interview', href: '/interview', icon: HelpCircle, badge: 'Live AI' },
  { name: 'Career Assistant', href: '/chat', icon: MessageSquare, badge: 'RAG' },
  { name: 'Career What-If', href: '/what-if', icon: Sparkles, badge: 'Simulator' },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-[#07090E] text-gray-100 font-sans antialiased overflow-hidden selection:bg-blue-500/30 selection:text-blue-200">
      {/* Background Ambient Glows */}
      <div className="fixed top-[-10%] left-[-5%] w-[45vw] h-[45vw] rounded-full bg-blue-600/10 blur-[140px] pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[-5%] w-[45vw] h-[45vw] rounded-full bg-purple-600/10 blur-[150px] pointer-events-none" />

      {/* Sidebar */}
      <aside className="w-68 border-r border-white/[0.06] bg-[#0A0D15]/80 backdrop-blur-2xl flex flex-col z-20 shrink-0">
        {/* Brand Header */}
        <div className="p-6 pb-5 flex items-center gap-3.5 border-b border-white/[0.06]">
          <div className="relative">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 flex items-center justify-center font-extrabold text-base text-white shadow-lg shadow-blue-500/30 ring-1 ring-white/20">
              SB
            </div>
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 ring-2 ring-[#0A0D15]"></span>
            </span>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="font-extrabold text-base text-white tracking-tight leading-none">SkillBridge</h1>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">AI</span>
            </div>
            <p className="text-[11px] text-gray-400 font-medium mt-1">Smart Skill Copilot</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto px-3.5 py-4 space-y-1.5">
          <div className="px-3 pb-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
            Core Modules
          </div>
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `relative flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 group ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600/20 to-indigo-600/10 text-white border border-blue-500/30 shadow-sm shadow-blue-500/10'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.03]'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <div className={`p-1 rounded-lg transition-colors ${
                    isActive ? 'text-blue-400 bg-blue-500/10' : 'text-gray-400 group-hover:text-blue-400'
                  }`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <span>{item.name}</span>
                </div>

                {item.badge && (
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-md border ${
                    isActive 
                      ? 'bg-blue-500/20 text-blue-300 border-blue-500/40' 
                      : 'bg-white/[0.04] text-gray-500 border-white/[0.05] group-hover:text-gray-400'
                  }`}>
                    {item.badge}
                  </span>
                )}

                {isActive && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="absolute left-0 top-2 bottom-2 w-1 bg-blue-500 rounded-r-full shadow-lg shadow-blue-500/80"
                  />
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* User Profile Footer */}
        <div className="p-3.5 border-t border-white/[0.06] bg-[#07090E]/60">
          <div className="flex items-center justify-between p-2 rounded-xl bg-white/[0.03] border border-white/[0.05]">
            <div className="flex items-center gap-2.5 truncate">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-md">
                {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold text-gray-200 truncate">{user?.full_name || 'Candidate'}</p>
                <p className="text-[10px] text-emerald-400 font-medium flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Active Session
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-1.5 rounded-lg text-gray-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 border-b border-white/[0.06] bg-[#0A0D15]/60 backdrop-blur-xl px-8 flex items-center justify-between z-10">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span>SkillBridge Copilot</span>
            <ChevronRight className="h-3.5 w-3.5 text-gray-600" />
            <span className="text-gray-200 font-medium capitalize">
              {location.pathname.replace('/', '') || 'Dashboard'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] text-xs text-gray-400">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
              <span>Grounded AI Mode Active</span>
            </div>
          </div>
        </header>

        {/* Dynamic Route Content */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          <div className="max-w-6xl mx-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}
