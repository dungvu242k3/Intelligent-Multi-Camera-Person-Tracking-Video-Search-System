import { Edit2, Trash2, Video } from 'lucide-react';
import Table from '../../../shared/components/common/Table.tsx';
import Badge from '../../../shared/components/common/Badge.tsx';

export interface Camera {
  id: string;
  name: string;
  rtsp_url: string;
  location: string;
  status: string;
  fps: number;
  created_at: string;
}

interface CameraTableProps {
  data: Camera[];
  isLoading?: boolean;
  onEdit: (camera: Camera) => void;
  onDelete: (id: string) => void;
  isAdmin?: boolean;
}

export default function CameraTable({
  data,
  isLoading = false,
  onEdit,
  onDelete,
  isAdmin = false,
}: CameraTableProps) {
  const columns = [
    {
      header: 'Stream Info',
      accessor: (camera: Camera) => (
        <div style={styles.streamInfo}>
          <div style={styles.iconContainer}>
            <Video size={16} color="var(--color-primary)" />
          </div>
          <div>
            <div style={styles.name}>{camera.name}</div>
            <div style={styles.rtsp}>{camera.rtsp_url}</div>
          </div>
        </div>
      ),
    },
    {
      header: 'Status',
      accessor: (camera: Camera) => {
        const isOnline = camera.status?.toLowerCase() === 'online' || camera.status?.toLowerCase() === 'active';
        return (
          <Badge variant={isOnline ? 'success' : 'danger'}>
            {isOnline ? 'Online' : 'Offline'}
          </Badge>
        );
      },
    },
    {
      header: 'Location',
      accessor: (camera: Camera) => (
        <span style={styles.location}>{camera.location}</span>
      ),
    },
    {
      header: 'Target FPS',
      accessor: (camera: Camera) => (
        <span style={styles.fps}>{camera.fps} FPS</span>
      ),
    },
    {
      header: 'Actions',
      accessor: (camera: Camera) => (
        <div style={styles.actions}>
          <button
            type="button"
            onClick={() => onEdit(camera)}
            style={styles.actionBtn}
            title="Edit Camera Details"
            disabled={!isAdmin}
          >
            <Edit2 size={14} color={isAdmin ? 'var(--color-primary)' : 'var(--color-border)'} />
          </button>
          <button
            type="button"
            onClick={() => onDelete(camera.id)}
            style={styles.actionBtnDanger}
            title="Delete Camera"
            disabled={!isAdmin}
          >
            <Trash2 size={14} color={isAdmin ? 'var(--color-danger)' : 'var(--color-border)'} />
          </button>
        </div>
      ),
      style: { textAlign: 'right' as const },
    },
  ];

  return (
    <Table
      data={data}
      columns={columns}
      isLoading={isLoading}
      emptyMessage="No cameras registered. Register a stream endpoint using the control button."
    />
  );
}

const styles: Record<string, React.CSSProperties> = {
  streamInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  iconContainer: {
    width: '32px',
    height: '32px',
    borderRadius: 'var(--radius-sm)',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  name: {
    fontWeight: 600,
    color: 'var(--color-text)',
  },
  rtsp: {
    fontSize: '11px',
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-heading)',
    marginTop: '2px',
  },
  location: {
    color: 'var(--color-text)',
    fontSize: '13px',
  },
  fps: {
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-heading)',
    fontSize: '13px',
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: '8px',
  },
  actionBtn: {
    background: 'rgba(59, 130, 246, 0.05)',
    border: 'none',
    cursor: 'pointer',
    padding: '6px',
    borderRadius: 'var(--radius-sm)',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 150ms ease',
  },
  actionBtnDanger: {
    background: 'rgba(239, 68, 68, 0.05)',
    border: 'none',
    cursor: 'pointer',
    padding: '6px',
    borderRadius: 'var(--radius-sm)',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 150ms ease',
  },
};
