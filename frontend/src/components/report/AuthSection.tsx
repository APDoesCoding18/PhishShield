import React from 'react';
import { CheckCircle2, XCircle, AlertCircle, HelpCircle, Shield } from 'lucide-react';
import { FindingResponse } from '../../types/api';

interface AuthSectionProps {
  findings: FindingResponse[];
  isCompleted: boolean;
}

interface AuthStatusItem {
  mechanism: 'SPF' | 'DKIM' | 'DMARC';
  status: 'pass' | 'fail' | 'neutral' | 'none' | 'missing' | 'unknown';
  details?: string;
  finding?: FindingResponse;
}

export const AuthSection: React.FC<AuthSectionProps> = ({ findings, isCompleted }) => {
  // Extract auth findings
  const authFindings = findings.filter((f) => f.category?.toLowerCase() === 'auth');

  // Helper to determine status from finding types emitted by AuthenticationAnalyzer
  const getAuthMechanismStatus = (mech: 'spf' | 'dkim' | 'dmarc'): AuthStatusItem => {
    const finding = authFindings.find((f) => f.type?.toLowerCase().startsWith(mech));
    if (!finding) {
      // Check if missing_headers finding exists
      const missingFinding = authFindings.find((f) => f.type === 'missing_headers');
      if (missingFinding) {
        return {
          mechanism: mech.toUpperCase() as 'SPF' | 'DKIM' | 'DMARC',
          status: 'missing',
          details: 'Header omitted or unverified',
          finding: missingFinding,
        };
      }
      return {
        mechanism: mech.toUpperCase() as 'SPF' | 'DKIM' | 'DMARC',
        status: isCompleted ? 'unknown' : 'unknown',
        details: isCompleted ? 'No verification header found' : 'Check pending',
      };
    }

    const type = finding.type.toLowerCase();
    let status: AuthStatusItem['status'] = 'unknown';

    if (type.includes('pass')) {
      status = 'pass';
    } else if (type.includes('fail')) {
      status = 'fail';
    } else if (type.includes('neutral') || type.includes('none')) {
      status = 'neutral';
    }

    return {
      mechanism: mech.toUpperCase() as 'SPF' | 'DKIM' | 'DMARC',
      status,
      details: finding.description || finding.title,
      finding,
    };
  };

  const mechanisms: AuthStatusItem[] = [
    getAuthMechanismStatus('spf'),
    getAuthMechanismStatus('dkim'),
    getAuthMechanismStatus('dmarc'),
  ];

  const renderBadge = (status: AuthStatusItem['status']) => {
    switch (status) {
      case 'pass':
        return (
          <span className="badge badge-clean">
            <CheckCircle2 size={13} /> PASS
          </span>
        );
      case 'fail':
        return (
          <span className="badge badge-malicious">
            <XCircle size={13} /> FAIL
          </span>
        );
      case 'neutral':
      case 'none':
        return (
          <span className="badge badge-suspicious">
            <AlertCircle size={13} /> NEUTRAL / NONE
          </span>
        );
      case 'missing':
        return (
          <span className="badge badge-suspicious">
            <AlertCircle size={13} /> MISSING HEADER
          </span>
        );
      default:
        return (
          <span className="badge badge-unknown">
            <HelpCircle size={13} /> UNASSESSED
          </span>
        );
    }
  };

  return (
    <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
        <Shield size={18} color="var(--color-action-blue)" />
        <h2 className="text-section">Domain Authentication Verification</h2>
      </div>
      <p className="text-meta" style={{ marginBottom: 'var(--space-4)' }}>
        Interrogates inbound <code>Authentication-Results</code> headers stamped by MTAs without executing external DNS lookups.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)' }}>
        {mechanisms.map((item) => (
          <div
            key={item.mechanism}
            style={{
              padding: 'var(--space-4)',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--bg-surface-subtle)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <span style={{ fontWeight: 600, fontSize: '15px' }}>{item.mechanism}</span>
              {renderBadge(item.status)}
            </div>
            {item.finding?.title && item.finding.title !== item.mechanism && (
              <div style={{ fontWeight: 500, fontSize: '13px', marginBottom: 'var(--space-1)', color: 'var(--text-primary)' }}>
                {item.finding.title}
              </div>
            )}
            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              {item.details || 'No evidence detail'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
