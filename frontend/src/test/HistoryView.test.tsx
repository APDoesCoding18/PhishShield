import '@testing-library/jest-dom/vitest';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { HistoryView } from '../views/HistoryView';
import { apiClient } from '../services/api';
import { historyStorage } from '../services/historyStorage';

describe('HistoryView — Analysis History Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders loading state initially while fetching history', async () => {
    vi.spyOn(apiClient, 'listAnalyses').mockImplementation(
      () => new Promise(() => {}) // never resolves to keep loading state active
    );

    render(<HistoryView onSelectJob={vi.fn()} onNewAnalysis={vi.fn()} />);

    expect(screen.getByText(/Loading analysis history from server\.\.\./i)).toBeInTheDocument();
  });

  it('renders empty state when no analysis records are found', async () => {
    vi.spyOn(apiClient, 'listAnalyses').mockResolvedValueOnce([]);

    const onNewAnalysis = vi.fn();
    render(<HistoryView onSelectJob={vi.fn()} onNewAnalysis={onNewAnalysis} />);

    await waitFor(() => {
      expect(screen.getByText('No Analysis History Found')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Start First Analysis/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Start First Analysis/i }));
    expect(onNewAnalysis).toHaveBeenCalled();
  });

  it('renders populated records with actual backend fields and handles report navigation', async () => {
    const onSelectJob = vi.fn();

    vi.spyOn(apiClient, 'listAnalyses').mockResolvedValueOnce([
      {
        job_id: 'job-history-uuid-1',
        original_filename: 'suspicious_invoice.eml',
        status: 'COMPLETED',
        created_at: '2026-10-11T14:30:00Z',
        updated_at: '2026-10-11T14:30:10Z',
        verdict: 'malicious',
        score: 18.5,
        severity: 'critical',
      },
      {
        job_id: 'job-history-uuid-2',
        original_filename: 'team_newsletter.eml',
        status: 'COMPLETED',
        created_at: '2026-10-11T13:00:00Z',
        updated_at: '2026-10-11T13:00:05Z',
        verdict: 'clean',
        score: 0.0,
        severity: 'informational',
      },
      {
        job_id: 'job-history-uuid-3',
        original_filename: null,
        status: 'PROCESSING',
        created_at: '2026-10-11T15:00:00Z',
        updated_at: '2026-10-11T15:00:02Z',
        verdict: null,
        score: null,
        severity: null,
      },
    ]);

    render(<HistoryView onSelectJob={onSelectJob} onNewAnalysis={vi.fn()} />);

    await waitFor(() => {
      // Filenames and fallbacks (rendered in both desktop table and mobile list)
      expect(screen.getAllByText('suspicious_invoice.eml').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('team_newsletter.eml').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Unknown Email File').length).toBeGreaterThanOrEqual(1);

      // Verdicts and badges
      expect(screen.getAllByText('Malicious').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Clean / Low Risk').length).toBeGreaterThanOrEqual(1);

      // Scores
      expect(screen.getAllByText('18.5 / 100').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('0.0 / 100').length).toBeGreaterThanOrEqual(1);

      // Action button
      const openButtons = screen.getAllByRole('button', { name: /Open analysis report for job job-history-uuid-1/i });
      expect(openButtons.length).toBeGreaterThan(0);
      fireEvent.click(openButtons[0]);
      expect(onSelectJob).toHaveBeenCalledWith('job-history-uuid-1');
    });
  });

  it('supports search and status/verdict filtering', async () => {
    vi.spyOn(apiClient, 'listAnalyses').mockResolvedValueOnce([
      {
        job_id: 'job-alpha-123',
        original_filename: 'security_update.eml',
        status: 'COMPLETED',
        created_at: '2026-10-11T12:00:00Z',
        updated_at: '2026-10-11T12:00:05Z',
        verdict: 'clean',
        score: 2.0,
        severity: 'low',
      },
      {
        job_id: 'job-beta-456',
        original_filename: 'payroll_alert.eml',
        status: 'COMPLETED',
        created_at: '2026-10-11T12:30:00Z',
        updated_at: '2026-10-11T12:30:10Z',
        verdict: 'malicious',
        score: 15.0,
        severity: 'high',
      },
    ]);

    render(<HistoryView onSelectJob={vi.fn()} onNewAnalysis={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getAllByText('security_update.eml').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('payroll_alert.eml').length).toBeGreaterThanOrEqual(1);
    });

    // Search query
    const searchInput = screen.getByPlaceholderText(/Search by filename or Job ID\.\.\./i);
    fireEvent.change(searchInput, { target: { value: 'payroll' } });

    expect(screen.queryByText('security_update.eml')).not.toBeInTheDocument();
    expect(screen.getAllByText('payroll_alert.eml').length).toBeGreaterThanOrEqual(1);

    // Reset search
    fireEvent.change(searchInput, { target: { value: '' } });
    expect(screen.getAllByText('security_update.eml').length).toBeGreaterThanOrEqual(1);
  });

  it('handles backend network errors and falls back to local history with retry option', async () => {
    // Populate local storage
    historyStorage.addItem({
      jobId: 'local-cached-job',
      originalFilename: 'cached_offline.eml',
      fileSizeBytes: 2048,
      uploadedAt: '2026-10-11T10:00:00Z',
      status: 'COMPLETED',
      verdict: 'malicious',
      score: 12.0,
    });

    vi.spyOn(apiClient, 'listAnalyses').mockRejectedValueOnce(
      new Error('503 Service Unavailable')
    );

    render(<HistoryView onSelectJob={vi.fn()} onNewAnalysis={vi.fn()} />);

    await waitFor(() => {
      // Shows error banner
      expect(screen.getByText(/Failed to fetch backend records:/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
      // Falls back to local item
      expect(screen.getAllByText('cached_offline.eml').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/local-cached-job/i).length).toBeGreaterThanOrEqual(1);
    });
  });
});
