
export default function LiveMonitorPage() {
  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: '16px' }}>Live Monitor Feed</h1>
      <div className="card" style={{ maxWidth: '600px' }}>
        <h3 style={{ marginBottom: '12px' }}>Active Cameras</h3>
        <p style={{ color: 'var(--color-text-secondary)' }}>
          Real-time video grids with YOLOv8 & ReID object bounding boxes overlay will be displayed here.
        </p>
      </div>
    </div>
  );
}
