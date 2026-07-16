import React, { useRef, useState } from 'react';
import { UploadCloud, Users } from 'lucide-react';
import Button from '../../../shared/components/common/Button.tsx';

// Pre-defined ReID sample vectors of dimension 512 representing suspect profiles
export const SAMPLE_TARGETS = [
  {
    id: 'target_A',
    name: 'Operator Alexander',
    role: 'Staff',
    thumb: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=120&h=120',
    // Generate a reproducible mock 512-dim normalized vector for search queries
    embedding: Array.from({ length: 512 }, (_, i) => Math.sin(i * 0.1) / 10),
  },
  {
    id: 'target_B',
    name: 'Suspect Baker',
    role: 'Intruder',
    thumb: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=120&h=120',
    embedding: Array.from({ length: 512 }, (_, i) => Math.cos(i * 0.15) / 10),
  },
  {
    id: 'target_C',
    name: 'Visitor Charlie',
    role: 'Delivery',
    thumb: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=120&h=120',
    embedding: Array.from({ length: 512 }, (_, i) => Math.sin(i * 0.25) / 8),
  },
];

interface ImageUploadProps {
  onSelectEmbedding: (embedding: number[], name: string, thumb: string) => void;
  isLoading?: boolean;
}

export default function ImageUpload({ onSelectEmbedding, isLoading = false }: ImageUploadProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedTargetId, setSelectedTargetId] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleTargetClick = (target: typeof SAMPLE_TARGETS[0]) => {
    setSelectedTargetId(target.id);
    onSelectEmbedding(target.embedding, target.name, target.thumb);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    processUploadedFile(file);
  };

  const processUploadedFile = (file: File) => {
    setSelectedTargetId(null);
    // Generate a reproducible mock embedding based on filename hash to allow query simulation
    const hash = file.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const mockEmbedding = Array.from(
      { length: 512 },
      (_, i) => Math.sin((i + hash) * 0.12) / 10
    );

    const reader = new FileReader();
    reader.onload = () => {
      onSelectEmbedding(
        mockEmbedding,
        file.name,
        reader.result as string || 'https://placehold.co/120x120?text=Upload'
      );
    };
    reader.readAsDataURL(file);
  };

  return (
    <div style={styles.container}>
      {/* Upload Box */}
      <div
        style={{
          ...styles.dropzone,
          borderColor: isDragOver ? 'var(--color-primary)' : 'var(--color-border)',
          backgroundColor: isDragOver ? 'rgba(59, 130, 246, 0.03)' : 'rgba(15, 23, 42, 0.2)',
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragOver(false);
          const file = e.dataTransfer.files?.[0];
          if (file) processUploadedFile(file);
        }}
      >
        <UploadCloud size={38} color="var(--color-text-secondary)" style={{ marginBottom: '12px' }} />
        <h4 style={styles.uploadTitle}>Drag Suspect Photo Here</h4>
        <p style={styles.uploadSubtitle}>Supports JPG, PNG up to 10MB</p>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/*"
          style={{ display: 'none' }}
        />
        <Button
          variant="secondary"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
          style={{ marginTop: '12px' }}
        >
          Select File
        </Button>
      </div>

      {/* Target gallery title */}
      <div style={styles.galleryHeader}>
        <Users size={14} color="var(--color-primary)" />
        <span style={styles.galleryTitle}>Demo Suspect Profiles Gallery</span>
      </div>

      {/* Target cards list */}
      <div style={styles.cardsGrid}>
        {SAMPLE_TARGETS.map((target) => {
          const isSelected = selectedTargetId === target.id;
          return (
            <div
              key={target.id}
              onClick={() => handleTargetClick(target)}
              style={{
                ...styles.card,
                borderColor: isSelected ? 'var(--color-primary)' : 'var(--color-border)',
                backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.05)' : 'var(--color-surface)',
              }}
            >
              <img src={target.thumb} alt={target.name} style={styles.avatar} />
              <div style={styles.cardInfo}>
                <div style={styles.cardName}>{target.name}</div>
                <div style={styles.cardRole}>{target.role}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  dropzone: {
    border: '2px dashed var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    padding: '32px 24px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    transition: 'all 200ms ease',
  },
  uploadTitle: {
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--color-text)',
    fontFamily: 'var(--font-body)',
  },
  uploadSubtitle: {
    fontSize: '12px',
    color: 'var(--color-text-secondary)',
    marginTop: '4px',
  },
  galleryHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginTop: '8px',
  },
  galleryTitle: {
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-heading)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  cardsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
  },
  card: {
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    padding: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    cursor: 'pointer',
    transition: 'all 150ms ease',
  },
  avatar: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    objectFit: 'cover',
    border: '1px solid var(--color-border)',
  },
  cardInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  cardName: {
    fontSize: '13px',
    fontWeight: 600,
    color: 'var(--color-text)',
  },
  cardRole: {
    fontSize: '10px',
    color: 'var(--color-text-secondary)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
};
