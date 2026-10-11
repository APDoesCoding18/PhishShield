import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, HelpCircle, Info } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';
import { RiskResultResponse } from '../../types/api';

interface VerdictSummaryProps {
  riskResult?: RiskResultResponse | null;
  isLoading?: boolean;
}

export const VerdictSummary: React.FC<VerdictSummaryProps> = ({ riskResult, isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <span className="spinner" style={{ width: '18px', height: '18px' }} />
          <span>Aggregating multi-vector risk verdict...</span>
        </div>
      </div>
    );
  }

  if (!riskResult) {
    return (
      <div
        className="card"
        style={{
          borderLeft: '5px solid var(--risk-unknown)',
          marginBottom: 'var(--space-6)',
          backgroundColor: 'var(--bg-surface-elevated)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
          <HelpCircle size={22} color="var(--risk-unknown)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 600, marginBottom: '4px' }}>Risk Verdict Not Yet Available</div>
            <p className="text-meta" style={{ color: 'var(--text-muted)' }}>
              The risk engine computes final scoring and verdict once all modular analyzers complete their passes.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const { verdict, score, severity, rationale } = riskResult;
  const normalizedVerdict = verdict?.toLowerCase() || 'unknown';

  let borderColor = 'var(--risk-unknown)';
  let VerdictIcon = HelpCircle;

  if (normalizedVerdict === 'malicious') {
    borderColor = 'var(--risk-high)';
    VerdictIcon = ShieldAlert;
  } else if (normalizedVerdict === 'suspicious') {
    borderColor = 'var(--risk-caution)';
    VerdictIcon = AlertTriangle;
  } else if (normalizedVerdict === 'clean') {
    borderColor = 'var(--risk-clean)';
    VerdictIcon = ShieldCheck;
  }

  return (
    <div
      className="card"
      style={{
        borderLeft: `6px solid ${borderColor}`,
        marginBottom: 'var(--space-6)',
        backgroundColor: 'var(--bg-surface-elevated)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div style={{ flex: 1, minWidth: '280px' }}>
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <VerdictIcon size={20} color={borderColor} />
              <StatusBadge
                status={normalizedVerdict}
                label={`Verdict: ${verdict.toUpperCase()}`}
              />
            </div>
            {severity && (
              <span className="badge badge-unknown text-meta" style={{ textTransform: 'uppercase' }}>
                Severity: {severity}
              </span>
            )}
            <span className="font-mono text-meta" style={{ fontWeight: 600 }}>
              Calculated Score: {typeof score === 'number' && !isNaN(score) ? `${score.toFixed(1)} / 100` : 'Unavailable'}
            </span>
          </div>

          <div style={{ fontSize: '15px', color: 'var(--text-main)', fontWeight: 500, lineHeight: 1.5, marginTop: 'var(--space-2)' }}>
            {rationale || 'No automated rationale was returned for this analysis.'}
          </div>

          {/* Safety Disclaimer */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginTop: 'var(--space-3)',
              paddingTop: 'var(--space-3)',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: '12px',
              color: 'var(--text-muted)',
            }}
          >
            <Info size={14} style={{ flexShrink: 0 }} />
            <span>
              Heuristic assessment disclaimer: A low score or absence of indicators indicates no known static threats matched, not proof that the email is benign.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
