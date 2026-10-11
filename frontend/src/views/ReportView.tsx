import React, { useEffect, useState, useRef, useCallback } from 'react';
import { apiClient, ApiError } from '../services/api';
import { historyStorage } from '../services/historyStorage';
import {
  AnalysisJobDetailResponse,
  RiskResultResponse,
  EmailResponse,
  UrlResponse,
  AttachmentResponse,
} from '../types/api';
import { ReportHeader } from '../components/report/ReportHeader';
import { VerdictSummary } from '../components/report/VerdictSummary';
import { AuthSection } from '../components/report/AuthSection';
import { ContentFindingsSection } from '../components/report/ContentFindingsSection';
import { UrlAnalysisSection } from '../components/report/UrlAnalysisSection';
import { AttachmentAnalysisSection } from '../components/report/AttachmentAnalysisSection';
import { EmailMetadataSection } from '../components/report/EmailMetadataSection';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ReportViewProps {
  jobId: string;
  onNewAnalysis: () => void;
}

export const ReportView: React.FC<ReportViewProps> = ({ jobId, onNewAnalysis }) => {
  const [jobDetail, setJobDetail] = useState<AnalysisJobDetailResponse | null>(null);
  const [riskResult, setRiskResult] = useState<RiskResultResponse | null>(null);
  const [emailData, setEmailData] = useState<EmailResponse | null>(null);
  const [urls, setUrls] = useState<UrlResponse[]>([]);
  const [attachments, setAttachments] = useState<AttachmentResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(false);

  // Retrieve matching item from client-side history if present
  const storedItem = historyStorage.getItems().find((i) => i.jobId === jobId);

  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef<boolean>(true);

  const fetchCompletedEvidence = useCallback(async (currentJobId: string) => {
    try {
      const [resResult, resEmail, resUrls, resAttachments] = await Promise.allSettled([
        apiClient.getJobResult(currentJobId),
        apiClient.getJobEmail(currentJobId),
        apiClient.getJobUrls(currentJobId),
        apiClient.getJobAttachments(currentJobId),
      ]);

      if (!isMountedRef.current) return;

      if (resResult.status === 'fulfilled') {
        setRiskResult(resResult.value);
        // Sync history cache
        historyStorage.updateItemStatus(
          currentJobId,
          'COMPLETED',
          resResult.value.verdict,
          resResult.value.score
        );
      }
      if (resEmail.status === 'fulfilled') {
        setEmailData(resEmail.value);
      }
      if (resUrls.status === 'fulfilled') {
        setUrls(resUrls.value);
      }
      if (resAttachments.status === 'fulfilled') {
        setAttachments(resAttachments.value);
      }
    } catch {
      // Partial failure handled gracefully
    }
  }, []);

  const pollJobStatus = useCallback(async () => {
    if (!isMountedRef.current) return;
    setIsPolling(true);
    setError(null);

    try {
      const detail = await apiClient.getJobStatus(jobId);
      if (!isMountedRef.current) return;
      setJobDetail(detail);

      if (detail.status === 'COMPLETED') {
        await fetchCompletedEvidence(jobId);
        if (!isMountedRef.current) return;
        setIsLoading(false);
        setIsPolling(false);
      } else if (detail.status === 'FAILED') {
        setIsLoading(false);
        setIsPolling(false);
        historyStorage.updateItemStatus(jobId, 'FAILED', 'error');
      } else {
        // PENDING or PROCESSING: schedule next poll in 1500ms
        setIsPolling(false);
        pollTimeoutRef.current = setTimeout(pollJobStatus, 1500);
      }
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      setIsLoading(false);
      setIsPolling(false);
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to poll analysis progress. The server may be unreachable.');
      }
    }
  }, [jobId, fetchCompletedEvidence]);

  useEffect(() => {
    isMountedRef.current = true;
    setIsLoading(true);
    setError(null);

    pollJobStatus();

    return () => {
      isMountedRef.current = false;
      if (pollTimeoutRef.current) {
        clearTimeout(pollTimeoutRef.current);
      }
    };
  }, [jobId, pollJobStatus]);

  const isCompleted = jobDetail?.status === 'COMPLETED';
  const allFindings = riskResult?.findings || [];

  return (
    <div className="report-view-container">
      {/* 1. Header with Metadata */}
      <ReportHeader
        jobId={jobId}
        originalFilename={storedItem?.originalFilename}
        status={jobDetail?.status || 'PENDING'}
        createdAt={jobDetail?.created_at || storedItem?.uploadedAt}
        updatedAt={jobDetail?.updated_at}
        onBackToDashboard={onNewAnalysis}
        onRefresh={() => pollJobStatus()}
        isPolling={isPolling}
      />

      {/* 2. Error Message */}
      {error && (
        <div className="alert alert-danger" style={{ marginBottom: 'var(--space-6)' }} role="alert">
          <AlertCircle size={20} />
          <div style={{ flex: 1 }}>
            <strong>Analysis Request Error:</strong> {error}
          </div>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => pollJobStatus()}>
            <RefreshCw size={13} /> Retry
          </button>
        </div>
      )}

      {/* 3. In-flight Lifecycle Progress Banner */}
      {jobDetail && (jobDetail.status === 'PENDING' || jobDetail.status === 'PROCESSING') && (
        <div
          className="card"
          style={{
            padding: 'var(--space-6)',
            marginBottom: 'var(--space-6)',
            textAlign: 'center',
            backgroundColor: 'var(--bg-surface-elevated)',
          }}
        >
          <div className="spinner" style={{ width: '32px', height: '32px', margin: '0 auto var(--space-3)' }} />
          <h2 className="text-section" style={{ marginBottom: 'var(--space-2)' }}>
            {jobDetail.status === 'PROCESSING'
              ? 'Analyzing Email Evidence...'
              : 'Job Queued in Sandbox...'}
          </h2>
          <p className="text-meta" style={{ maxWidth: '480px', margin: '0 auto var(--space-4)' }}>
            Modular static analyzers are parsing MIME structures, testing SPF/DKIM/DMARC headers, and inspecting attachments.
          </p>
          <div style={{ maxWidth: '320px', margin: '0 auto' }}>
            <div
              style={{
                height: '8px',
                backgroundColor: 'var(--border-subtle)',
                borderRadius: 'var(--radius-full)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${jobDetail.progress}%`,
                  backgroundColor: 'var(--color-action-blue)',
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
            <div className="font-mono text-meta" style={{ marginTop: '6px' }}>
              Progress: {jobDetail.progress}%
            </div>
          </div>
        </div>
      )}

      {/* 4. Failure Lifecycle State */}
      {jobDetail && jobDetail.status === 'FAILED' && (
        <div
          className="card"
          style={{
            borderLeft: '5px solid var(--risk-high)',
            padding: 'var(--space-6)',
            marginBottom: 'var(--space-6)',
          }}
        >
          <h2 className="text-section" style={{ color: 'var(--risk-high)', marginBottom: 'var(--space-2)' }}>
            Analysis Job Failed
          </h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>
            An unrecoverable error occurred while executing the static analysis pipeline on this file.
          </p>
          <button type="button" className="btn btn-primary btn-sm" onClick={onNewAnalysis}>
            Submit Another Email
          </button>
        </div>
      )}

      {/* 5. Verdict and Risk Summary */}
      {(isCompleted || riskResult) && (
        <VerdictSummary riskResult={riskResult} isLoading={isLoading && !riskResult} />
      )}

      {/* 6. Parsed Email Headers */}
      <EmailMetadataSection email={emailData} isCompleted={isCompleted} />

      {/* 7. Domain Authentication Evidence */}
      <AuthSection findings={allFindings} isCompleted={isCompleted} />

      {/* 8. Content Heuristics & Phishing Indicators */}
      <ContentFindingsSection findings={allFindings} isCompleted={isCompleted} />

      {/* 9. URL Analysis & Defanged Destinations */}
      <UrlAnalysisSection urls={urls} findings={allFindings} isCompleted={isCompleted} />

      {/* 10. Attachment Forensic Metadata */}
      <AttachmentAnalysisSection attachments={attachments} findings={allFindings} isCompleted={isCompleted} />
    </div>
  );
};
