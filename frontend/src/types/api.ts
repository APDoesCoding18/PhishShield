export type JobStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface AnalysisJobResponse {
  job_id: string;
  status: JobStatus;
}

export interface AnalysisJobDetailResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface AnalysisHistoryItemResponse {
  job_id: string;
  original_filename?: string | null;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  verdict?: 'clean' | 'suspicious' | 'malicious' | 'unknown' | 'error' | string | null;
  score?: number | null;
  severity?: string | null;
}

export interface FindingResponse {
  type: string;
  category: string;
  severity: 'informational' | 'low' | 'medium' | 'high' | 'critical' | string;
  title: string;
  description?: string | null;
  evidence?: string | null;
}

export interface RiskResultResponse {
  verdict: 'clean' | 'suspicious' | 'malicious' | 'unknown' | 'error' | string;
  score: number;
  severity: string;
  rationale: string;
  findings: FindingResponse[];
}

export interface EmailResponse {
  sender?: string | null;
  recipient?: string | null;
  subject?: string | null;
  date_header?: string | null;
  body_text?: string | null;
  body_html?: string | null;
}

export interface UrlResponse {
  url: string;
  normalized_url?: string | null;
  domain?: string | null;
  is_ip: boolean;
}

export interface AttachmentResponse {
  original_filename?: string | null;
  mime_type?: string | null;
  detected_mime_type?: string | null;
  is_executable: boolean;
  size: number;
  sha256: string;
}

export interface ErrorResponse {
  error_code: string;
  message: string;
  details?: string | null;
}
