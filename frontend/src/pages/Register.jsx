import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '../services/api';
import { motion } from 'framer-motion';
import { User, Mail, Lock, Loader2 } from 'lucide-react';

export default function Register() {
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.post('/register', formData);
      alert("Registration successful! Please login.");
      navigate('/login');
    } catch (err) {
      alert(err.response?.data?.detail || err.response?.data?.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card p-8 rounded-3xl w-full max-w-md shadow-2xl"
      >
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-white mb-2">Create Account</h2>
          <p className="text-slate-400 text-sm">Join us for your AI-powered interview</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="relative">
            <User className="absolute left-3 top-3.5 text-slate-500" size={20} />
            <input 
              type="text" 
              required
              placeholder="Full Name" 
              className="w-full pl-11 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl outline-none focus:border-indigo-500 focus:bg-white/10 transition-all text-white" 
              onChange={(e) => setFormData({...formData, name: e.target.value})} 
            />
          </div>
          <div className="relative">
            <Mail className="absolute left-3 top-3.5 text-slate-500" size={20} />
            <input 
              type="email" 
              required
              placeholder="Email address" 
              className="w-full pl-11 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl outline-none focus:border-indigo-500 focus:bg-white/10 transition-all text-white" 
              onChange={(e) => setFormData({...formData, email: e.target.value})} 
            />
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-3.5 text-slate-500" size={20} />
            <input 
              type="password" 
              required
              placeholder="Password" 
              className="w-full pl-11 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl outline-none focus:border-indigo-500 focus:bg-white/10 transition-all text-white" 
              onChange={(e) => setFormData({...formData, password: e.target.value})} 
            />
          </div>
          
          <button 
            disabled={loading}
            className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl font-bold transition-all flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" /> : "Register"}
          </button>
        </form>

        <p className="text-center mt-6 text-slate-400 text-sm">
          Already have an account? <Link to="/login" className="text-indigo-400 hover:underline">Sign In</Link>
        </p>
      </motion.div>
    </div>
  );
}
