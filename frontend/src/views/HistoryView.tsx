import React, { useState, useEffect, useCallback } from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';
import { apiClient } from '../services/api';
import { historyStorage } from '../services/historyStorage';
import { AnalysisHistoryItemResponse } from '../types/api';
import {
  Shield,
  Search,
  RefreshCw,
  AlertCircle,
  ExternalLink,
  Trash2,
  Filter,
  Clock,
  FileText,
  ChevronRight,
} from 'lucide-react';

interface HistoryViewProps {
  onSelectJob: (jobId: string) => void;
  onNewAnalysis: () => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({ onSelectJob, onNewAnalysis }) => {
  const [items, setItems] = useState<AnalysisHistoryItemResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [verdictFilter, setVerdictFilter] = useState<string>('all');

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // 1. Fetch real persisted history from the backend
      const backendItems = await apiClient.listAnalyses({ limit: 100 });

      // 2. Fetch local storage items for filename reconciliation (if backend didn't parse original filename)
      const localMap = new Map<string, string>();
      historyStorage.getItems().forEach((item) => {
        if (item.originalFilename) {
          localMap.set(item.jobId, item.originalFilename);
        }
      });

      // Merge filename if available locally and missing from backend
      const mergedItems: AnalysisHistoryItemResponse[] = backendItems.map((item) => ({
        ...item,
        original_filename: item.original_filename || localMap.get(item.job_id) || null,
      }));

      setItems(mergedItems);
    } catch (err: unknown) {
      // If backend call fails, fallback to local storage cache so the user still has visibility
      const localItems = historyStorage.getItems();
      if (localItems.length > 0) {
        const fallbackItems: AnalysisHistoryItemResponse[] = localItems.map((l) => ({
          job_id: l.jobId,
          original_filename: l.originalFilename,
          status: l.status,
          created_at: l.uploadedAt,
          updated_at: l.uploadedAt,
          verdict: l.verdict,
          score: l.score,
          severity: null,
        }));
        setItems(fallbackItems);
      }
      const message = err instanceof Error ? err.message : 'Failed to load analysis history.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleClearLocalCache = () => {
    if (window.confirm('Clear local history cache? Note that backend records remain persisted.')) {
      historyStorage.clearHistory();
      fetchHistory();
    }
  };

