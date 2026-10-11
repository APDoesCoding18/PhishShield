export interface StoredAnalysisItem {
  jobId: string;
  originalFilename: string;
  fileSizeBytes: number;
  uploadedAt: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  verdict?: 'clean' | 'suspicious' | 'malicious' | 'unknown' | 'error' | string;
  score?: number;
}

const STORAGE_KEY = 'phishshield_analyses_history';

export const historyStorage = {
  getItems(): StoredAnalysisItem[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (!data) return [];
      return JSON.parse(data) as StoredAnalysisItem[];
    } catch {
      return [];
    }
  },

  addItem(item: StoredAnalysisItem): void {
    try {
      const current = this.getItems().filter((i) => i.jobId !== item.jobId);
      const updated = [item, ...current].slice(0, 50); // Keep 50 most recent
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch {
      // Storage quota or parsing safety
    }
  },

  updateItemStatus(jobId: string, status: StoredAnalysisItem['status'], verdict?: string, score?: number): void {
    try {
      const items = this.getItems().map((item) => {
        if (item.jobId === jobId) {
          return {
            ...item,
            status,
            verdict: verdict !== undefined ? verdict : item.verdict,
            score: score !== undefined ? score : item.score,
          };
        }
        return item;
      });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {
      // Ignore storage errors
    }
  },

  clearHistory(): void {
    localStorage.removeItem(STORAGE_KEY);
  },
};
