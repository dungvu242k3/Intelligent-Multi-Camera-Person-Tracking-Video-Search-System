import { useI18nStore } from '../stores/i18nStore.ts';

export function useTranslation() {
  const { locale, setLocale, t } = useI18nStore();
  return { locale, setLocale, t };
}