  const formatTimestamp = (isoString?: string | null): string => {
    if (!isoString) return '—';
    try {
      const date = new Date(isoString);
      if (isNaN(date.getTime())) return isoString;
      return (
        date.toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        }) +
        ' ' +
        date.toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit',
        })
      );
    } catch {
      return isoString;
    }
  };

  // Client-side filtering across available fields
  const filteredItems = items.filter((item) => {
    // Search query matches job_id or original_filename
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchId = item.job_id.toLowerCase().includes(q);
      const matchFilename = (item.original_filename || '').toLowerCase().includes(q);
      if (!matchId && !matchFilename) return false;
    }

    // Status filter
    if (statusFilter !== 'all' && item.status.toLowerCase() !== statusFilter.toLowerCase()) {
      return false;
    }

    // Verdict filter
    if (verdictFilter !== 'all') {
      const itemVerdict = (item.verdict || 'unassessed').toLowerCase();
      if (itemVerdict !== verdictFilter.toLowerCase()) {
        return false;
      }
    }

    return true;
  });

  return (
    <div className="history-view-container">
      <PageHeader
        title="Analysis History"
        description="Review persisted email sandbox analyses, inspect risk verdicts, and reopen full technical reports."
        actions={
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={fetchHistory}
              disabled={isLoading}
              title="Refresh history records"
            >
              <RefreshCw size={14} className={isLoading ? 'spinner' : ''} /> Refresh
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleClearLocalCache}
              title="Clear cached browser history entries"
            >
              <Trash2 size={14} /> Clear Cache
            </button>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={onNewAnalysis}
            >
              + New Analysis
            </button>
          </div>
        }
      />

      {/* Error Banner with Retry */}
      {error && (
        <div
          className="alert alert-danger"
          style={{ marginBottom: 'var(--space-4)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
          role="alert"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <AlertCircle size={18} />
            <div>
              <strong>Failed to fetch backend records:</strong> {error}
            </div>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={fetchHistory}
          >
            Retry
          </button>
        </div>
      )}

      {/* Search and Filters Toolbar */}
      <div
        className="card"
        style={{
          marginBottom: 'var(--space-5)',
          padding: 'var(--space-4)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: 'var(--space-3)',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flex: '1 1 280px' }}>
          <Search size={16} color="var(--text-dim)" />
          <input
            type="text"
            placeholder="Search by filename or Job ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: 'var(--space-2) var(--space-3)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-default)',
              backgroundColor: 'var(--input-bg)',
              color: 'var(--text-main)',
              fontSize: '13px',
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <Filter size={14} color="var(--text-dim)" />
            <span className="text-meta" style={{ fontWeight: 500 }}>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                padding: 'var(--space-1) var(--space-2)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-default)',
                backgroundColor: 'var(--input-bg)',
                color: 'var(--text-main)',
                fontSize: '13px',
              }}
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span className="text-meta" style={{ fontWeight: 500 }}>Verdict:</span>
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
              style={{
                padding: 'var(--space-1) var(--space-2)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-default)',
                backgroundColor: 'var(--input-bg)',
                color: 'var(--text-main)',
                fontSize: '13px',
              }}
            >
              <option value="all">All Verdicts</option>
              <option value="clean">Clean</option>
              <option value="suspicious">Suspicious</option>
              <option value="malicious">Malicious</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content: Loading, Empty, or Populated List */}
      {isLoading && items.length === 0 ? (
        <div className="card" style={{ padding: 'var(--space-10)', textAlign: 'center' }}>
          <div className="spinner" style={{ margin: '0 auto var(--space-3)', width: '28px', height: '28px' }} />
          <p style={{ color: 'var(--text-muted)' }}>Loading analysis history from server...</p>
        </div>
      ) : items.length === 0 ? (
        /* Empty State */
        <div className="card" style={{ padding: 'var(--space-10)', textAlign: 'center' }}>
          <div style={{ color: 'var(--text-dim)', marginBottom: 'var(--space-3)' }}>
            <Shield size={42} style={{ margin: '0 auto' }} />
          </div>
          <h2 className="text-section" style={{ marginBottom: 'var(--space-2)' }}>No Analysis History Found</h2>
          <p style={{ color: 'var(--text-muted)', maxWidth: '440px', margin: '0 auto var(--space-5)' }}>
            No emails have been analyzed yet or records were purged. Start by submitting an RFC 822 (.eml) file for static and heuristic threat evaluation.
          </p>
          <button type="button" className="btn btn-primary" onClick={onNewAnalysis}>
            Start First Analysis
          </button>
        </div>
      ) : filteredItems.length === 0 ? (
        /* Filter Zero Results State */
        <div className="card" style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
          <p style={{ color: 'var(--text-muted)', marginBottom: 'var(--space-3)' }}>
            No analysis jobs matched your current filter criteria.
          </p>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => {
              setSearchQuery('');
              setStatusFilter('all');
              setVerdictFilter('all');
            }}
          >
            Clear Filters
          </button>
        </div>
      ) : (
        /* Populated State */
        <>
          {/* Desktop / Tablet Table View */}
          <div className="card history-table-container">
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '13px' }}>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>File / Email</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Job Identifier</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Submitted</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Verdict</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Score</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((row) => (
                  <tr
                    key={row.job_id}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      fontSize: '14px',
                      transition: 'background-color var(--transition-fast)',
                    }}
                  >
                    <td style={{ padding: 'var(--space-3) var(--space-4)', maxWidth: '240px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <FileText size={16} color="var(--color-action-blue)" style={{ flexShrink: 0 }} />
                        <span
                          style={{
                            fontWeight: 500,
                            wordBreak: 'break-all',
                            color: 'var(--text-main)',
                          }}
                        >
                          {row.original_filename || 'Unknown Email File'}
                        </span>
                      </div>
                    </td>

                    <td style={{ padding: 'var(--space-3) var(--space-4)', maxWidth: '220px' }}>
                      <span
                        className="font-mono text-meta"
                        style={{ wordBreak: 'break-all' }}
                      >
                        {row.job_id}
                      </span>
                    </td>

                    <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-muted)', fontSize: '13px', whiteSpace: 'nowrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={12} />
                        <span>{formatTimestamp(row.created_at)}</span>
                      </div>
                    </td>

                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      <span className={`badge ${row.status === 'COMPLETED' ? 'badge-clean' : row.status === 'FAILED' ? 'badge-malicious' : 'badge-unknown'}`}>
                        {row.status}
                      </span>
                    </td>

                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      {row.verdict ? (
                        <StatusBadge status={row.verdict} size="sm" />
                      ) : (
                        <span className="text-meta" style={{ color: 'var(--text-dim)' }}>
                          {row.status === 'COMPLETED' ? 'No verdict' : 'Pending'}
                        </span>
                      )}
                    </td>

                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      <span className="font-mono text-meta" style={{ fontWeight: 600 }}>
                        {typeof row.score === 'number' && !isNaN(row.score)
                          ? `${row.score.toFixed(1)} / 100`
                          : '—'}
                      </span>
                    </td>

                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'right' }}>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => onSelectJob(row.job_id)}
                        aria-label={`Open analysis report for job ${row.job_id}`}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                      >
                        <span>Open Report</span>
                        <ExternalLink size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Responsive Cards View */}
          <div className="history-mobile-cards">
            {filteredItems.map((row) => (
              <div
                key={row.job_id}
                className="card"
                style={{
                  padding: 'var(--space-4)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-3)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={16} color="var(--color-action-blue)" />
                    <span style={{ fontWeight: 600, fontSize: '14px', wordBreak: 'break-all' }}>
                      {row.original_filename || 'Unknown Email File'}
                    </span>
                  </div>
                  <span className={`badge ${row.status === 'COMPLETED' ? 'badge-clean' : row.status === 'FAILED' ? 'badge-malicious' : 'badge-unknown'}`}>
                    {row.status}
                  </span>
                </div>

                <div className="font-mono text-meta" style={{ wordBreak: 'break-all' }}>
                  ID: {row.job_id}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-2)', fontSize: '13px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)' }}>
                    <Clock size={12} />
                    <span>{formatTimestamp(row.created_at)}</span>
                  </div>

                  <div>
                    {row.verdict ? (
                      <StatusBadge status={row.verdict} size="sm" />
                    ) : (
                      <span className="text-meta" style={{ color: 'var(--text-dim)' }}>
                        Verdict: {row.status === 'COMPLETED' ? 'None' : 'Pending'}
                      </span>
                    )}
                  </div>
                </div>

                {typeof row.score === 'number' && !isNaN(row.score) && (
                  <div className="font-mono text-meta" style={{ fontWeight: 600 }}>
                    Calculated Score: {row.score.toFixed(1)} / 100
                  </div>
                )}

                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => onSelectJob(row.job_id)}
                  style={{ width: '100%', marginTop: 'var(--space-1)' }}
                  aria-label={`Open report for ${row.job_id}`}
                >
                  <span>Open Full Analysis Report</span>
                  <ChevronRight size={14} />
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
