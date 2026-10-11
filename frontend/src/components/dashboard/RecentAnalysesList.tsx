import React from 'react';
import { Shield, Clock, ArrowRight, ExternalLink } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';
import { StoredAnalysisItem } from '../../services/historyStorage';

interface RecentAnalysesListProps {
  items: StoredAnalysisItem[];
  onSelectJob: (jobId: string) => void;
  onViewAllHistory: () => void;
}

export const RecentAnalysesList: React.FC<RecentAnalysesListProps> = ({
  items,
  onSelectJob,
  onViewAllHistory,
}) => {
  if (items.length === 0) {
    return null;
  }

  const formatTimestamp = (isoString: string): string => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' on ' + date.toLocaleDateString();
    } catch {
      return isoString;
    }
  };

  return (
    <div className="recent-analyses-section" style={{ marginTop: 'var(--space-8)' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 'var(--space-4)',
        }}
      >
        <div>
          <h2 className="text-section">Recent Analysis Submissions</h2>
          <p className="text-meta">Locally recorded analysis jobs submitted from this session.</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={onViewAllHistory}>
          View History <ArrowRight size={14} />
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {items.slice(0, 5).map((item) => (
          <div
            key={item.jobId}
            className="card"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: 'var(--space-4) var(--space-5)',
              cursor: 'pointer',
              transition: 'border-color var(--transition-fast)',
            }}
            onClick={() => onSelectJob(item.jobId)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', minWidth: 0 }}>
              <div style={{ color: 'var(--color-action-blue)' }}>
                <Shield size={20} />
              </div>
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontWeight: 600,
                    color: 'var(--text-main)',
                    marginBottom: '2px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {item.originalFilename}
                </div>
                <div className="font-mono text-meta" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>{item.jobId}</span>
                  <span>•</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} />
                    {formatTimestamp(item.uploadedAt)}
                  </span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', flexShrink: 0 }}>
              {item.verdict ? (
                <StatusBadge status={item.verdict} size="sm" />
              ) : (
                <span className="badge badge-unknown text-meta">{item.status}</span>
              )}
              {item.score !== undefined && (
                <span className="font-mono text-meta" style={{ fontWeight: 600 }}>
                  Score: {item.score.toFixed(1)}
                </span>
              )}
              <ExternalLink size={16} color="var(--text-dim)" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
