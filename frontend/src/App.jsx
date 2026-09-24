import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import AppLayout from './layouts/AppLayout';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import Dashboard from './pages/Dashboard';
import ResumeAnalyzer from './pages/ResumeAnalyzer';
import JDAnalyzer from './pages/JDAnalyzer';
import SkillGap from './pages/SkillGap';
import Roadmap from './pages/Roadmap';
import MockInterview from './pages/MockInterview';
import CareerAssistant from './pages/CareerAssistant';
import CareerWhatIf from './pages/CareerWhatIf';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="h-screen bg-[#0B0F17] flex items-center justify-center text-xs text-gray-500">Loading CareerPilot...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="resume" element={<ResumeAnalyzer />} />
            <Route path="jobs" element={<JDAnalyzer />} />
            <Route path="skills" element={<SkillGap />} />
            <Route path="roadmap" element={<Roadmap />} />
            <Route path="projects" element={<Roadmap />} />
            <Route path="interview" element={<MockInterview />} />
            <Route path="chat" element={<CareerAssistant />} />
            <Route path="what-if" element={<CareerWhatIf />} />
            <Route path="progress" element={<Dashboard />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
