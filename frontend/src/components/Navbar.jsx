import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, Cpu } from 'lucide-react';

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  if (!isAuthenticated) return null;

  return (
    <nav className="fixed top-0 w-full z-50 border-b border-white/10 bg-slate-950/50 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/dashboard" className="flex items-center gap-2 font-bold text-xl tracking-tight">
          <Cpu className="text-indigo-500" />
          <span>AI <span className="text-indigo-500">Recruiter</span></span>
        </Link>
        
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <User size={16} />
            {user?.email}
          </div>
          <button 
            onClick={() => { logout(); navigate('/login'); }}
            className="flex items-center gap-2 text-sm text-red-400 hover:text-red-300 transition-colors"
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
