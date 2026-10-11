import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';
import { FindingResponse } from '../../types/api';

interface ContentFindingsSectionProps {
  findings: FindingResponse[];
  isCompleted: boolean;
}

export const ContentFindingsSection: React.FC<ContentFindingsSectionProps> = ({ findings, isCompleted }) => {
  const [expandedIndices, setExpandedIndices] = useState<Record<number, boolean>>({});

  const contentFindings = findings.filter((f) => f.category?.toLowerCase() === 'content');

  const toggleExpand = (idx: number) => {
    setExpandedIndices((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <AlertTriangle size={18} color="var(--risk-caution)" />
          <h2 className="text-section">Content & Phishing Indicators ({contentFindings.length})</h2>
        </div>
      </div>
      <p className="text-meta" style={{ marginBottom: 'var(--space-4)' }}>
        Rule-based lexical detection matching urgency triggers, credential harvesting requests, and authority impersonation patterns.
      </p>

      {contentFindings.length === 0 ? (
        <div
          style={{
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--bg-surface-subtle)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-muted)',
            fontSize: '13px',
          }}
        >
          {isCompleted
            ? 'No suspicious content or social engineering heuristics were flagged in the subject or body.'
            : 'Content inspection in progress...'}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {contentFindings.map((finding, idx) => {
            const isExpanded = !!expandedIndices[idx];

            let parsedEvidence: Record<string, unknown> | null = null;
            if (finding.evidence) {
              try {
                parsedEvidence = JSON.parse(finding.evidence);
              } catch {
                // If evidence is plain text
              }
            }

            return (
              <div
                key={idx}
                style={{
                  padding: 'var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--bg-surface-subtle)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    userSelect: 'none',
                  }}
                  onClick={() => toggleExpand(idx)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flex: 1 }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '14px' }}>
                      {finding.title}
                    </span>
                    <StatusBadge status={finding.severity} size="sm" />
                  </div>
                  <button
                    type="button"
                    style={{ color: 'var(--text-muted)', padding: '2px' }}
                    aria-label={isExpanded ? 'Collapse finding details' : 'Expand finding details'}
                  >
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                </div>

                {finding.description && (
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: 'var(--space-2)' }}>
                    {finding.description}
                  </p>
                )}

                {isExpanded && (
                  <div
                    style={{
                      marginTop: 'var(--space-3)',
                      paddingTop: 'var(--space-3)',
                      borderTop: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div className="text-meta" style={{ fontWeight: 600, marginBottom: '4px' }}>
                      Technical Evidence:
                    </div>
                    {parsedEvidence ? (
                      <pre
                        className="font-mono text-meta"
                        style={{
                          backgroundColor: 'var(--bg-page)',
                          padding: 'var(--space-3)',
                          borderRadius: 'var(--radius-sm)',
                          overflowX: 'auto',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-all',
                        }}
                      >
                        {JSON.stringify(parsedEvidence, null, 2)}
                      </pre>
                    ) : (
                      <div className="font-mono text-meta" style={{ backgroundColor: 'var(--bg-page)', padding: 'var(--space-2)' }}>
                        {finding.evidence || 'No additional raw evidence details available.'}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
