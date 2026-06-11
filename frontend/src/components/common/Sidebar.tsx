import { NavLink, useNavigate } from 'react-router-dom';
import { useAppStore } from '../../store/appStore';
import { useAuthStore } from '../../store/authStore';
import { useSimulationStore } from '../../store/simulationStore';
import {
  LayoutDashboard, Activity, BarChart3, Settings, Database,
  Cpu, FlaskConical, ChevronLeft, ChevronRight, Zap, LogOut
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/simulation', label: 'Simulation', icon: FlaskConical },
  { path: '/agents', label: 'AI Agents', icon: Cpu },
  { path: '/data', label: 'Data', icon: Database },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar, mode, showSimulation, setShowSimulation } = useAppStore();
  const { isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleExit = () => {
    if (isAuthenticated) {
      logout();
    }
    useSimulationStore.getState().reset();
    setShowSimulation(false);
    navigate('/');
  };

  return (
    <aside
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        height: '100vh',
        width: sidebarCollapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-width)',
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width var(--transition-base)',
        zIndex: 50,
        overflow: 'hidden',
      }}
    >
      {/* Logo */}
      <div style={{
        padding: sidebarCollapsed ? '20px 16px' : '20px 24px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        minHeight: 'var(--header-height)',
      }}>
        <div style={{
          width: 36,
          height: 36,
          borderRadius: 'var(--radius-md)',
          background: 'var(--accent-gradient)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Zap size={20} color="white" />
        </div>
        {!sidebarCollapsed && (
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
              Supply Chain AI
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Orchestrator
            </div>
          </div>
        )}
      </div>

      {/* Mode Badge */}
      {!sidebarCollapsed && !isAuthenticated && (
        <div style={{ padding: '12px 24px' }}>
          <div style={{
            padding: '8px 12px',
            background: mode === 'simulation' ? 'var(--info-bg)' : mode === 'realtime' ? 'var(--success-bg)' : 'var(--warning-bg)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            <Activity size={14} style={{
              color: mode === 'simulation' ? 'var(--info)' : mode === 'realtime' ? 'var(--success)' : 'var(--warning)',
            }} />
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              color: mode === 'simulation' ? 'var(--info)' : mode === 'realtime' ? 'var(--success)' : 'var(--warning)',
            }}>
              {mode} Mode
            </span>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {navItems.filter(item => item.path !== '/simulation' || (!isAuthenticated && showSimulation)).map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: sidebarCollapsed ? '12px' : '10px 16px',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: isActive ? 'var(--bg-hover)' : 'transparent',
              borderLeft: isActive ? '3px solid var(--accent-primary)' : '3px solid transparent',
              fontSize: '0.875rem',
              fontWeight: isActive ? 600 : 400,
              transition: 'all var(--transition-fast)',
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
            })}
          >
            <Icon size={20} style={{ flexShrink: 0 }} />
            {!sidebarCollapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Exit / Logout Button */}
      <button
        onClick={handleExit}
        title={isAuthenticated ? "Log Out" : "Exit Demo"}
        style={{
          margin: '4px 12px',
          padding: sidebarCollapsed ? '12px' : '10px 16px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: 'var(--radius-md)',
          color: '#ef4444',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
          gap: '12px',
          fontWeight: 600,
          fontSize: '0.875rem',
          transition: 'all var(--transition-fast)',
        }}
      >
        <LogOut size={18} style={{ flexShrink: 0 }} />
        {!sidebarCollapsed && <span>{isAuthenticated ? 'Log Out' : 'Exit Demo'}</span>}
      </button>

      {/* Collapse Toggle */}
      <button
        onClick={toggleSidebar}
        style={{
          margin: '12px',
          padding: '10px',
          background: 'var(--bg-tertiary)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--text-secondary)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>
    </aside>
  );
}
