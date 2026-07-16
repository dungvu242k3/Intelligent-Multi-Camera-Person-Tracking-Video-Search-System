import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, ShieldAlert, Globe, Eye, EyeOff, User, CheckCircle } from 'lucide-react';
import { useTranslation } from '../../shared/hooks/useTranslation.ts';
import axiosInstance from '../../shared/utils/axiosInstance.ts';

export default function RegisterPage() {
  const { t, locale, setLocale } = useTranslation();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const toggleLanguage = () => {
    setLocale(locale === 'en' ? 'vi' : 'en');
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const nameTrimmed = fullName.trim();
    if (!nameTrimmed) {
      setError(t('auth.errName'));
      return;
    }

    const emailTrimmed = email.trim();
    if (!emailTrimmed || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrimmed)) {
      setError(t('auth.errEmail'));
      return;
    }

    if (password.length < 6) {
      setError(t('auth.errPassword'));
      return;
    }

    if (password !== confirmPassword) {
      setError(locale === 'en' ? 'Passwords do not match.' : 'Mật khẩu xác nhận không trùng khớp.');
      return;
    }

    setIsLoading(true);
    try {
      await axiosInstance.post('/auth/register', {
        email: emailTrimmed,
        password,
        full_name: nameTrimmed,
        role_id: 2 // Hardcoded Operator role (Production protection layer)
      });

      setSuccess(t('auth.successRegister'));
      setTimeout(() => {
        navigate('/login');
      }, 1500);
    } catch (err: any) {
      if (err.response) {
        const status = err.response.status;
        if (status === 400) {
          setError(locale === 'en' ? 'Email address is already registered.' : 'Địa chỉ email này đã được đăng ký.');
        } else {
          setError(t('error.500'));
        }
      } else {
        setError(t('error.generic'));
      }
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

      {/* Register Card */}
      <div className="card" style={styles.card}>
        {/* Header Logo */}
        <div style={styles.header}>
          <div style={styles.logoWrapper}>
            <User size={32} color="var(--color-primary)" />
          </div>
          <h1 style={styles.title}>{t('auth.registerTitle')}</h1>
          <p style={styles.subtitle}>{t('auth.registerSubtitle')}</p>
        </div>

        {/* Success Banner */}
        {success && (
          <div style={styles.successBanner}>
            <CheckCircle size={18} color="var(--color-success)" />
            <span style={styles.successText}>{success}</span>
          </div>
        )}

        {/* Errors Block */}
        {error && (
          <div style={styles.errorBanner}>
            <ShieldAlert size={18} color="var(--color-danger)" />
            <span style={styles.errorText}>{error}</span>
          </div>
        )}

        {/* Inputs Form */}
        <form onSubmit={handleRegisterSubmit} style={styles.form}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>{t('auth.fullName')}</label>
            <div style={styles.inputWrapper}>
              <User size={16} color="var(--color-text-secondary)" style={styles.inputIcon} />
              <input 
                type="text" 
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                disabled={isLoading || !!success}
                style={styles.input}
                required
              />
            </div>
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>{t('auth.email')}</label>
            <div style={styles.inputWrapper}>
              <Mail size={16} color="var(--color-text-secondary)" style={styles.inputIcon} />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@mcpt.secure"
                disabled={isLoading || !!success}
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
                disabled={isLoading || !!success}
                style={styles.input}
                required
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={styles.eyeBtn}
                aria-label="Toggle password"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>{locale === 'en' ? 'Confirm Password' : 'Xác nhận mật khẩu'}</label>
            <div style={styles.inputWrapper}>
              <Lock size={16} color="var(--color-text-secondary)" style={styles.inputIcon} />
              <input 
                type={showConfirmPassword ? 'text' : 'password'} 
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                disabled={isLoading || !!success}
                style={styles.input}
                required
              />
              <button 
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                style={styles.eyeBtn}
                aria-label="Toggle confirm password"
              >
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button 
            type="submit" 
            disabled={isLoading || !!success}
            className="btn-primary" 
            style={styles.submitBtn}
          >
            {isLoading ? '...' : t('auth.btnRegister')}
          </button>
        </form>

        {/* Redirect back to Login */}
        <div style={styles.footer}>
          <span style={styles.footerText}>{t('auth.hasAccount')}</span>
          <button 
            type="button" 
            onClick={() => navigate('/login')}
            style={styles.loginLink}
          >
            {t('auth.btnSignIn')}
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
    backgroundColor: '#0b0f19',
    position: 'relative',
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
  },
  card: {
    width: '100%',
    maxWidth: '440px',
    padding: '40px',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
    backdropFilter: 'blur(12px)',
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
  },
  header: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    gap: '10px',
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
    marginBottom: '4px',
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
  successBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    backgroundColor: 'rgba(16, 185, 129, 0.06)',
    border: '1px solid rgba(16, 185, 129, 0.2)',
    borderRadius: '8px',
    padding: '12px 16px',
  },
  successText: {
    fontSize: '13px',
    color: 'var(--color-success)',
    fontWeight: 500,
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
    gap: '16px',
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
    marginTop: '6px',
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
  loginLink: {
    background: 'none',
    border: 'none',
    color: 'var(--color-primary)',
    fontWeight: 600,
    cursor: 'pointer',
    padding: 0,
    textDecoration: 'underline',
  },
};
