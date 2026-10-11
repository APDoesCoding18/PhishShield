import '@testing-library/jest-dom/vitest';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ReportView } from '../views/ReportView';
import { apiClient } from '../services/api';

describe('ReportView Lifecycle & Evidence Presentation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders pending/processing state when job is processing', async () => {
    vi.spyOn(apiClient, 'getJobStatus').mockResolvedValueOnce({
      job_id: 'job-pending-1',
      status: 'PROCESSING',
      progress: 50,
      created_at: '2026-10-11T12:00:00Z',
      updated_at: '2026-10-11T12:00:02Z',
    });

    const { unmount } = render(<ReportView jobId="job-pending-1" onNewAnalysis={vi.fn()} />);

    expect(screen.getByText('Job ID: job-pending-1')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Analyzing Email Evidence\.\.\./i)).toBeInTheDocument();
      expect(screen.getByText(/Progress: 50%/i)).toBeInTheDocument();
    });
    unmount();
  });

  it('renders failed state when job has failed in the pipeline', async () => {
    vi.spyOn(apiClient, 'getJobStatus').mockResolvedValueOnce({
      job_id: 'job-failed-1',
      status: 'FAILED',
      progress: 0,
      created_at: '2026-10-11T12:00:00Z',
      updated_at: '2026-10-11T12:00:02Z',
    });

    const { unmount } = render(<ReportView jobId="job-failed-1" onNewAnalysis={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Analysis Job Failed/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Submit Another Email/i })).toBeInTheDocument();
    });
    unmount();
  });

  it('renders high-risk completed report with verdict, findings, defanged URLs, and attachments', async () => {
    vi.spyOn(apiClient, 'getJobStatus').mockResolvedValue({
      job_id: 'job-completed-high',
      status: 'COMPLETED',
      progress: 100,
      created_at: '2026-10-11T12:00:00Z',
      updated_at: '2026-10-11T12:00:05Z',
    });

    vi.spyOn(apiClient, 'getJobResult').mockResolvedValue({
      verdict: 'malicious',
      score: 16.0,
      severity: 'critical',
      rationale: 'Executable Attachment Detected (critical). SPF check resulted in fail.',
      findings: [
        {
          type: 'executable_attachment',
          category: 'attachment',
          severity: 'critical',
          title: 'Executable Attachment Detected',
          description: 'Attachment contains executable PE headers.',
          evidence: JSON.stringify({ magic: 'MZ', filename: 'invoice.pdf.exe' }),
        },
        {
          type: 'spf_fail',
          category: 'auth',
          severity: 'high',
          title: 'SPF Failed',
          description: 'SPF check resulted in fail',
        },
        {
          type: 'credential_request_indicator',
          category: 'content',
          severity: 'high',
          title: 'Suspicious Credential Request',
          description: 'Email asks for login password or account verification.',
        },
      ],
    });

    vi.spyOn(apiClient, 'getJobEmail').mockResolvedValue({
      sender: 'attacker@evil.com',
      recipient: 'victim@target.org',
      subject: 'URGENT: Password Reset Required',
      date_header: 'Sun, 11 Oct 2026 12:00:00 GMT',
      body_text: 'Click here to login and reset your account.',
      body_html: null,
    });

    vi.spyOn(apiClient, 'getJobUrls').mockResolvedValue([
      {
        url: 'http://192.168.1.50/login',
        normalized_url: 'http://192.168.1.50/login',
        domain: '192.168.1.50',
        is_ip: true,
      },
    ]);

    vi.spyOn(apiClient, 'getJobAttachments').mockResolvedValue([
      {
        original_filename: 'invoice.pdf.exe',
        mime_type: 'application/pdf',
        detected_mime_type: 'application/x-msdownload',
        is_executable: true,
        size: 10240,
        sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      },
    ]);

    render(<ReportView jobId="job-completed-high" onNewAnalysis={vi.fn()} />);

    await waitFor(
      () => {
        // Verdict and Score
        expect(screen.getByText(/Verdict: MALICIOUS/i)).toBeInTheDocument();
        expect(screen.getByText(/Calculated Score: 16.0 \/ 100/i)).toBeInTheDocument();
        expect(screen.getByText(/Severity: critical/i)).toBeInTheDocument();

        // Email header
        expect(screen.getByText('attacker@evil.com')).toBeInTheDocument();
        expect(screen.getByText('URGENT: Password Reset Required')).toBeInTheDocument();

        // Auth mechanism evaluation
        expect(screen.getByText('SPF Failed')).toBeInTheDocument();

        // Defanged URL display
        expect(screen.getByText(/hxxp:\/\/192\[\.\]168\[\.\]1\[\.\]50\/login/i)).toBeInTheDocument();
        expect(screen.getByText('Direct IP Destination')).toBeInTheDocument();

        // Attachment details
        expect(screen.getByText('invoice.pdf.exe')).toBeInTheDocument();
        expect(screen.getByText('Executable Payload')).toBeInTheDocument();
        expect(screen.getByText('MIME Spoof Detected')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('renders clean verdict when analysis detects no threats', async () => {
    vi.spyOn(apiClient, 'getJobStatus').mockResolvedValue({
      job_id: 'job-completed-clean',
      status: 'COMPLETED',
      progress: 100,
      created_at: '2026-10-11T12:00:00Z',
      updated_at: '2026-10-11T12:00:05Z',
    });

    vi.spyOn(apiClient, 'getJobResult').mockResolvedValue({
      verdict: 'clean',
      score: 0.0,
      severity: 'informational',
      rationale: 'No suspicious indicators were detected across all analysis modules.',
      findings: [],
    });

    vi.spyOn(apiClient, 'getJobEmail').mockResolvedValue({
      sender: 'colleague@company.com',
      recipient: 'employee@company.com',
      subject: 'Team Lunch Agenda',
      date_header: 'Sun, 11 Oct 2026 12:00:00 GMT',
      body_text: 'See you tomorrow at noon.',
      body_html: null,
    });

    vi.spyOn(apiClient, 'getJobUrls').mockResolvedValue([]);
    vi.spyOn(apiClient, 'getJobAttachments').mockResolvedValue([]);

    render(<ReportView jobId="job-completed-clean" onNewAnalysis={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Verdict: CLEAN/i)).toBeInTheDocument();
      expect(screen.getByText(/Calculated Score: 0.0 \/ 100/i)).toBeInTheDocument();
      expect(screen.getByText(/No attachments were extracted from this message\./i)).toBeInTheDocument();
      expect(screen.getByText(/No hyperlinks or URLs were extracted from the email\./i)).toBeInTheDocument();
    });
  });

  it('handles API failure and allows retry', async () => {
    vi.spyOn(apiClient, 'getJobStatus').mockRejectedValueOnce(
      new Error('Connection timed out')
    );

    render(<ReportView jobId="job-network-err" onNewAnalysis={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Analysis Request Error:/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
    });
  });

  it('renders correctly when verdict is unknown and score/rationale are omitted', async () => {
    vi.spyOn(apiClient, 'getJobStatus').mockResolvedValue({
      job_id: 'job-edge-case-with-very-long-unique-uuid-identifier-0123456789abcdef',
      status: 'COMPLETED',
      progress: 100,
      created_at: '2026-10-11T12:00:00Z',
      updated_at: '2026-10-11T12:00:05Z',
    });

    vi.spyOn(apiClient, 'getJobResult').mockResolvedValue({
      verdict: 'unknown',
      score: null as any,
      severity: null as any,
      rationale: null as any,
      findings: [],
    });

    vi.spyOn(apiClient, 'getJobEmail').mockResolvedValue(null as any);
    vi.spyOn(apiClient, 'getJobUrls').mockResolvedValue([]);
    vi.spyOn(apiClient, 'getJobAttachments').mockResolvedValue([]);

    render(
      <ReportView
        jobId="job-edge-case-with-very-long-unique-uuid-identifier-0123456789abcdef"
        onNewAnalysis={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Verdict: UNKNOWN/i)).toBeInTheDocument();
      expect(screen.getByText(/Calculated Score: Unavailable/i)).toBeInTheDocument();
      expect(screen.getByText(/No automated rationale was returned for this analysis/i)).toBeInTheDocument();
      expect(screen.getByText(/job-edge-case-with-very-long-unique-uuid-identifier-0123456789abcdef/i)).toBeInTheDocument();
    });
  });
});
