import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/api';
import { motion } from 'framer-motion';
import { Mail, Lock, Loader2 } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authApi.post('/login', { email, password });
      login({ id: res.data.user_id, email }, res.data.access_token);
      navigate('/dashboard');
    } catch (err) {
      alert(err.response?.data?.detail || err.response?.data?.message || "Login failed check credentials");
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
          <h2 className="text-3xl font-bold text-white mb-2">Welcome Back</h2>
          <p className="text-slate-400 text-sm">Please enter your details to sign in</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="relative">
            <Mail className="absolute left-3 top-3.5 text-slate-500" size={20} />
            <input 
              type="email" 
              required
              placeholder="Email address" 
              className="w-full pl-11 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl outline-none focus:border-indigo-500 focus:bg-white/10 transition-all text-white" 
              onChange={(e) => setEmail(e.target.value)} 
            />
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-3.5 text-slate-500" size={20} />
            <input 
              type="password" 
              required
              placeholder="Password" 
              className="w-full pl-11 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl outline-none focus:border-indigo-500 focus:bg-white/10 transition-all text-white" 
              onChange={(e) => setPassword(e.target.value)} 
            />
          </div>
          
          <button 
            disabled={loading}
            className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-bold shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" /> : "Sign In"}
          </button>
        </form>

        <p className="text-center mt-6 text-slate-400 text-sm">
          Don't have an account? <Link to="/register" className="text-indigo-400 hover:underline">Register now</Link>
        </p>
      </motion.div>
    </div>
  );
}
