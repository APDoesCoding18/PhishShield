import React from 'react';
import { ArrowLeft, Clock, RefreshCw } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';
import { JobStatus } from '../../types/api';

interface ReportHeaderProps {
  jobId: string;
  originalFilename?: string;
  status: JobStatus;
  createdAt?: string;
  updatedAt?: string;
  onBackToDashboard: () => void;
  onRefresh?: () => void;
  isPolling?: boolean;
}

export const ReportHeader: React.FC<ReportHeaderProps> = ({
  jobId,
  originalFilename,
  status,
  createdAt,
  updatedAt,
  onBackToDashboard,
  onRefresh,
  isPolling = false,
}) => {
  const formatTimestamp = (iso?: string) => {
    if (!iso) return null;
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' (' + d.toLocaleDateString() + ')';
    } catch {
      return iso;
    }
  };

  return (
    <div className="report-header" style={{ marginBottom: 'var(--space-6)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={onBackToDashboard}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
        >
          <ArrowLeft size={14} /> Back to Dashboard
        </button>

        {onRefresh && (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={onRefresh}
            disabled={isPolling}
            title="Refresh analysis report status"
          >
            <RefreshCw size={13} className={isPolling ? 'spinner' : ''} />
            <span>{isPolling ? 'Polling Status...' : 'Refresh Status'}</span>
          </button>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-1)' }}>
            <h1 className="text-title" style={{ wordBreak: 'break-all' }}>
              {originalFilename || 'Analysis Report'}
            </h1>
            <StatusBadge status={status} label={status} size="sm" />
          </div>

          <div className="font-mono text-meta" style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <span>Job ID: {jobId}</span>
            {createdAt && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={12} /> Submitted: {formatTimestamp(createdAt)}
              </span>
            )}
            {updatedAt && updatedAt !== createdAt && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                Updated: {formatTimestamp(updatedAt)}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
