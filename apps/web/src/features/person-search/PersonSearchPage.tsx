
export default function PersonSearchPage() {
  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: '16px' }}>Person Image Search</h1>
      <div className="card" style={{ maxWidth: '600px' }}>
        <h3 style={{ marginBottom: '12px' }}>Vector Search Interface</h3>
        <p style={{ color: 'var(--color-text-secondary)' }}>
          Query Qdrant DB for matching person embedding profiles by uploading crop images or drawing bounding boxes.
        </p>
      </div>
    </div>
  );
}
