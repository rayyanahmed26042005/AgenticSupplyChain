import React, { useEffect, useRef, useState } from 'react';
import {
  Zap,
  TrendingUp,
  AlertTriangle,
  Cpu,
  ArrowRight,
  LogIn,
  Lock,
  Mail,
  User,
  Check,
  Globe,
  DollarSign,
  Clock,
  Settings,
  Activity,
  FileText
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useAppStore } from '../store/appStore';
import { authService } from '../services/authService';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

// Intersection Observer Hook for Scroll Animations
const useScrollReveal = () => {
  const [isRevealed, setIsRevealed] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsRevealed(true);
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, []);

  return { ref, isRevealed };
};

interface RevealWrapperProps {
  children: React.ReactNode;
  delay?: number;
}

const RevealWrapper: React.FC<RevealWrapperProps> = ({ children, delay = 0 }) => {
  const { ref, isRevealed } = useScrollReveal();
  return (
    <div
      ref={ref}
      style={{
        opacity: isRevealed ? 1 : 0,
        transform: isRevealed ? 'translateY(0)' : 'translateY(40px)',
        transition: `opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1) ${delay}s, transform 0.8s cubic-bezier(0.16, 1, 0.3, 1) ${delay}s`,
      }}
    >
      {children}
    </div>
  );
};

const getErrorMessage = (err: any): string => {
  if (!err) return 'An unknown error occurred';
  if (typeof err === 'string') return err;
  
  if (err.detail) {
    if (Array.isArray(err.detail)) {
      return err.detail.map((e: any) => `${e.loc ? e.loc.join('.') + ': ' : ''}${e.msg}`).join(', ');
    }
    if (typeof err.detail === 'string') {
      return err.detail;
    }
  }
  
  if (err.message) {
    return err.message;
  }
  
  if (err.error) {
    return typeof err.error === 'string' ? err.error : JSON.stringify(err.error);
  }
  
  return JSON.stringify(err);
};

