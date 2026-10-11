import {
  AnalysisJobResponse,
  AnalysisJobDetailResponse,
  AnalysisHistoryItemResponse,
  RiskResultResponse,
  EmailResponse,
  UrlResponse,
  AttachmentResponse,
  ErrorResponse,
} from '../types/api';

const API_BASE = '/api/v1';

export class ApiError extends Error {
  public errorCode: string;
  public status: number;
  public details?: string | null;

  constructor(status: number, errorData: ErrorResponse) {
    super(errorData.message || 'An unexpected error occurred during request processing');
    this.name = 'ApiError';
    this.status = status;
    this.errorCode = errorData.error_code || 'API_ERROR';
    this.details = errorData.details;
  }
}

async function parseResponseOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: ErrorResponse;
    try {
      errorData = await response.json();
    } catch {
      errorData = {
        error_code: `HTTP_${response.status}`,
        message: `Request failed with HTTP status ${response.status} (${response.statusText})`,
      };
    }
    throw new ApiError(response.status, errorData);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  /**
   * Securely upload .eml file as multipart/form-data with field name 'file'
   */
  async uploadEmail(file: File): Promise<AnalysisJobResponse> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/analyses`, {
        method: 'POST',
        body: formData,
      });
      return await parseResponseOrThrow<AnalysisJobResponse>(response);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        throw err;
      }
      throw new ApiError(0, {
        error_code: 'NETWORK_ERROR',
        message: 'Unable to connect to the PhishShield analysis server. Please check your network connection.',
      });
    }
  },

  /**
   * Get job execution status and progress
   */
  async getJobStatus(jobId: string): Promise<AnalysisJobDetailResponse> {
    try {
      const response = await fetch(`${API_BASE}/analyses/${encodeURIComponent(jobId)}`);
      return await parseResponseOrThrow<AnalysisJobDetailResponse>(response);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        throw err;
      }
      throw new ApiError(0, {
        error_code: 'NETWORK_ERROR',
        message: 'Failed to retrieve analysis status.',
      });
    }
  },

  /**
   * Get risk score and evidence findings
   */
  async getJobResult(jobId: string): Promise<RiskResultResponse> {
    const response = await fetch(`${API_BASE}/analyses/${encodeURIComponent(jobId)}/result`);
    return await parseResponseOrThrow<RiskResultResponse>(response);
  },

  /**
   * Get parsed email headers and body
   */
  async getJobEmail(jobId: string): Promise<EmailResponse> {
    const response = await fetch(`${API_BASE}/analyses/${encodeURIComponent(jobId)}/email`);
    return await parseResponseOrThrow<EmailResponse>(response);
  },

  /**
   * Get extracted URLs
   */
  async getJobUrls(jobId: string): Promise<UrlResponse[]> {
    const response = await fetch(`${API_BASE}/analyses/${encodeURIComponent(jobId)}/urls`);
    return await parseResponseOrThrow<UrlResponse[]>(response);
  },

  /**
   * Get attachment forensic records
   */
  async getJobAttachments(jobId: string): Promise<AttachmentResponse[]> {
    const response = await fetch(`${API_BASE}/analyses/${encodeURIComponent(jobId)}/attachments`);
    return await parseResponseOrThrow<AttachmentResponse[]>(response);
  },

  /**
   * Health check endpoint
   */
  async checkHealth(): Promise<{ status: string; database: string }> {
    const response = await fetch(`${API_BASE}/health`);
    return await parseResponseOrThrow<{ status: string; database: string }>(response);
  },

  /**
   * Get historical analysis jobs from backend
   */
  async listAnalyses(params?: { limit?: number; offset?: number; status?: string }): Promise<AnalysisHistoryItemResponse[]> {
    const searchParams = new URLSearchParams();
    if (params?.limit !== undefined) searchParams.set('limit', params.limit.toString());
    if (params?.offset !== undefined) searchParams.set('offset', params.offset.toString());
    if (params?.status) searchParams.set('status', params.status);

    const query = searchParams.toString();
    const url = query ? `${API_BASE}/analyses?${query}` : `${API_BASE}/analyses`;
    const response = await fetch(url);
    return await parseResponseOrThrow<AnalysisHistoryItemResponse[]>(response);
  },
};
