import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar.tsx';
import Header from './Header.tsx';

export default function MainLayout() {
  return (
    <div style={styles.container}>
      {/* Sidebar - fixed left */}
      <Sidebar />
      
      {/* Content Area - shifted right by 240px */}
      <div style={styles.mainArea}>
        {/* Header - fixed top */}
        <Header />
        
        {/* Page content - shifted down by 70px */}
        <main style={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: 'var(--color-background)',
  },
  mainArea: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    marginLeft: '240px', /* Sidebar width */
  },
  content: {
    flex: 1,
    marginTop: '70px', /* Header height */
    minHeight: 'calc(100vh - 70px)',
    backgroundColor: 'var(--color-background)',
    color: 'var(--color-text)',
  },
};
