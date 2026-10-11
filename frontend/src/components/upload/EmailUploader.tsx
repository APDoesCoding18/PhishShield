import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, X, AlertCircle, Shield, RefreshCw } from 'lucide-react';
import { apiClient, ApiError } from '../../services/api';
import { historyStorage } from '../../services/historyStorage';

interface EmailUploaderProps {
  onAnalysisStarted: (jobId: string) => void;
}

const MAX_UPLOAD_SIZE = 10 * 1024 * 1024; // 10MB as defined by backend MAX_UPLOAD_SIZE

export const EmailUploader: React.FC<EmailUploaderProps> = ({ onAnalysisStarted }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<{ code: string; message: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const validateAndSetFile = (file: File) => {
    setValidationError(null);
    setSubmissionError(null);

    // 1. Filename presence
    if (!file.name) {
      setValidationError('Invalid file: Missing filename.');
      setSelectedFile(null);
      return;
    }

    // 2. Extension constraint (.eml only)
    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith('.eml')) {
      setValidationError('Invalid file format: PhishShield only accepts standard RFC 822 email files (.eml).');
      setSelectedFile(null);
      return;
    }

    // 3. File size restriction (10MB)
    if (file.size > MAX_UPLOAD_SIZE) {
      setValidationError(`File exceeds maximum allowed size of 10MB (${formatFileSize(file.size)}).`);
      setSelectedFile(null);
      return;
    }

    if (file.size === 0) {
      setValidationError('File is empty (0 Bytes). Please select a valid .eml file.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isSubmitting) {
      setDragActive(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (isSubmitting) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      validateAndSetFile(file);
    }
  };

  const handleRemoveFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isSubmitting) return;
    setSelectedFile(null);
    setValidationError(null);
    setSubmissionError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile || isSubmitting) return;

    setIsSubmitting(true);
    setSubmissionError(null);

    try {
      const result = await apiClient.uploadEmail(selectedFile);

      // Record in client history cache for immediate navigation & auditability
      historyStorage.addItem({
        jobId: result.job_id,
        originalFilename: selectedFile.name,
        fileSizeBytes: selectedFile.size,
        uploadedAt: new Date().toISOString(),
        status: result.status,
      });

      // Clear local selection and trigger navigation to report
      setSelectedFile(null);
      onAnalysisStarted(result.job_id);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setSubmissionError({
          code: err.errorCode,
          message: err.message,
        });
      } else {
        setSubmissionError({
          code: 'UNEXPECTED_ERROR',
          message: 'An unexpected error occurred while communicating with the analysis server.',
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="email-uploader-container">
      {/* Hidden Native File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".eml"
        style={{ display: 'none' }}
        onChange={handleFileChange}
        disabled={isSubmitting}
        aria-label="Upload .eml email file"
      />

      {/* Main Drag & Drop Zone */}
      <div
        className={`dropzone-card ${dragActive ? 'drag-active' : ''} ${
          selectedFile ? 'file-selected' : ''
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => {
          if (!selectedFile && !isSubmitting) {
            fileInputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !selectedFile && !isSubmitting) {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        aria-label="Drag and drop .eml file or click to select"
      >
        {!selectedFile ? (
          <div className="dropzone-empty-state">
            <div className="icon-badge">
              <UploadCloud size={32} />
            </div>
            <h2 className="text-section" style={{ marginBottom: 'var(--space-2)' }}>
              Drag & Drop .eml Email File Here
            </h2>
            <p className="dropzone-hint">
              Upload an RFC 822 formatted email file up to 10MB. PhishShield parses headers, body text, URLs, and attachments in an isolated sandbox.
            </p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
              disabled={isSubmitting}
            >
              Browse Files (.eml)
            </button>
          </div>
        ) : (
          <div className="selected-file-view">
            <div className="file-info-header">
              <div className="file-badge-icon">
                <FileText size={28} />
              </div>
              <div className="file-details">
                <span className="file-name font-mono">{selectedFile.name}</span>
                <span className="file-size text-meta">
                  {formatFileSize(selectedFile.size)} • Standard RFC 822 Email
                </span>
              </div>
              <button
                type="button"
                className="btn-remove"
                onClick={handleRemoveFile}
                disabled={isSubmitting}
                title="Remove selected file"
                aria-label="Remove selected file"
              >
                <X size={18} />
              </button>
            </div>

            <div className="file-actions">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                disabled={isSubmitting}
              >
                Replace File
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={(e) => {
                  e.stopPropagation();
                  handleAnalyze();
                }}
                disabled={isSubmitting}
                style={{ minWidth: '160px' }}
              >
                {isSubmitting ? (
                  <>
                    <span className="spinner" style={{ width: '16px', height: '16px' }} />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Shield size={16} />
                    <span>Analyze Email</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Validation Feedback Banner */}
      {validationError && (
        <div className="alert alert-warning" style={{ marginTop: 'var(--space-4)' }} role="alert">
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <div>
            <strong>Validation Error:</strong> {validationError}
          </div>
        </div>
      )}

      {/* Submission Error Banner with Retry */}
      {submissionError && (
        <div className="alert alert-danger" style={{ marginTop: 'var(--space-4)' }} role="alert">
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, marginBottom: '2px' }}>
              Submission Failed ({submissionError.code})
            </div>
            <div style={{ fontSize: '13px' }}>{submissionError.message}</div>
          </div>
          {selectedFile && !isSubmitting && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleAnalyze}
              style={{ alignSelf: 'center' }}
            >
              <RefreshCw size={14} />
              <span>Retry</span>
            </button>
          )}
        </div>
      )}

      {/* Submission In-Flight Banner */}
      {isSubmitting && (
        <div className="alert alert-info" style={{ marginTop: 'var(--space-4)' }}>
          <span className="spinner" style={{ width: '16px', height: '16px', flexShrink: 0 }} />
          <div>
            <strong>Uploading & Enqueueing:</strong> Sending email to PhishShield secure workspace...
          </div>
        </div>
      )}

      <style>{`
        .email-uploader-container {
          width: 100%;
        }

        .dropzone-card {
          border: 2px dashed var(--border-default);
          border-radius: var(--radius-lg);
          background-color: var(--bg-surface);
          padding: var(--space-8) var(--space-6);
          transition: all var(--transition-normal);
          cursor: pointer;
        }

        .dropzone-card:hover {
          border-color: var(--color-action-blue);
          background-color: var(--bg-surface-subtle);
        }

        .dropzone-card.drag-active {
          border-color: var(--color-action-blue);
          background-color: rgba(37, 99, 235, 0.05);
          box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15);
        }

        .dropzone-card.file-selected {
          border-style: solid;
          cursor: default;
          padding: var(--space-6);
        }

        .dropzone-empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }

        .icon-badge {
          width: 64px;
          height: 64px;
          border-radius: 50%;
          background-color: rgba(37, 99, 235, 0.1);
          color: var(--color-action-blue);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: var(--space-4);
        }

        .dropzone-hint {
          color: var(--text-muted);
          max-width: 500px;
          margin-bottom: var(--space-5);
          line-height: 1.5;
        }

        .selected-file-view {
          display: flex;
          flex-direction: column;
          gap: var(--space-5);
        }

        .file-info-header {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          background-color: var(--bg-surface-subtle);
          padding: var(--space-4) var(--space-5);
          border-radius: var(--radius-md);
          border: 1px solid var(--border-subtle);
        }

        .file-badge-icon {
          color: var(--color-action-blue);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .file-details {
          flex: 1;
          display: flex;
          flex-direction: column;
          min-width: 0;
        }

        .file-name {
          font-weight: 600;
          color: var(--text-main);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .btn-remove {
          color: var(--text-muted);
          padding: 6px;
          border-radius: var(--radius-sm);
          transition: all var(--transition-fast);
        }

        .btn-remove:hover {
          color: var(--risk-high);
          background-color: var(--risk-high-bg);
        }

        .file-actions {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: var(--space-3);
        }
      `}</style>
    </div>
  );
};
