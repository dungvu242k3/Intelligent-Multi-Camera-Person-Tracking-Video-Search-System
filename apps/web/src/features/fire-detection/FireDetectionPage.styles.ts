import React from 'react';

export const fireDetectionPageStyles: Record<string, React.CSSProperties> = {
  page: {
    width: '100%',
  },
  contentLayout: {
    display: 'flex',
    paddingRight: '320px',
  },
  mainPanel: {
    flex: 1,
    padding: '24px 32px',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    maxWidth: '900px',
    margin: '0 auto',
  },
  titleBlock: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    alignItems: 'flex-start',
  },
  titleGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  title: {
    fontSize: '22px',
    color: 'var(--color-text)',
  },
  subtitle: {
    fontSize: '14px',
    color: 'var(--color-text-secondary)',
    maxWidth: '800px',
    textAlign: 'left',
  },
  devCard: {
    padding: '16px 20px',
    backgroundColor: 'rgba(30, 41, 59, 0.2)',
    borderStyle: 'dashed',
  },
  devHeading: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '12px',
    color: 'var(--color-text-secondary)',
  },
  devHeadingText: {
    fontSize: '13px',
    fontWeight: 600,
  },
  btnRow: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
  },
  simBtn: {
    padding: '8px 16px',
    fontSize: '12px',
  },
  clearBtn: {
    padding: '6px 14px',
    fontSize: '12px',
  },
};
