import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, ShieldAlert, Globe, Eye, EyeOff, Cpu, Server, Database, Activity } from 'lucide-react';
import { useTranslation } from '../../shared/hooks/useTranslation.ts';
import { useAuthStore } from '../../shared/stores/authStore.ts';
import axiosInstance, { isHttpClientError } from '../../shared/utils/axiosInstance.ts';

export default function LoginPage() {
  const { t, locale, setLocale } = useTranslation();
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const loginRequestRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      loginRequestRef.current?.abort();
    };
  }, []);

  const toggleLanguage = () => {
    setLocale(locale === 'en' ? 'vi' : 'en');
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const emailTrimmed = email.trim();
    if (!emailTrimmed || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrimmed)) {
      setError(t('auth.errEmail'));
      return;
    }

    if (password.length < 6) {
      setError(t('auth.errPassword'));
      return;
    }

    loginRequestRef.current?.abort();
    const controller = new AbortController();
    loginRequestRef.current = controller;
    setIsLoading(true);
    try {
      const res = await axiosInstance.post('/auth/login', {
        email: emailTrimmed,
        password
      }, {
        signal: controller.signal,
      });

      login(res.data.access_token);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      if (controller.signal.aborted) {
        return;
      }

      if (isHttpClientError(err) && err.response) {
        const { status } = err.response;
        if (status === 401) {
          setError(t('error.401'));
        } else if (status === 423) {
          setError(t('error.429'));
        } else if (status === 429) {
          setError(t('error.429'));
        } else {
          setError(t('error.500'));
        }
      } else {
        setError(t('error.generic'));
      }
    } finally {
      if (!controller.signal.aborted) {
        setIsLoading(false);
      }
      if (loginRequestRef.current === controller) {
        loginRequestRef.current = null;
      }
    }
  };

  return (
    <div style={styles.container}>
      {/* Background Image with Dark Overlay */}
      <div style={styles.bgImage} />
      <div style={styles.bgOverlay} />

      {/* Floating Language Toggler */}
      <button 
        type="button" 
        onClick={toggleLanguage} 
        style={styles.langBtn}
        aria-label="Toggle language"
      >
        <Globe size={14} color="var(--color-primary)" />
        <span>{locale === 'en' ? 'EN' : 'VI'}</span>
      </button>

      {/* Main Split Panel Layout */}
      <div style={styles.loginWrapper}>
        {/* Left Side: System Telemetry Info (Hidden on mobile) */}
        <div style={styles.telemetryPanel}>
          <div style={styles.telemetryHeader}>
            <Activity size={18} color="var(--color-primary)" className="pulse-red-glow" />
            <span style={styles.telemetryTitle}>Intelligent Surveillance System</span>
          </div>

          <p style={styles.telemetryDesc}>
            Access control terminal for Multi-Camera Person Tracking & ReID query pipeline. Authorized operators only.
          </p>

          <div style={styles.telemetryGrid}>
            <div style={styles.telemetryCard}>
              <Cpu size={16} color="var(--color-primary)" />
              <div>
                <div style={styles.telLabel}>GStreamer Inference</div>
                <div style={styles.telVal}>30 FPS / GPU</div>
              </div>
            </div>
            <div style={styles.telemetryCard}>
              <Server size={16} color="var(--color-secondary)" />
              <div>
                <div style={styles.telLabel}>Active Streams</div>
                <div style={styles.telVal}>4 Channels</div>
              </div>
            </div>
            <div style={styles.telemetryCard}>
              <Database size={16} color="var(--color-cta)" />
              <div>
                <div style={styles.telLabel}>Qdrant Vectors</div>
                <div style={styles.telVal}>1,024 Index</div>
              </div>
            </div>
          </div>

          <div style={styles.systemStatus}>
            <span style={styles.statusPulse} />
            <span style={styles.statusText}>Operator Terminal SecOps: Active (256-bit SSL)</span>
          </div>
        </div>

        {/* Right Side: Glassmorphism Login Card */}
        <div className="card" style={styles.card}>
          {/* Header Logo */}
          <div style={styles.header}>
            <div style={styles.logoWrapper}>
              <Activity size={28} color="var(--color-primary)" className="pulse-red-glow" />
            </div>
            <h1 style={styles.title}>{t('auth.loginTitle')}</h1>
            <p style={styles.subtitle}>{t('auth.loginSubtitle')}</p>
          </div>

          {/* Errors Block */}
          {error && (
            <div style={styles.errorBanner} role="alert" id="login-error">
              <ShieldAlert size={16} color="var(--color-danger)" style={{ flexShrink: 0 }} />
              <span style={styles.errorText}>{error}</span>
            </div>
          )}

          {/* Inputs Form */}
          <form onSubmit={handleLoginSubmit} style={styles.form}>
            <div style={styles.inputGroup}>
              <label htmlFor="login-email" style={styles.label}>{t('auth.email')}</label>
              <div style={styles.inputWrapper}>
                <Mail size={16} color="var(--color-text-secondary)" style={styles.inputIcon} />
                <input 
                  id="login-email"
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="operator@mcpt.secure"
                  disabled={isLoading}
                  aria-invalid={!!error}
                  aria-describedby={error ? 'login-error' : undefined}
                  style={styles.input}
                  required
                />
              </div>
            </div>

            <div style={styles.inputGroup}>
              <label htmlFor="login-password" style={styles.label}>{t('auth.password')}</label>
              <div style={styles.inputWrapper}>
                <Lock size={16} color="var(--color-text-secondary)" style={styles.inputIcon} />
                <input 
                  id="login-password"
                  type={showPassword ? 'text' : 'password'} 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={isLoading}
                  aria-invalid={!!error}
                  aria-describedby={error ? 'login-error' : undefined}
                  style={styles.input}
                  required
                />
                <button 
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={styles.eyeBtn}
                  aria-label="Toggle password visibility"
                  aria-pressed={showPassword}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              aria-busy={isLoading}
              className="btn-primary" 
              style={styles.submitBtn}
            >
              {isLoading ? 'Authenticating Operator...' : t('auth.btnSignIn')}
            </button>
          </form>

          {/* Register Redirect */}
          <div style={styles.footer}>
            <span style={styles.footerText}>{t('auth.noAccount')}</span>
            <button 
              type="button" 
              onClick={() => navigate('/register')}
              style={styles.registerLink}
            >
              {t('auth.btnRegister')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100vw',
    height: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    fontFamily: 'inherit',
    overflow: 'hidden',
    backgroundColor: '#05070c',
  },
  bgImage: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundImage: 'url("/control_room_bg.png")',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    filter: 'blur(3px) brightness(0.6)',
    zIndex: 1,
  },
  bgOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'radial-gradient(circle at center, rgba(15, 23, 42, 0.4) 0%, rgba(5, 7, 12, 0.95) 100%)',
    zIndex: 2,
  },
  langBtn: {
    position: 'absolute',
    top: '24px',
    right: '24px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--color-text)',
    padding: '8px 14px',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 600,
    fontFamily: 'var(--font-heading)',
    zIndex: 10,
    transition: 'all 200ms ease',
    boxShadow: 'var(--shadow-sm)',
  },
  loginWrapper: {
    display: 'flex',
    width: '100%',
    maxWidth: '920px',
    height: '560px',
    borderRadius: 'var(--radius-xl)',
    overflow: 'hidden',
    border: '1px solid var(--color-border)',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
    zIndex: 5,
    backdropFilter: 'blur(10px)',
  },
  telemetryPanel: {
    flex: 1.1,
    backgroundColor: 'rgba(15, 23, 42, 0.7)',
    padding: '40px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    borderRight: '1px solid var(--color-border)',
  },
  telemetryHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '16px',
  },
  telemetryTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  telemetryDesc: {
    fontSize: '13px',
    color: 'var(--color-text-secondary)',
    lineHeight: 1.6,
    marginBottom: '32px',
  },
  telemetryGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    marginBottom: '40px',
  },
  telemetryCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '14px',
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: 'var(--radius-md)',
    padding: '12px 16px',
  },
  telLabel: {
    fontSize: '11px',
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-heading)',
    textTransform: 'uppercase',
  },
  telVal: {
    fontSize: '14px',
    fontWeight: 600,
    color: 'var(--color-text)',
    marginTop: '2px',
  },
  systemStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginTop: 'auto',
  },
  statusPulse: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    backgroundColor: 'var(--color-success)',
    animation: 'pulse 1.5s infinite ease-in-out',
  },
  statusText: {
    fontSize: '11px',
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-heading)',
  },
  card: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.85)',
    padding: '40px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    gap: '20px',
    borderRadius: 0,
    border: 'none',
  },
  header: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    gap: '8px',
  },
  logoWrapper: {
    width: '54px',
    height: '54px',
    borderRadius: 'var(--radius-md)',
    backgroundColor: 'rgba(59, 130, 246, 0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '1px solid rgba(59, 130, 246, 0.2)',
    marginBottom: '4px',
  },
  title: {
    fontSize: '20px',
    fontWeight: 700,
    color: 'var(--color-text)',
    margin: 0,
    fontFamily: 'var(--font-heading)',
  },
  subtitle: {
    fontSize: '12px',
    color: 'var(--color-text-secondary)',
    margin: 0,
    lineHeight: 1.5,
  },
  errorBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    backgroundColor: 'var(--color-danger-bg)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    borderRadius: 'var(--radius-md)',
    padding: '10px 14px',
  },
  errorText: {
    fontSize: '12px',
    color: 'var(--color-danger)',
    fontWeight: 500,
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    fontSize: '11px',
    fontWeight: 600,
    color: 'var(--color-text-secondary)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    fontFamily: 'var(--font-heading)',
  },
  inputWrapper: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  inputIcon: {
    position: 'absolute',
    left: '14px',
  },
  input: {
    width: '100%',
    backgroundColor: 'rgba(15, 23, 42, 0.5)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--color-text)',
    padding: '12px 40px',
    fontSize: '14px',
    outline: 'none',
    transition: 'all 150ms ease',
    fontFamily: 'var(--font-body)',
  },
  eyeBtn: {
    position: 'absolute',
    right: '14px',
    background: 'none',
    border: 'none',
    color: 'var(--color-text-secondary)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    padding: 0,
  },
  submitBtn: {
    width: '100%',
    padding: '12px',
    fontSize: '14px',
    fontWeight: 600,
    marginTop: '6px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: 'var(--font-heading)',
  },
  footer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '6px',
    fontSize: '13px',
    marginTop: '4px',
  },
  footerText: {
    color: 'var(--color-text-secondary)',
  },
  registerLink: {
    background: 'none',
    border: 'none',
    color: 'var(--color-primary)',
    fontWeight: 600,
    cursor: 'pointer',
    padding: 0,
    textDecoration: 'underline',
  },
};
