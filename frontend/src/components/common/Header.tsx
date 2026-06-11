import { useLocation } from 'react-router-dom';
import { Bell, Search } from 'lucide-react';

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/simulation': 'Simulation Engine',
  '/agents': 'AI Agents',
  '/data': 'Data Management',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
};

export default function Header() {
  const location = useLocation();

  const title = pageTitles[location.pathname] || 'Dashboard';

  return (
    <header style={{
      position: 'fixed',
      top: 0,
      right: 0,
      left: 'var(--sidebar-width)',
      height: 'var(--header-height)',
      background: 'rgba(10, 14, 26, 0.85)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 32px',
      zIndex: 40,
      transition: 'left var(--transition-base)',
    }}>
      <h1 style={{
        fontSize: '1.15rem',
        fontWeight: 700,
        color: 'var(--text-primary)',
      }}>
        {title}
      </h1>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Search */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 16px',
          background: 'var(--bg-tertiary)',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--border)',
        }}>
          <Search size={16} style={{ color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search..."
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.85rem',
              width: '180px',
              fontFamily: 'var(--font-primary)',
            }}
          />
        </div>

        {/* Notifications */}
        <button style={{
          position: 'relative',
          background: 'var(--bg-tertiary)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          padding: '8px',
          cursor: 'pointer',
          color: 'var(--text-secondary)',
        }}>
          <Bell size={18} />
          <span style={{
            position: 'absolute',
            top: 4,
            right: 4,
            width: 8,
            height: 8,
            background: 'var(--danger)',
            borderRadius: '50%',
          }} />
        </button>

        {/* Avatar */}
        <div style={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          background: 'var(--accent-gradient)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.85rem',
          fontWeight: 700,
          color: 'white',
        }}>
          SC
        </div>
      </div>
    </header>
  );
}
