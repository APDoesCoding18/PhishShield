import '@testing-library/jest-dom/vitest';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EmailUploader } from '../components/upload/EmailUploader';
import { apiClient, ApiError } from '../services/api';

describe('EmailUploader Component', () => {
  const mockOnAnalysisStarted = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders initial dropzone empty state with instructions', () => {
    render(<EmailUploader onAnalysisStarted={mockOnAnalysisStarted} />);
    expect(screen.getByText(/Drag & Drop \.eml Email File Here/i)).toBeInTheDocument();
    expect(screen.getByText(/Browse Files \(\.eml\)/i)).toBeInTheDocument();
  });

  it('validates and rejects non-.eml file selection', () => {
    render(<EmailUploader onAnalysisStarted={mockOnAnalysisStarted} />);
    const input = screen.getByLabelText(/Upload \.eml email file/i);

    const badFile = new File(['fake content'], 'test.pdf', { type: 'application/pdf' });
    fireEvent.change(input, { target: { files: [badFile] } });

    expect(
      screen.getByText(/Invalid file format: PhishShield only accepts standard RFC 822 email files \(\.eml\)\./i)
    ).toBeInTheDocument();
  });

  it('validates and accepts valid .eml file selection', () => {
    render(<EmailUploader onAnalysisStarted={mockOnAnalysisStarted} />);
    const input = screen.getByLabelText(/Upload \.eml email file/i);

    const goodFile = new File(['Subject: Test\n\nBody'], 'phish.eml', { type: 'message/rfc822' });
    fireEvent.change(input, { target: { files: [goodFile] } });

    expect(screen.getByText('phish.eml')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Analyze Email/i })).toBeInTheDocument();
  });

  it('submits file via apiClient and calls onAnalysisStarted on success', async () => {
    vi.spyOn(apiClient, 'uploadEmail').mockResolvedValueOnce({
      job_id: 'test-job-uuid-1234',
      status: 'PENDING',
    });

    render(<EmailUploader onAnalysisStarted={mockOnAnalysisStarted} />);
    const input = screen.getByLabelText(/Upload \.eml email file/i);

    const goodFile = new File(['Subject: Test\n\nBody'], 'invoice.eml', { type: 'message/rfc822' });
    fireEvent.change(input, { target: { files: [goodFile] } });

    const analyzeBtn = screen.getByRole('button', { name: /Analyze Email/i });
    fireEvent.click(analyzeBtn);

    await waitFor(() => {
      expect(apiClient.uploadEmail).toHaveBeenCalledTimes(1);
      expect(mockOnAnalysisStarted).toHaveBeenCalledWith('test-job-uuid-1234');
    });
  });

  it('displays recoverable error and allows retry when API fails', async () => {
    vi.spyOn(apiClient, 'uploadEmail').mockRejectedValueOnce(
      new ApiError(400, {
        error_code: 'UNSUPPORTED_FORMAT',
        message: 'Only .eml files are supported for this milestone',
      })
    );

    render(<EmailUploader onAnalysisStarted={mockOnAnalysisStarted} />);
    const input = screen.getByLabelText(/Upload \.eml email file/i);

    const goodFile = new File(['Subject: Test\n\nBody'], 'invoice.eml', { type: 'message/rfc822' });
    fireEvent.change(input, { target: { files: [goodFile] } });

    const analyzeBtn = screen.getByRole('button', { name: /Analyze Email/i });
    fireEvent.click(analyzeBtn);

    await waitFor(() => {
      expect(screen.getByText(/Submission Failed \(UNSUPPORTED_FORMAT\)/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
    });
  });
});