export default function Home() {
  const { isAuthenticated, user, login, logout } = useAuthStore();
  const { setShowSimulation } = useAppStore();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isLoginTab, setIsLoginTab] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  // Form Fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  // Simulation Setup Modal
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [setupData, setSetupData] = useState<any>(null);
  const [setupLoading, setSetupLoading] = useState(false);

  // Handle Credentials Submit
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setAuthLoading(true);

    try {
      if (isLoginTab) {
        const res = await authService.login({ email, password });
        setShowSimulation(false); // Set to false when logging in
        login(res.data.token, res.data.user);
        setShowAuthModal(false);
        navigate('/');
      } else {
        const res = await authService.signup({
          email,
          password,
          name,
          role: 'admin'
        });
        setShowSimulation(false); // Set to false when logging in
        login(res.data.token, res.data.user);
        setShowAuthModal(false);
        navigate('/');
      }
      // Reset forms
      setEmail('');
      setPassword('');
      setName('');
    } catch (err: any) {
      const msg = getErrorMessage(err);
      setAuthError(msg);
      alert(msg);
    } finally {
      setAuthLoading(false);
    }
  };

  // Handle Mock OAuth Popup
  const handleMockOAuth = async (provider: 'google' | 'microsoft') => {
    setAuthError(null);
    setAuthLoading(true);

    // Simulate OAuth Popup
    const mockOAuthWindow = window.open(
      '',
      '_blank',
      'width=500,height=600,left=100,top=100,resizable=yes,scrollbars=yes'
    );

    if (!mockOAuthWindow) {
      setAuthError('Popup blocked by browser. Please allow popups.');
      setAuthLoading(false);
      return;
    }

    mockOAuthWindow.document.write(`
      <html>
        <head>
          <title>Sign in with ${provider === 'google' ? 'Google' : 'Microsoft'}</title>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
              background: #0f172a;
              color: #f8fafc;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              height: 100vh;
              margin: 0;
            }
            .card {
              background: #1e293b;
              border: 1px solid #334155;
              border-radius: 12px;
              padding: 32px;
              text-align: center;
              box-shadow: 0 10px 25px rgba(0,0,0,0.5);
              max-width: 380px;
            }
            h2 { margin-bottom: 8px; color: #fff; }
            p { color: #94a3b8; font-size: 14px; margin-bottom: 24px; }
            .btn {
              background: ${provider === 'google' ? '#2563eb' : '#059669'};
              color: white;
              border: none;
              padding: 12px 24px;
              font-size: 14px;
              font-weight: 600;
              border-radius: 6px;
              cursor: pointer;
              transition: all 0.2s;
              width: 100%;
            }
            .btn:hover { opacity: 0.9; transform: translateY(-1px); }
          </style>
        </head>
        <body>
          <div class="card">
            <h2>OAuth Simulation</h2>
            <p>You are authenticating through <strong>${provider === 'google' ? 'Google Account Services' : 'Microsoft Account Portal'}</strong> for testing.</p>
            <button class="btn" onclick="window.opener.postMessage({ type: 'OAUTH_SUCCESS', provider: '${provider}' }, '*'); window.close();">
              Authorize Account Access
            </button>
          </div>
        </body>
      </html>
    `);

    // Listener for popup response
    const handleMessage = async (event: MessageEvent) => {
      if (event.data && event.data.type === 'OAUTH_SUCCESS') {
        window.removeEventListener('message', handleMessage);
        const prov = event.data.provider;

        // Mock OAuth values
        const mockEmail = `${prov.toLowerCase()}_user@supplychain.ai`;
        const mockName = `${prov === 'google' ? 'Google' : 'Microsoft'} User`;
        const mockUid = `oauth-${prov.toLowerCase()}-${Math.random().toString(36).substr(2, 9)}`;

        try {
          const res = await authService.oauth({
            email: mockEmail,
            name: mockName,
            provider: prov,
            uid: mockUid
          });
          setShowSimulation(false); // Set to false when logging in
          login(res.data.token, res.data.user);
          setShowAuthModal(false);
          navigate('/');
        } catch (err: any) {
          const msg = getErrorMessage(err);
          setAuthError(msg);
          alert(msg);
        } finally {
          setAuthLoading(false);
        }
      }
    };

    window.addEventListener('message', handleMessage);
  };

  // Fetch Current Simulation variables
  const fetchSetupDetails = async () => {
    setShowSetupModal(true);
    setSetupLoading(true);
    try {
      const [simRes, dataRes] = await Promise.all([
        api.get('/simulation/state'),
        api.get('/data/status')
      ]);
      setSetupData({
        simulation: simRes.data,
        data: dataRes.data
      });
    } catch (e) {
      console.error('Error fetching setup details:', e);
      setSetupData({ error: 'Failed to connect to the simulation engine. Make sure the backend server is running.' });
    } finally {
      setSetupLoading(false);
    }
  };

  return (
    <div style={{ background: '#0a0e1a', minHeight: '100vh', paddingBottom: '80px', overflowX: 'hidden' }}>
      {/* Dynamic Glowing Background Effects */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '15%',
        width: '400px',
        height: '400px',
        background: 'rgba(99, 102, 241, 0.15)',
        borderRadius: '50%',
        filter: 'blur(100px)',
        pointerEvents: 'none',
        zIndex: 0
      }} />
      <div style={{
        position: 'absolute',
        top: '60%',
        right: '10%',
        width: '500px',
        height: '500px',
        background: 'rgba(139, 92, 246, 0.12)',
        borderRadius: '50%',
        filter: 'blur(120px)',
        pointerEvents: 'none',
        zIndex: 0
      }} />

      {/* Hero Header / Nav */}
      <nav style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '20px 8%',
        borderBottom: '1px solid rgba(148, 163, 184, 0.08)',
        backdropFilter: 'blur(10px)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        background: 'rgba(10, 14, 26, 0.8)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            background: 'var(--accent-gradient)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Zap size={18} color="white" />
          </div>
          <span style={{ fontWeight: 800, fontSize: '1.2rem', letterSpacing: '0.5px' }}>
            SUPPLYCHAIN<span style={{ color: 'var(--text-accent)' }}>AI</span>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={fetchSetupDetails}
            className="btn btn-secondary btn-sm"
            style={{ borderRadius: 'var(--radius-full)', border: '1px solid rgba(99, 102, 241, 0.3)' }}
          >
            <Settings size={14} />
            Test Simulation Setup
          </button>

          <button
            onClick={() => {
              setShowSimulation(true);
              navigate('/');
            }}
            className="btn btn-secondary btn-sm"
            style={{ borderRadius: 'var(--radius-full)', border: '1px solid rgba(99, 102, 241, 0.3)' }}
          >
            <Activity size={14} />
            Dashboard / Simulation
          </button>

          {isAuthenticated ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{
                background: 'var(--bg-tertiary)',
                padding: '4px 12px',
                borderRadius: 'var(--radius-full)',
                border: '1px solid var(--border)',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <div style={{ width: '8px', height: '8px', background: 'var(--success)', borderRadius: '50%' }} />
                <span>{user?.name}</span>
              </div>
              <button
                onClick={() => logout()}
                className="btn btn-danger btn-sm"
                style={{ padding: '6px 12px', borderRadius: 'var(--radius-md)' }}
              >
                Log Out
              </button>
            </div>
          ) : (
            <button
              onClick={() => {
                setIsLoginTab(true);
                setShowAuthModal(true);
              }}
              className="btn btn-primary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <LogIn size={14} />
              Sign In
            </button>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <header style={{
        padding: '120px 8% 80px 8%',
        textAlign: 'center',
        position: 'relative',
        zIndex: 10
      }}>
        <RevealWrapper>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: 'var(--success-bg)',
            color: 'var(--success)',
            padding: '6px 16px',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.8rem',
            fontWeight: 600,
            marginBottom: '24px',
            border: '1px solid rgba(34, 197, 94, 0.2)'
          }}>
            <Activity size={14} />
            v1.0.0 Autonomous Multi-Agent Orchestrator
          </div>
        </RevealWrapper>

        <RevealWrapper delay={0.1}>
          <h1 style={{
            fontSize: '3.5rem',
            fontWeight: 800,
            lineHeight: 1.2,
            maxWidth: '900px',
            margin: '0 auto 24px auto',
            letterSpacing: '-1px'
          }}>
            Orchestrate Global Supply Chains with{' '}
            <span style={{
              background: 'linear-gradient(135deg, #818cf8, #a78bfa, #c084fc)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Autonomous Agentic AI
            </span>
          </h1>
        </RevealWrapper>

        <RevealWrapper delay={0.2}>
          <p style={{
            color: 'var(--text-secondary)',
            fontSize: '1.15rem',
            maxWidth: '700px',
            margin: '0 auto 36px auto',
            lineHeight: 1.6
          }}>
            Move past static templates and reactive logistics. Empower demand forecasters, inventory managers, and supplier risk analysts to make real-time decisions collectively.
          </p>
        </RevealWrapper>

        <RevealWrapper delay={0.3}>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
            {isAuthenticated ? (
              <button
                onClick={() => navigate('/')}
                className="btn btn-primary btn-lg"
                style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                Go to Dashboard
                <ArrowRight size={18} />
              </button>
            ) : (
              <button
                onClick={() => {
                  setIsLoginTab(false);
                  setShowAuthModal(true);
                }}
                className="btn btn-primary btn-lg"
                style={{ display: 'flex', alignItems: 'center', gap: '10px' }}
              >
                Create Free Account
                <ArrowRight size={18} />
              </button>
            )}
          </div>
        </RevealWrapper>
      </header>

      {/* Business Impact Statistics Component */}
      <section style={{ padding: '40px 8%', position: 'relative', zIndex: 10 }}>
        <RevealWrapper>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '24px',
            maxWidth: '1200px',
            margin: '0 auto'
          }}>
            <div className="glass-card" style={{ textAlign: 'center', padding: '30px 20px', borderLeft: '4px solid var(--accent-primary)' }}>
              <div style={{ color: 'var(--accent-primary)', display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
                <TrendingUp size={36} />
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>30%</div>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600, marginTop: '8px' }}>Inventory Carry Savings</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>Continuous stockout optimization</div>
            </div>

            <div className="glass-card" style={{ textAlign: 'center', padding: '30px 20px', borderLeft: '4px solid var(--success)' }}>
              <div style={{ color: 'var(--success)', display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
                <Check size={36} />
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--success)' }}>25%</div>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600, marginTop: '8px' }}>OTD Rate Improvement</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>Dynamic primary & backup splits</div>
            </div>

            <div className="glass-card" style={{ textAlign: 'center', padding: '30px 20px', borderLeft: '4px solid var(--info)' }}>
              <div style={{ color: 'var(--info)', display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
                <Clock size={36} />
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--info)' }}>40%</div>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600, marginTop: '8px' }}>Faster Disruption Response</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>Predictive multi-week lead indicators</div>
            </div>

            <div className="glass-card" style={{ textAlign: 'center', padding: '30px 20px', borderLeft: '4px solid var(--warning)' }}>
              <div style={{ color: 'var(--warning)', display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
                <DollarSign size={36} />
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--warning)' }}>15%</div>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600, marginTop: '8px' }}>Procurement Cost Reduction</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>Autonomous contract parameters</div>
            </div>
          </div>
        </RevealWrapper>
      </section>

      {/* Challenge Section (Copywriting) */}
      <section style={{ padding: '100px 8% 60px 8%', position: 'relative', zIndex: 10 }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '60px' }}>
            <RevealWrapper>
              <div style={{
                background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.05), rgba(10, 14, 26, 0.8))',
                border: '1px solid rgba(239, 68, 68, 0.1)',
                padding: '48px',
                borderRadius: 'var(--radius-xl)',
                position: 'relative'
              }}>
                <div style={{
                  position: 'absolute',
                  top: '-24px',
                  left: '48px',
                  width: '48px',
                  height: '48px',
                  background: 'var(--danger-bg)',
                  border: '1px solid var(--danger)',
                  color: 'var(--danger)',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(239, 68, 68, 0.2)'
                }}>
                  <AlertTriangle size={24} />
                </div>
                <h2 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '20px', color: '#f8fafc' }}>
                  2. Dynamic supply chain orchestration
                </h2>
                <div style={{ borderBottom: '1px solid rgba(239, 68, 68, 0.15)', paddingBottom: '16px', marginBottom: '20px' }}>
                  <span style={{ textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px', color: 'var(--danger)' }}>
                    The Challenge
                  </span>
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: 1.7, textAlign: 'justify' }}>
                  Global supply chains are intricate networks with hundreds of interdependent variables that change constantly. Traditional supply chain management relies on historical data and periodic reviews, creating blind spots when disruptions occur. Supplier performance fluctuates due to capacity constraints, quality issues, or geopolitical factors that are difficult to predict and monitor in real-time. Demand forecasting struggles with seasonal variations, market trends, and external events that traditional models cannot anticipate accurately. Transportation costs shift based on fuel prices, route availability, and carrier capacity changes that occur daily or even hourly.
                </p>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: 1.7, marginTop: '16px', textAlign: 'justify' }}>
                  Inventory optimization presents a constant balancing act between carrying costs and stockout risks across multiple locations, with each decision impacting cash flow and customer satisfaction. Manual processes delay response to critical disruptions, often discovered weeks after impact begins, when mitigation options are limited and costs are exponential. Organizations lack visibility into tier-2 and tier-3 suppliers who may represent single points of failure, creating cascade effects that can shut down entire production lines without warning.
                </p>
              </div>
            </RevealWrapper>
          </div>
        </div>
      </section>

      {/* Solution Section (Copywriting) */}
      <section style={{ padding: '40px 8%', position: 'relative', zIndex: 10 }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <RevealWrapper>
            <div style={{
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(10, 14, 26, 0.8))',
              border: '1px solid rgba(99, 102, 241, 0.15)',
              padding: '48px',
              borderRadius: 'var(--radius-xl)',
              position: 'relative'
            }}>
              <div style={{
                position: 'absolute',
                top: '-24px',
                left: '48px',
                width: '48px',
                height: '48px',
                background: 'var(--info-bg)',
                border: '1px solid var(--accent-primary)',
                color: 'var(--text-accent)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.2)'
              }}>
                <Cpu size={24} />
              </div>
              <h2 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '20px', color: '#f8fafc' }}>
                Agentic AI Solution
              </h2>
              <div style={{ borderBottom: '1px solid rgba(99, 102, 241, 0.15)', paddingBottom: '16px', marginBottom: '20px' }}>
                <span style={{ textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px', color: 'var(--text-accent)' }}>
                  Intelligent Orchestration
                </span>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: 1.7, textAlign: 'justify', marginBottom: '24px' }}>
                Intelligent supply chain orchestration creates a self-managing network that continuously optimizes based on real-time global conditions. The system ingests data from suppliers, logistics partners, market indicators, weather systems, and geopolitical sources to make autonomous decisions that keep operations flowing smoothly.
              </p>

              {/* Specific features cards grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '24px',
                marginTop: '32px'
              }}>
                <div style={{ background: 'rgba(10, 14, 26, 0.5)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '8px', color: 'var(--text-primary)' }}>Predictive Disruption Modeling</h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Identifies potential issues two to six weeks in advance by analyzing patterns in supplier communications, regional economic indicators, and global event impacts.
                  </p>
                </div>
                <div style={{ background: 'rgba(10, 14, 26, 0.5)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '8px', color: 'var(--text-primary)' }}>Automated Supplier Diversification</h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Maintains relationships with backup providers through dynamic qualification and onboarding processes that ensure alternatives are always available when needed.
                  </p>
                </div>
                <div style={{ background: 'rgba(10, 14, 26, 0.5)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '8px', color: 'var(--text-primary)' }}>Real-time Route Optimization</h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Continuously evaluates transportation options considering costs, delivery windows, and risk factors to ensure optimal logistics decisions are made automatically.
                  </p>
                </div>
                <div style={{ background: 'rgba(10, 14, 26, 0.5)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '8px', color: 'var(--text-primary)' }}>Autonomous Contract Negotiation</h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Operates within predefined parameters for emergency procurement, enabling rapid response to supply shortages without waiting for human approval processes.
                  </p>
                </div>
                <div style={{ background: 'rgba(10, 14, 26, 0.5)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '8px', color: 'var(--text-primary)' }}>Continuous Inventory Optimization</h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Uses demand predictions, storage costs, and supplier lead times to maintain optimal stock levels automatically across all locations.
                  </p>
                </div>
                <div style={{ background: 'rgba(10, 14, 26, 0.5)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                  <h4 style={{ fontWeight: 600, marginBottom: '8px', color: 'var(--text-primary)' }}>Self-healing Supply Networks</h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Activates backup suppliers and alternative routes automatically when disruptions are detected, minimizing impact on production schedules.
                  </p>
                </div>
              </div>
            </div>
          </RevealWrapper>
        </div>
      </section>

      {/* Case Study Section */}
      <section style={{ padding: '60px 8% 100px 8%', position: 'relative', zIndex: 10 }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <RevealWrapper>
            <div style={{
              background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.03), rgba(10, 14, 26, 0.8))',
              border: '1px solid rgba(34, 197, 94, 0.1)',
              padding: '48px',
              borderRadius: 'var(--radius-xl)',
              position: 'relative'
            }}>
              <div style={{
                position: 'absolute',
                top: '-24px',
                left: '48px',
                width: '48px',
                height: '48px',
                background: 'var(--success-bg)',
                border: '1px solid var(--success)',
                color: 'var(--success)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(34, 197, 94, 0.2)'
              }}>
                <Globe size={24} />
              </div>
              <h2 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '20px', color: '#f8fafc' }}>
                Real-World Application
              </h2>
              <div style={{ borderBottom: '1px solid rgba(34, 197, 94, 0.15)', paddingBottom: '16px', marginBottom: '20px' }}>
                <span style={{ textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px', color: 'var(--success)' }}>
                  Case Study
                </span>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', lineHeight: 1.8, textAlign: 'justify', fontStyle: 'italic' }}>
                "A global electronics manufacturer implemented agentic AI that monitors 200+ suppliers across 15 countries. When semiconductor shortages emerged in Southeast Asia, the system automatically identified alternative suppliers, negotiated emergency contracts, and rerouted shipments – all before human managers were aware of the issue."
              </p>
            </div>
          </RevealWrapper>
        </div>
      </section>

      {/* Auth Modal Overlay */}
      {showAuthModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(5, 7, 13, 0.85)',
          backdropFilter: 'blur(16px)',
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div className="glass-card" style={{
            width: '100%',
            maxWidth: '440px',
            border: '1px solid var(--border-hover)',
            boxShadow: '0 20px 50px rgba(0,0,0,0.6)'
          }}>
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Zap size={18} color="var(--accent-primary)" />
                <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>Supply Chain AI Portal</span>
              </div>
              <button
                onClick={() => setShowAuthModal(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                &times;
              </button>
            </div>

            {/* Modal Tabs */}
            <div style={{ display: 'flex', background: 'var(--bg-tertiary)', padding: '4px', borderRadius: 'var(--radius-md)', marginBottom: '24px' }}>
              <button
                onClick={() => { setIsLoginTab(true); setAuthError(null); }}
                style={{
                  flex: 1,
                  padding: '8px',
                  background: isLoginTab ? 'var(--accent-gradient)' : 'transparent',
                  color: isLoginTab ? 'white' : 'var(--text-secondary)',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Sign In
              </button>
              <button
                onClick={() => { setIsLoginTab(false); setAuthError(null); }}
                style={{
                  flex: 1,
                  padding: '8px',
                  background: !isLoginTab ? 'var(--accent-gradient)' : 'transparent',
                  color: !isLoginTab ? 'white' : 'var(--text-secondary)',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Sign Up
              </button>
            </div>

            {/* Auth Form */}
            <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {!isLoginTab && (
                <div>
                  <label className="label">Full Name</label>
                  <div style={{ position: 'relative' }}>
                    <User size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
                    <input
                      type="text"
                      className="input"
                      style={{ paddingLeft: '40px' }}
                      placeholder="Alex Mercer"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required={!isLoginTab}
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="label">Email Address</label>
                <div style={{ position: 'relative' }}>
                  <Mail size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
                  <input
                    type="email"
                    className="input"
                    style={{ paddingLeft: '40px' }}
                    placeholder="alex@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Password</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
                  <input
                    type="password"
                    className="input"
                    style={{ paddingLeft: '40px' }}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>



              {authError && (
                <div style={{
                  background: 'var(--danger-bg)',
                  border: '1px solid var(--danger)',
                  color: 'var(--danger)',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.8rem'
                }}>
                  {authError}
                </div>
              )}

              <button
                type="submit"
                disabled={authLoading}
                className="btn btn-primary"
                style={{ width: '100%', marginTop: '8px' }}
              >
                {authLoading ? 'Verifying Credentials...' : isLoginTab ? 'Sign In to Dashboard' : 'Create Account'}
              </button>
            </form>

            {/* OAuth Dividers */}
            <div style={{ display: 'flex', alignItems: 'center', margin: '20px 0', gap: '10px' }}>
              <div style={{ flex: 1, height: '1px', background: 'var(--border)' }} />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>or sign in with</span>
              <div style={{ flex: 1, height: '1px', background: 'var(--border)' }} />
            </div>

            {/* OAuth Buttons */}
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => handleMockOAuth('google')}
                disabled={authLoading}
                className="btn btn-secondary"
                style={{ flex: 1, fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '8px 12px' }}
              >
                <Globe size={14} color="#4285F4" />
                Google
              </button>
              <button
                onClick={() => handleMockOAuth('microsoft')}
                disabled={authLoading}
                className="btn btn-secondary"
                style={{ flex: 1, fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '8px 12px' }}
              >
                <Globe size={14} color="#00A4EF" />
                Microsoft
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Simulation Setup Inspector Modal */}
      {showSetupModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(5, 7, 13, 0.85)',
          backdropFilter: 'blur(16px)',
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div className="glass-card" style={{
            width: '100%',
            maxWidth: '680px',
            border: '1px solid var(--border-hover)',
            boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
            maxHeight: '90vh',
            overflowY: 'auto'
          }}>
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Settings size={20} color="var(--accent-primary)" />
                <span style={{ fontWeight: 700, fontSize: '1.2rem' }}>Current Simulation Setup Variables</span>
              </div>
              <button
                onClick={() => setShowSetupModal(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.5rem' }}
              >
                &times;
              </button>
            </div>

            {setupLoading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px' }}>
                <div className="spinner" style={{ marginBottom: '16px' }} />
                <span>Reading active configurations from backend...</span>
              </div>
            ) : setupData?.error ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--danger)', background: 'var(--danger-bg)', borderRadius: 'var(--radius-md)' }}>
                {setupData.error}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {/* Simulation Section */}
                <div style={{ background: 'var(--bg-tertiary)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '12px', color: 'var(--text-accent)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Active Simulation State
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 24px', fontSize: '0.85rem' }}>
                    <div>
                      <span style={{ color: 'var(--text-secondary)' }}>Status: </span>
                      <strong className={`badge ${setupData?.simulation?.status === 'running' ? 'badge-success' : 'badge-info'}`}>
                        {setupData?.simulation?.status || 'idle'}
                      </strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-secondary)' }}>Elapsed Days: </span>
                      <strong>{setupData?.simulation?.days_elapsed || 0} days</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-secondary)' }}>Base Daily Demand: </span>
                      <strong>{setupData?.simulation?.base_demand || 1000} units</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-secondary)' }}>Disruptions Generated: </span>
                      <strong>{setupData?.simulation?.disruptions_occurred || 0}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-secondary)' }}>Seed Configuration: </span>
                      <strong>{setupData?.simulation?.seed || 42}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-secondary)' }}>Active Lead Time: </span>
                      <strong>{setupData?.simulation?.lead_time_days || 2} days</strong>
                    </div>
                  </div>
                </div>

                {/* Datasets Section */}
                <div style={{ background: 'var(--bg-tertiary)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '12px', color: 'var(--text-accent)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Loaded Ingestion Sources
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 24px', fontSize: '0.85rem' }}>
                    <div>
                      <span style={{ color: 'var(--text-secondary)' }}>Ingested Mode: </span>
                      <strong>{setupData?.data?.mode?.toUpperCase() || 'SIMULATION'}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-secondary)' }}>Data Source Configuration: </span>
                      <strong>{setupData?.data?.data_source?.toUpperCase() || 'MANUAL'}</strong>
                    </div>
                  </div>

                  {setupData?.data?.loaded_datasets && setupData.data.loaded_datasets.length > 0 ? (
                    <div style={{ marginTop: '16px' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Active Datasets:</span>
                      <ul style={{ margin: '6px 0 0 0', paddingLeft: '20px', fontSize: '0.85rem' }}>
                        {setupData.data.loaded_datasets.map((name: string) => (
                          <li key={name} style={{ color: 'var(--text-primary)', marginBottom: '4px' }}>
                            {name} (Loaded)
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <div style={{
                      marginTop: '12px',
                      padding: '8px 12px',
                      background: 'rgba(99, 102, 241, 0.05)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.8rem',
                      color: 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                      <FileText size={14} />
                      No uploaded CSV files found. Using standard manual dataset buffer.
                    </div>
                  )}
                </div>

                {/* Agent Decisions Logic Setup */}
                <div style={{ background: 'var(--bg-tertiary)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '12px', color: 'var(--text-accent)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    AI Agent Decision Configurations
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.8rem' }}>
                    <div style={{ paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <strong>1. Demand Forecaster:</strong>
                      <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>
                        Generates forecast using Holt-Winters ML models. Uses safety stock thresholds. Strictly does not issue replenishment orders.
                      </div>
                    </div>
                    <div style={{ paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <strong>2. Inventory Optimizer:</strong>
                      <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>
                        Controls reordering calculations. Computes replenishment order quantities using Economic Order Quantity (EOQ) algorithms.
                      </div>
                    </div>
                    <div style={{ paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <strong>3. Supplier Risk Agent:</strong>
                      <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>
                        Predicts disruption probabilities. Overrides supplier risk to <strong>CRITICAL</strong> when individual metrics (defect rate / delays) exceed 75%.
                      </div>
                    </div>
                    <div>
                      <strong>4. Coordinator:</strong>
                      <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>
                        Aggregates details. Automatically rejects single-supplier recommendations and triggers **split procurement** when Supplier Risk is classified as CRITICAL.
                      </div>
                    </div>
                  </div>
                </div>

                {/* Close Button */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                  <button onClick={() => setShowSetupModal(false)} className="btn btn-primary btn-sm">
                    Close Setup Inspector
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
