import React, { useState } from 'react';
import { Mail, ChevronDown, ChevronUp, FileCode } from 'lucide-react';
import { EmailResponse } from '../../types/api';

interface EmailMetadataSectionProps {
  email?: EmailResponse | null;
  isCompleted: boolean;
}

export const EmailMetadataSection: React.FC<EmailMetadataSectionProps> = ({ email, isCompleted }) => {
  const [showBody, setShowBody] = useState(false);

  if (!email && isCompleted) {
    return null;
  }

  return (
    <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <Mail size={18} color="var(--color-action-blue)" />
          <h2 className="text-section">Parsed Email Headers & Identity</h2>
        </div>
      </div>

      {!email ? (
        <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Parsing header envelope...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--space-3)' }}>
            <div>
              <span className="text-meta" style={{ display: 'block', marginBottom: '2px' }}>Sender (From):</span>
              <span className="font-mono" style={{ color: 'var(--text-main)', fontSize: '13px', wordBreak: 'break-all' }}>
                {email.sender || 'Not specified'}
              </span>
            </div>

            <div>
              <span className="text-meta" style={{ display: 'block', marginBottom: '2px' }}>Recipient (To):</span>
              <span className="font-mono" style={{ color: 'var(--text-main)', fontSize: '13px', wordBreak: 'break-all' }}>
                {email.recipient || 'Not specified'}
              </span>
            </div>

            <div style={{ gridColumn: '1 / -1' }}>
              <span className="text-meta" style={{ display: 'block', marginBottom: '2px' }}>Subject Line:</span>
              <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '14px' }}>
                {email.subject || '(No subject provided)'}
              </span>
            </div>

            {email.date_header && (
              <div style={{ gridColumn: '1 / -1' }}>
                <span className="text-meta" style={{ display: 'block', marginBottom: '2px' }}>Date Stamped:</span>
                <span className="text-meta">{email.date_header}</span>
              </div>
            )}
          </div>

          {/* Safe Plain Text Body Inspection Toggle */}
          {(email.body_text || email.body_html) && (
            <div style={{ marginTop: 'var(--space-2)', paddingTop: 'var(--space-3)', borderTop: '1px solid var(--border-subtle)' }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setShowBody(!showBody)}
                style={{ fontSize: '12px' }}
              >
                <FileCode size={13} />
                <span>{showBody ? 'Hide Normalized Email Body' : 'Inspect Normalized Email Body (Text)'}</span>
                {showBody ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </button>

              {showBody && (
                <div style={{ marginTop: 'var(--space-3)' }}>
                  <p className="text-meta" style={{ marginBottom: '6px' }}>
                    Rendered securely as escaped plain text to prevent script or DOM execution.
                  </p>
                  <pre
                    className="font-mono text-meta"
                    style={{
                      padding: 'var(--space-3)',
                      backgroundColor: 'var(--bg-page)',
                      borderRadius: 'var(--radius-sm)',
                      maxHeight: '260px',
                      overflowY: 'auto',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {email.body_text || '(Only HTML structure was present in message)'}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
