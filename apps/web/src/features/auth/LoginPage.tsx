import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, ShieldAlert, Globe, Eye, EyeOff, Activity } from 'lucide-react';
import { useTranslation } from '../../shared/hooks/useTranslation.ts';
import { useAuthStore } from '../../shared/stores/authStore.ts';
import axiosInstance from '../../shared/utils/axiosInstance.ts';

export default function LoginPage() {
  const { t, locale, setLocale } = useTranslation();
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

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

    setIsLoading(true);
    try {
      const res = await axiosInstance.post('/auth/login', {
        email: emailTrimmed,
        password
      });

      // Succeeds -> Write tokens to store
      login(res.data.access_token, res.data.refresh_token);
      navigate('/', { replace: true });
    } catch (err: any) {
      if (err.response) {
        const status = err.response.status;
        if (status === 401) {
          setError(t('error.401'));
        } else if (status === 423) {
          setError(t('error.429')); // Show lockout/rate limit
        } else if (status === 429) {
          setError(t('error.429'));
        } else {
          setError(t('error.500'));
        }
      } else {
        setError(t('error.generic'));
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Floating Language Toggler */}
      <button 
        type="button" 
        onClick={toggleLanguage} 
        style={styles.langBtn}
        aria-label="Toggle language"
      >
        <Globe size={16} />
        <span>{locale === 'en' ? 'EN' : 'VI'}</span>
      </button>

      {/* Login Card */}
      <div className="card" style={styles.card}>
        {/* Header Logo */}
        <div style={styles.header}>
          <div style={styles.logoWrapper}>
            <Activity size={32} color="var(--color-primary)" className="pulse-red-glow" />
          </div>
          <h1 style={styles.title}>{t('auth.loginTitle')}</h1>
          <p style={styles.subtitle}>{t('auth.loginSubtitle')}</p>
        </div>

        {/* Errors Block */}
        {error && (
          <div style={styles.errorBanner}>
            <ShieldAlert size={18} color="var(--color-danger)" />
            <span style={styles.errorText}>{error}</span>
          </div>
        )}

        {/* Inputs Form */}
        <form onSubmit={handleLoginSubmit} style={styles.form}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>{t('auth.email')}</label>
            <div style={styles.inputWrapper}>
              <Mail size={16} color="var(--color-text-secondary)" style={styles.inputIcon} />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@mcpt.secure"
                disabled={isLoading}
                style={styles.input}
                required
              />
            </div>
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>{t('auth.password')}</label>
            <div style={styles.inputWrapper}>
              <Lock size={16} color="var(--color-text-secondary)" style={styles.inputIcon} />
              <input 
                type={showPassword ? 'text' : 'password'} 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={isLoading}
                style={styles.input}
                required
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={styles.eyeBtn}
                aria-label="Toggle password visibility"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="btn-primary" 
            style={styles.submitBtn}
          >
            {isLoading ? '...' : t('auth.btnSignIn')}
          </button>
        </form>

        {/* Register Redirect Redirect */}
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
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100vw',
    height: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0b0f19', // Dark Cyber Base
    position: 'relative',
    fontFamily: 'inherit',
    overflow: 'hidden',
  },
  langBtn: {
    position: 'absolute',
    top: '24px',
    right: '24px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    backgroundColor: 'rgba(30, 41, 59, 0.5)',
    border: '1px solid var(--color-border)',
    borderRadius: '6px',
    color: 'var(--color-text)',
    padding: '8px 12px',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 500,
    transition: 'all 200ms ease',
  },
  card: {
    width: '100%',
    maxWidth: '440px',
    padding: '40px',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
    backdropFilter: 'blur(12px)',
    backgroundColor: 'rgba(15, 23, 42, 0.75)', // Glassmorphism Slate
    border: '1px solid rgba(255, 255, 255, 0.05)',
  },
  header: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    gap: '12px',
  },
  logoWrapper: {
    width: '64px',
    height: '64px',
    borderRadius: '16px',
    backgroundColor: 'rgba(59, 130, 246, 0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '1px solid rgba(59, 130, 246, 0.2)',
    marginBottom: '8px',
  },
  title: {
    fontSize: '22px',
    fontWeight: 700,
    color: 'var(--color-text)',
    margin: 0,
    letterSpacing: '-0.025em',
  },
  subtitle: {
    fontSize: '13px',
    color: 'var(--color-text-secondary)',
    margin: 0,
    lineHeight: 1.5,
  },
  errorBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    backgroundColor: 'rgba(239, 68, 68, 0.06)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    borderRadius: '8px',
    padding: '12px 16px',
  },
  errorText: {
    fontSize: '13px',
    color: 'var(--color-danger)',
    fontWeight: 500,
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--color-text)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
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
    backgroundColor: 'rgba(30, 41, 59, 0.4)',
    border: '1px solid var(--color-border)',
    borderRadius: '8px',
    color: 'var(--color-text)',
    padding: '12px 40px 12px 40px',
    fontSize: '14px',
    outline: 'none',
    transition: 'all 200ms ease',
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
    marginTop: '8px',
  },
  footer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '6px',
    fontSize: '13px',
    marginTop: '8px',
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
