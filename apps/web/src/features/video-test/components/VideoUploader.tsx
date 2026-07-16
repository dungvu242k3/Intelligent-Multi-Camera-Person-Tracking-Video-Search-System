import React, { memo, useCallback, useRef, useState } from 'react';
import { UploadCloud, FileVideo, AlertCircle } from 'lucide-react';
import { useTranslation } from '../../../shared/hooks/useTranslation.ts';
import { VIDEO_UPLOAD_CONSTRAINTS } from '../constants.ts';

interface VideoUploaderProps {
  onFileSelected: (file: File) => void;
}

function VideoUploader({ onFileSelected }: VideoUploaderProps) {
  const { t } = useTranslation();
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const validateAndSelect = useCallback((file: File) => {
    setError(null);
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!VIDEO_UPLOAD_CONSTRAINTS.acceptedExtensions.includes(fileExtension)) {
      setError(t('vtest.uploader.errFormat'));
      return;
    }
    
    if (file.size > VIDEO_UPLOAD_CONSTRAINTS.maxFileSizeBytes) {
      setError(
        `${t('vtest.uploader.errSize')} (${(file.size / VIDEO_UPLOAD_CONSTRAINTS.bytesPerMegabyte).toFixed(1)}MB)`
      );
      return;
    }

    setSelectedFile(file);
    onFileSelected(file);
  }, [onFileSelected, t]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelect(e.dataTransfer.files[0]);
    }
  }, [validateAndSelect]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSelect(e.target.files[0]);
    }
  }, [validateAndSelect]);

  const triggerInput = useCallback(() => {
    inputRef.current?.click();
  }, []);

  return (
    <div style={styles.container}>
      <div 
        style={{
          ...styles.dropzone,
          borderColor: dragActive ? 'var(--color-primary)' : 'var(--color-border)',
          backgroundColor: dragActive ? 'rgba(59, 130, 246, 0.05)' : 'rgba(30, 41, 59, 0.5)',
        }}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          id="video-file-input"
          ref={inputRef}
          type="file" 
          style={styles.hiddenInput}
          accept={VIDEO_UPLOAD_CONSTRAINTS.acceptedMimeTypes}
          onChange={handleChange}
          aria-describedby={error ? 'video-file-error' : selectedFile ? 'video-file-selected' : undefined}
        />
        
        <UploadCloud size={48} color={dragActive ? 'var(--color-primary)' : 'var(--color-text-secondary)'} />
        
        <h3 style={styles.heading}>{t('vtest.uploader.title')}</h3>
        <p style={styles.subtext}>{t('vtest.uploader.sub')}</p>
        
        <button type="button" onClick={triggerInput} className="btn-secondary" style={styles.btn} aria-controls="video-file-input">
          {t('vtest.uploader.browse')}
        </button>

        {selectedFile && (
          <div style={styles.fileCard} role="status" id="video-file-selected">
            <FileVideo size={20} color="var(--color-success)" />
            <div style={styles.fileDetails}>
              <div style={styles.fileName}>{selectedFile.name}</div>
              <div style={styles.fileSize}>
                {(selectedFile.size / VIDEO_UPLOAD_CONSTRAINTS.bytesPerMegabyte).toFixed(1)} MB
              </div>
            </div>
          </div>
        )}

        {error && (
          <div style={styles.errorCard} role="alert" id="video-file-error">
            <AlertCircle size={20} color="var(--color-danger)" />
            <div style={styles.errorText}>{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(VideoUploader);

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    padding: '12px 0',
  },
  dropzone: {
    border: '2px dashed var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 20px',
    textAlign: 'center',
    cursor: 'pointer',
    position: 'relative',
    transition: 'all 200ms ease',
  },
  hiddenInput: {
    display: 'none',
  },
  heading: {
    fontSize: '16px',
    color: 'var(--color-text)',
    marginTop: '16px',
    marginBottom: '8px',
  },
  subtext: {
    fontSize: '13px',
    color: 'var(--color-text-secondary)',
    marginBottom: '20px',
  },
  btn: {
    padding: '8px 24px',
    fontSize: '13px',
  },
  fileCard: {
    marginTop: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    padding: '12px 16px',
    width: '100%',
    maxWidth: '400px',
  },
  fileDetails: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
    overflow: 'hidden',
  },
  fileName: {
    fontSize: '13px',
    fontWeight: 600,
    color: 'var(--color-text)',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
    overflow: 'hidden',
    width: '100%',
    textAlign: 'left',
  },
  fileSize: {
    fontSize: '11px',
    color: 'var(--color-text-secondary)',
    marginTop: '2px',
  },
  errorCard: {
    marginTop: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    backgroundColor: 'var(--color-danger-bg)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    borderRadius: 'var(--radius-md)',
    padding: '12px 16px',
    width: '100%',
    maxWidth: '450px',
  },
  errorText: {
    fontSize: '13px',
    color: 'var(--color-danger)',
    textAlign: 'left',
  },
};
