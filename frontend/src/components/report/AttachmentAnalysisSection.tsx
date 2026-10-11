import React, { useState } from 'react';
import { Paperclip, FileWarning, Copy, Check, ShieldAlert } from 'lucide-react';
import { AttachmentResponse, FindingResponse } from '../../types/api';
import { formatBytes } from '../../utils/formatters';

interface AttachmentAnalysisSectionProps {
  attachments: AttachmentResponse[];
  findings: FindingResponse[];
  isCompleted: boolean;
}

export const AttachmentAnalysisSection: React.FC<AttachmentAnalysisSectionProps> = ({
  attachments,
  findings,
  isCompleted,
}) => {
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const attachmentFindings = findings.filter((f) => f.category?.toLowerCase() === 'attachment');

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  return (
    <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <Paperclip size={18} color="var(--color-action-blue)" />
          <h2 className="text-section">Attachment Forensics ({attachments.length})</h2>
        </div>
      </div>
      <p className="text-meta" style={{ marginBottom: 'var(--space-4)' }}>
        Static forensic analysis inspecting magic byte signatures, double-extension masking, and SHA-256 cryptographic hashes.
      </p>

      {/* Attachment Threat Findings */}
      {attachmentFindings.length > 0 && (
        <div style={{ marginBottom: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          {attachmentFindings.map((f, i) => (
            <div key={i} className="alert alert-danger" style={{ fontSize: '13px' }}>
              <ShieldAlert size={16} style={{ flexShrink: 0 }} />
              <div>
                <strong>{f.title}:</strong> {f.description}
              </div>
            </div>
          ))}
        </div>
      )}

      {attachments.length === 0 ? (
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
          {isCompleted ? 'No attachments were extracted from this message.' : 'Extracting message attachments...'}
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '13px' }}>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Original Filename</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Detected Signature</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>File Size</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Flags</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>SHA-256 Hash</th>
              </tr>
            </thead>
            <tbody>
              {attachments.map((att, idx) => {
                const isMismatch = att.detected_mime_type && att.mime_type && att.detected_mime_type !== att.mime_type;
                return (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      fontSize: '13px',
                    }}
                  >
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 500 }}>
                      <span className="font-mono" style={{ color: 'var(--text-main)', wordBreak: 'break-all' }}>
                        {att.original_filename || 'unnamed_attachment'}
                      </span>
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      <div className="font-mono text-meta">
                        {att.detected_mime_type || att.mime_type || 'Unknown'}
                      </div>
                      {isMismatch && (
                        <span className="badge badge-malicious" style={{ fontSize: '10px', marginTop: '2px' }}>
                          MIME Spoof Detected
                        </span>
                      )}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-muted)' }}>
                      {formatBytes(att.size)}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      {att.is_executable ? (
                        <span className="badge badge-malicious" style={{ fontSize: '11px' }}>
                          <FileWarning size={12} /> Executable Payload
                        </span>
                      ) : (
                        <span className="badge badge-clean" style={{ fontSize: '11px' }}>
                          Non-executable
                        </span>
                      )}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span
                          className="font-mono text-meta"
                          style={{
                            maxWidth: '180px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                          title={att.sha256}
                        >
                          {att.sha256}
                        </span>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleCopyHash(att.sha256)}
                          title="Copy SHA-256 Hash"
                          style={{ padding: '3px 6px' }}
                        >
                          {copiedHash === att.sha256 ? <Check size={11} color="var(--risk-clean)" /> : <Copy size={11} />}
                        </button>
                      </div>
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
