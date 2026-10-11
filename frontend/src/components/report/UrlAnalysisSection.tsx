import React, { useState } from 'react';
import { Link2, Copy, Check, AlertOctagon } from 'lucide-react';
import { UrlResponse, FindingResponse } from '../../types/api';
import { defangUrl } from '../../utils/formatters';

interface UrlAnalysisSectionProps {
  urls: UrlResponse[];
  findings: FindingResponse[];
  isCompleted: boolean;
}

export const UrlAnalysisSection: React.FC<UrlAnalysisSectionProps> = ({
  urls,
  findings,
  isCompleted,
}) => {
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);

  const urlFindings = findings.filter((f) => f.category?.toLowerCase() === 'url');

  const handleCopy = (urlText: string) => {
    navigator.clipboard.writeText(urlText);
    setCopiedUrl(urlText);
    setTimeout(() => setCopiedUrl(null), 2000);
  };

  return (
    <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <Link2 size={18} color="var(--color-action-blue)" />
          <h2 className="text-section">Extracted URLs & Destinations ({urls.length})</h2>
        </div>
      </div>
      <p className="text-meta" style={{ marginBottom: 'var(--space-4)' }}>
        All extracted links are defanged (e.g. <code>hxxps://</code> and <code>[.]</code>) to prevent accidental execution. Live external network requests are restricted.
      </p>

      {/* URL Specific Threat Findings if any */}
      {urlFindings.length > 0 && (
        <div style={{ marginBottom: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          {urlFindings.map((f, i) => (
            <div key={i} className="alert alert-warning" style={{ fontSize: '13px' }}>
              <AlertOctagon size={16} style={{ flexShrink: 0 }} />
              <div>
                <strong>{f.title}:</strong> {f.description}
              </div>
            </div>
          ))}
        </div>
      )}

      {urls.length === 0 ? (
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
          {isCompleted ? 'No hyperlinks or URLs were extracted from the email.' : 'Scanning for URLs...'}
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '13px' }}>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Defanged URL</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Domain</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>IP Address Flag</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {urls.map((u, idx) => {
                const defanged = defangUrl(u.url);
                return (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      fontSize: '13px',
                    }}
                  >
                    <td style={{ padding: 'var(--space-3) var(--space-4)', maxWidth: '380px' }}>
                      <div
                        className="font-mono"
                        style={{
                          wordBreak: 'break-all',
                          color: 'var(--text-main)',
                        }}
                      >
                        {defanged}
                      </div>
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }} className="font-mono text-meta">
                      {u.domain || 'N/A'}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      {u.is_ip ? (
                        <span className="badge badge-malicious" style={{ fontSize: '11px' }}>
                          Direct IP Destination
                        </span>
                      ) : (
                        <span className="badge badge-clean" style={{ fontSize: '11px' }}>
                          Hostname
                        </span>
                      )}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'right' }}>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleCopy(defanged)}
                        title="Copy defanged URL"
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                      >
                        {copiedUrl === defanged ? <Check size={12} color="var(--risk-clean)" /> : <Copy size={12} />}
                        <span>{copiedUrl === defanged ? 'Copied' : 'Copy'}</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
