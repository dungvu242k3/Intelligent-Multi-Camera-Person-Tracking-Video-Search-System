import { create } from 'zustand';
import { Locale, i18nDict } from '../utils/i18n.ts';

interface I18nState {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: keyof typeof i18nDict['en'], replacements?: Record<string, string | number>) => string;
}

export const useI18nStore = create<I18nState>((set, get) => ({
  locale: (localStorage.getItem('mcpt_locale') as Locale) || 'en',
  
  setLocale: (locale: Locale) => {
    localStorage.setItem('mcpt_locale', locale);
    set({ locale });
  },

  t: (key, replacements) => {
    const { locale } = get();
    let text = i18nDict[locale]?.[key] || i18nDict['en']?.[key] || String(key);
    
    // Dynamic string replacements: e.g. replacing {secs} with numerical value
    if (replacements) {
      Object.entries(replacements).forEach(([k, val]) => {
        text = text.replace(`{${k}}`, String(val));
      });
    }
    
    return text;
  }
}));
