import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/common/Sidebar';
import Header from './components/common/Header';
import ErrorBoundary from './components/common/ErrorBoundary';
import DashboardPage from './pages/Dashboard';
import SimulationPage from './pages/Simulation';
import AgentsPage from './pages/Agents';
import DataPage from './pages/DataPage';
import AnalyticsPage from './pages/Analytics';
import SettingsPage from './pages/Settings';
import HomePage from './pages/Home';
import { useAppStore } from './store/appStore';
import { useAuthStore } from './store/authStore';
import { authService } from './services/authService';

function App() {
  const { sidebarCollapsed, showSimulation } = useAppStore();
  const { isAuthenticated, token, login, logout } = useAuthStore();

  useEffect(() => {
    const checkSession = async () => {
      if (token) {
        try {
          const res = await authService.getMe();
          login(token, res.data);
        } catch (e) {
          console.error('Session expired or invalid:', e);
          logout();
        }
      }
    };
    checkSession();
  }, [token]);

  const showSidebar = isAuthenticated || showSimulation;

  return (
    <BrowserRouter>
      <ErrorBoundary>
        <div className="app-layout">
          {showSidebar && <Sidebar />}
          {showSidebar && <Header />}
          <main 
            className={`main-content ${sidebarCollapsed ? 'collapsed' : ''}`}
            style={{ 
              marginLeft: showSidebar ? undefined : 0,
              paddingTop: showSidebar ? undefined : 0
            }}
          >
            <Routes>
              <Route path="/" element={showSidebar ? <DashboardPage /> : <HomePage />} />
              <Route path="/simulation" element={showSidebar && !isAuthenticated ? <SimulationPage /> : <Navigate to="/" replace />} />
              <Route path="/agents" element={showSidebar ? <AgentsPage /> : <Navigate to="/" replace />} />
              <Route path="/data" element={showSidebar ? <DataPage /> : <Navigate to="/" replace />} />
              <Route path="/analytics" element={showSidebar ? <AnalyticsPage /> : <Navigate to="/" replace />} />
              <Route path="/settings" element={showSidebar ? <SettingsPage /> : <Navigate to="/" replace />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
