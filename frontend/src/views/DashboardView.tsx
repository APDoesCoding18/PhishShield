import React, { useState } from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmailUploader } from '../components/upload/EmailUploader';
import { RecentAnalysesList } from '../components/dashboard/RecentAnalysesList';
import { historyStorage } from '../services/historyStorage';

interface DashboardViewProps {
  onAnalysisStarted: (jobId: string) => void;
  onViewAllHistory: () => void;
  onSelectJob: (jobId: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onAnalysisStarted,
  onViewAllHistory,
  onSelectJob,
}) => {
  const [recentItems] = useState(() => historyStorage.getItems());

  return (
    <div>
      <PageHeader
        title="Email Analysis Dashboard"
        description="Upload suspicious RFC 822 (.eml) emails for automated multi-vector forensic sandboxing and risk scoring."
      />

      {/* Dominant File Upload Area */}
      <EmailUploader onAnalysisStarted={onAnalysisStarted} />

      {/* Optional Recent Submissions Preview */}
      <RecentAnalysesList
        items={recentItems}
        onSelectJob={onSelectJob}
        onViewAllHistory={onViewAllHistory}
      />
    </div>
  );
};
