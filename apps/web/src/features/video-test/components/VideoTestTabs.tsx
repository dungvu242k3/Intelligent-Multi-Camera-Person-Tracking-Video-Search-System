import { memo, useMemo } from 'react';
import { FileVideo, Link } from 'lucide-react';
import { useTranslation } from '../../../shared/hooks/useTranslation.ts';
import { VideoTestTab } from '../../../shared/types/videoTest.ts';
import { videoTestPageStyles as styles } from '../VideoTestPage.styles.ts';

interface VideoTestTabsProps {
  activeTab: VideoTestTab;
  onTabChange: (tab: VideoTestTab) => void;
}

function VideoTestTabs({ activeTab, onTabChange }: VideoTestTabsProps) {
  const { t } = useTranslation();
  const uploadActive = activeTab === VideoTestTab.Upload;

  const uploadTabStyle = useMemo(
    () => ({
      ...styles.tabBtn,
      borderBottomColor: uploadActive ? 'var(--color-primary)' : 'transparent',
      color: uploadActive ? 'var(--color-primary)' : 'var(--color-text-secondary)',
    }),
    [uploadActive]
  );

  const urlTabStyle = useMemo(
    () => ({
      ...styles.tabBtn,
      borderBottomColor: uploadActive ? 'transparent' : 'var(--color-primary)',
      color: uploadActive ? 'var(--color-text-secondary)' : 'var(--color-primary)',
    }),
    [uploadActive]
  );

  return (
    <div style={styles.tabsHeader}>
      <button type="button" onClick={() => onTabChange(VideoTestTab.Upload)} style={uploadTabStyle}>
        <FileVideo size={16} />
        <span>{t('vtest.tabUpload')}</span>
      </button>
      <button type="button" onClick={() => onTabChange(VideoTestTab.Url)} style={urlTabStyle}>
        <Link size={16} />
        <span>{t('vtest.tabUrl')}</span>
      </button>
    </div>
  );
}

export default memo(VideoTestTabs);
