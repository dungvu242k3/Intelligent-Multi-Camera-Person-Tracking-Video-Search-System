
export default function DashboardPage() {
  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: '16px' }}>Dashboard Overview</h1>
      <div className="card" style={{ maxWidth: '600px' }}>
        <h3 style={{ marginBottom: '12px' }}>System Status</h3>
        <p style={{ color: 'var(--color-text-secondary)' }}>
          Operational analytics, event-driven statistics, and total tracking logs will be aggregated here.
        </p>
      </div>
    </div>
  );
}
