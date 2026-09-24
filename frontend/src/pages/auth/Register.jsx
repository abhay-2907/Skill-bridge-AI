import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Register() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    setLoading(true);
    try {
      await register(email, password, fullName);
      navigate('/dashboard');
    } catch (err) {
      console.error('Registration error:', err);
      setError(err.response?.data?.detail || err.message || 'Registration failed. Please check the server is running.');
    } finally {
      setLoading(false);
    }
  };

  const inp = {
    width: '100%', background: '#0B0F17',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '10px', padding: '0.65rem 0.9rem',
    fontSize: '0.85rem', color: '#e5e7eb', outline: 'none',
    boxSizing: 'border-box', fontFamily: 'inherit',
  };

  return (
    <div style={{
      minHeight: '100vh', width: '100vw', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #07090E 0%, #0D1117 50%, #0B0F1A 100%)',
      padding: '1rem', boxSizing: 'border-box', position: 'relative', overflow: 'hidden',
    }}>
      <div style={{ position: 'absolute', top: '15%', left: '20%', width: '500px', height: '500px', background: 'radial-gradient(circle, rgba(59,130,246,0.09) 0%,transparent 70%)', pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', bottom: '10%', right: '15%', width: '400px', height: '400px', background: 'radial-gradient(circle, rgba(139,92,246,0.07) 0%,transparent 70%)', pointerEvents: 'none' }} />

      <div style={{
        width: '100%', maxWidth: '420px',
        background: 'rgba(13,17,28,0.92)',
        backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)',
        border: '1px solid rgba(255,255,255,0.07)', borderRadius: '20px',
        padding: '2.5rem',
        boxShadow: '0 25px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.05)',
        position: 'relative', zIndex: 1,
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <div style={{ width: '52px', height: '52px', margin: '0 auto 1.25rem', borderRadius: '14px', background: 'linear-gradient(135deg, #3b82f6, #6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem', fontWeight: '800', color: '#fff', boxShadow: '0 8px 24px rgba(99,102,241,0.4)' }}>SB</div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#f9fafb', margin: '0 0 0.5rem', letterSpacing: '-0.02em' }}>Create your account</h1>
          <p style={{ fontSize: '0.8rem', color: '#6b7280', margin: 0 }}>Join SkillBridge AI and begin your career preparation.</p>
        </div>

        {success && (
          <div style={{ padding: '0.75rem 1rem', background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '10px', color: '#4ade80', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
            {success}
          </div>
        )}

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1rem', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '10px', color: '#f87171', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
            <span>⚘</span> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: '600', color: '#d1d5db', marginBottom: '0.4rem' }}>Full Name</label>
            <input id="reg-name" type="text" required value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Alex Johnson" style={inp} />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: '600', color: '#d1d5db', marginBottom: '0.4rem' }}>Email Address</label>
            <input id="reg-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="candidate@example.com" style={inp} />
          </div>
          <div style={{ marginBottom: '1.75rem' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: '600', color: '#d1d5db', marginBottom: '0.4rem' }}>Password <span style={{ color: '#6b7280', fontWeight: '400' }}>(min 8 characters)</span></label>
            <div style={{ position: 'relative' }}>
              <input id="reg-password" type={showPass ? 'text' : 'password'} required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" style={{ ...inp, paddingRight: '2.8rem' }} />
              <button type="button" onClick={() => setShowPass(!showPass)} style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280', fontSize: '0.75rem', padding: 0 }}>
                {showPass ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          <button id="reg-submit" type="submit" disabled={loading} style={{
            width: '100%', padding: '0.8rem', borderRadius: '10px',
            background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
            border: 'none', color: '#fff', fontWeight: '600', fontSize: '0.9rem',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 20px rgba(99,102,241,0.35)',
            opacity: loading ? 0.65 : 1, transition: 'opacity 0.2s', fontFamily: 'inherit',
          }}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p style={{ textAlign: 'center', fontSize: '0.8rem', color: '#6b7280', marginTop: '1.5rem', marginBottom: 0 }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: '500' }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
