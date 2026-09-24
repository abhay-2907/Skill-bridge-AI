import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { UploadCloud, CheckCircle, FileText, AlertCircle, Sparkles } from 'lucide-react';

export default function ResumeAnalyzer() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [resumeData, setResumeData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchActive = async () => {
      try {
        const res = await api.get('/resume/active');
        if (res.data) setResumeData(res.data);
      } catch (e) {
        // No active resume
      }
    };
    fetchActive();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/resume/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResumeData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload and analyze resume.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Resume Analyzer</h2>
        <p className="text-xs text-gray-400 mt-1">Upload your resume (PDF, DOCX, TXT) to extract skills, experience, and receive AI coaching.</p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Upload Zone */}
      <form onSubmit={handleUpload} className="bg-[#111827] border border-gray-800 rounded-xl p-8 text-center space-y-4">
        <div className="border-2 border-dashed border-gray-700 hover:border-blue-500/50 rounded-xl p-8 transition cursor-pointer relative">
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(e) => setFile(e.target.files[0])}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          <div className="flex flex-col items-center justify-center space-y-2">
            <div className="p-3 bg-blue-500/10 text-blue-400 rounded-full border border-blue-500/20">
              <UploadCloud className="h-6 w-6" />
            </div>
            <p className="text-sm font-medium text-gray-200">
              {file ? file.name : 'Click to select or drag and drop your resume file'}
            </p>
            <p className="text-[11px] text-gray-500">Supports PDF, DOCX, TXT (up to 10MB)</p>
          </div>
        </div>

        <button
          type="submit"
          disabled={!file || uploading}
          className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs transition shadow-lg shadow-blue-500/20"
        >
          {uploading ? 'Processing with NLP & AI...' : 'Analyze Resume'}
        </button>
      </form>

      {/* Analysis Results */}
      {resumeData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Extracted Details */}
          <div className="md:col-span-1 bg-[#111827] border border-gray-800 rounded-xl p-6 space-y-4">
            <h3 className="font-semibold text-white text-sm border-b border-gray-800 pb-3">Extracted Metadata</h3>
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-gray-400">Candidate Name:</span>
                <p className="font-medium text-gray-200">{resumeData.extracted_name || 'Not detected'}</p>
              </div>
              <div>
                <span className="text-gray-400">Email:</span>
                <p className="font-medium text-gray-200">{resumeData.extracted_email || 'Not detected'}</p>
              </div>
              <div>
                <span className="text-gray-400">Estimated Experience:</span>
                <p className="font-medium text-gray-200">
                  {resumeData.years_of_experience ? `${resumeData.years_of_experience} years` : 'Not detected'}
                </p>
              </div>
              <div>
                <span className="text-gray-400">Normalized Skills ({resumeData.extracted_skills?.length || 0}):</span>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {resumeData.extracted_skills?.map((s) => (
                    <span key={s} className="px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[11px]">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="md:col-span-2 bg-[#111827] border border-gray-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-2 border-b border-gray-800 pb-3">
              <Sparkles className="h-4 w-4 text-indigo-400" />
              <h3 className="font-semibold text-white text-sm">IBM Granite AI Coach Evaluation</h3>
            </div>
            <div className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
              {resumeData.ai_analysis || 'AI analysis generation in progress...'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
