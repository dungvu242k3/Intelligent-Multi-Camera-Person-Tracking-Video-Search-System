import { useEffect, useState } from 'react';
import { Camera as CameraIcon, Plus, Info } from 'lucide-react';
import { useAuthStore } from '../../shared/stores/authStore.ts';
import axiosInstance from '../../shared/utils/axiosInstance.ts';
import CameraTable, { Camera } from './components/CameraTable.tsx';
import CameraForm from './components/CameraForm.tsx';
import Modal from '../../shared/components/common/Modal.tsx';
import Button from '../../shared/components/common/Button.tsx';


export default function CameraManagementPage() {
  const { user } = useAuthStore();
  const isAdmin = user?.role_id === 1;

  const [cameras, setCameras] = useState<Camera[]>([]);
  const [stats, setStats] = useState<{ total: number; online: number; offline: number }>({
    total: 0,
    online: 0,
    offline: 0,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitLoading, setIsSubmitLoading] = useState(false);

  // Modal controls
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingCamera, setEditingCamera] = useState<Camera | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchCamerasAndStats = async () => {
    setIsLoading(true);
    try {
      const [camerasRes, statsRes] = await Promise.all([
        axiosInstance.get<Camera[]>('/cameras'),
        axiosInstance.get<{ total: number; online: number; offline: number }>('/cameras/status-summary'),
      ]);
      setCameras(camerasRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Failed to load cameras or stats:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void fetchCamerasAndStats();
  }, []);

  const handleCreateSubmit = async (values: { name: string; rtsp_url: string; location: string; fps: number }) => {
    setIsSubmitLoading(true);
    try {
      await axiosInstance.post('/cameras', values);
      setIsCreateOpen(false);
      await fetchCamerasAndStats();
    } finally {
      setIsSubmitLoading(false);
    }
  };

  const handleEditSubmit = async (values: { name: string; rtsp_url: string; location: string; fps: number }) => {
    if (!editingCamera) return;
    setIsSubmitLoading(true);
    try {
      await axiosInstance.put(`/cameras/${editingCamera.id}`, {
        name: values.name,
        location: values.location,
        fps: values.fps,
      });
      setEditingCamera(null);
      await fetchCamerasAndStats();
    } finally {
      setIsSubmitLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deletingId) return;
    setIsSubmitLoading(true);
    try {
      await axiosInstance.delete(`/cameras/${deletingId}`);
      setDeletingId(null);
      await fetchCamerasAndStats();
    } finally {
      setIsSubmitLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      {/* Title Header */}
      <div style={styles.header}>
        <div style={styles.titleBlock}>
          <CameraIcon size={24} color="var(--color-primary)" />
          <h1 style={styles.title}>Camera Management</h1>
        </div>
        {isAdmin && (
          <Button variant="primary" icon={<Plus size={16} />} onClick={() => setIsCreateOpen(true)}>
            Register Camera
          </Button>
        )}
      </div>

      {/* Connection Stats Grid */}
      <div style={styles.statsGrid}>
        <div className="card" style={styles.statCard}>
          <div style={styles.statLabel}>Total Cameras</div>
          <div style={styles.statVal}>{stats.total}</div>
        </div>
        <div className="card" style={styles.statCard}>
          <div style={styles.statLabel}>Online Streams</div>
          <div style={{ ...styles.statVal, color: 'var(--color-success)' }}>{stats.online}</div>
        </div>
        <div className="card" style={styles.statCard}>
          <div style={styles.statLabel}>Offline Streams</div>
          <div style={{ ...styles.statVal, color: 'var(--color-danger)' }}>{stats.offline}</div>
        </div>
      </div>

      {/* Main List Table */}
      <div className="card" style={styles.tableCard}>
        <CameraTable
          data={cameras}
          isLoading={isLoading}
          onEdit={(camera) => setEditingCamera(camera)}
          onDelete={(id) => setDeletingId(id)}
          isAdmin={isAdmin}
        />
      </div>

      {/* Register Camera Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Register Surveillance Camera"
      >
        <CameraForm onSubmit={handleCreateSubmit} isLoading={isSubmitLoading} />
      </Modal>

      {/* Edit Camera Modal */}
      <Modal
        isOpen={!!editingCamera}
        onClose={() => setEditingCamera(null)}
        title="Edit Camera Details"
      >
        {editingCamera && (
          <CameraForm
            initialValues={editingCamera}
            onSubmit={handleEditSubmit}
            isLoading={isSubmitLoading}
            isEdit
          />
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingId}
        onClose={() => setDeletingId(null)}
        title="Confirm Deletion"
        footer={
          <div style={styles.modalFooter}>
            <Button variant="secondary" onClick={() => setDeletingId(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDeleteConfirm} isLoading={isSubmitLoading}>
              Delete Camera
            </Button>
          </div>
        }
      >
        <div style={styles.deleteConfirm}>
          <Info size={36} color="var(--color-danger)" style={{ marginBottom: '16px' }} />
          <p>Are you sure you want to permanently delete this camera registration?</p>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginTop: '8px' }}>
            This action will disconnect the DeepStream analytics loop and cannot be undone.
          </p>
        </div>
      </Modal>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  titleBlock: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  title: {
    fontSize: '24px',
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '16px',
  },
  statCard: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    justifyContent: 'center',
  },
  statLabel: {
    fontSize: '12px',
    color: 'var(--color-text-secondary)',
    fontWeight: 600,
    fontFamily: 'var(--font-heading)',
    textTransform: 'uppercase',
  },
  statVal: {
    fontSize: '28px',
    fontWeight: 700,
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
  },
  tableCard: {
    padding: 0,
    overflow: 'hidden',
  },
  deleteConfirm: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    padding: '16px 0',
  },
  modalFooter: {
    display: 'flex',
    gap: '12px',
  },
};
