import React, { useState } from 'react';
import { AppShell, NavTab } from './components/layout/AppShell';
import { DashboardView } from './views/DashboardView';
import { ReportView } from './views/ReportView';
import { HistoryView } from './views/HistoryView';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const handleAnalysisStarted = (jobId: string) => {
    setSelectedJobId(jobId);
    setActiveTab('report');
  };

  const handleSelectJob = (jobId: string) => {
    setSelectedJobId(jobId);
    setActiveTab('report');
  };

  const handleNewAnalysis = () => {
    setActiveTab('dashboard');
  };

  return (
    <AppShell
      activeTab={activeTab}
      onNavigate={setActiveTab}
      reportAvailable={selectedJobId !== null}
    >
      {activeTab === 'dashboard' && (
        <DashboardView
          onAnalysisStarted={handleAnalysisStarted}
          onViewAllHistory={() => setActiveTab('history')}
          onSelectJob={handleSelectJob}
        />
      )}

      {activeTab === 'report' && (
        selectedJobId ? (
          <ReportView jobId={selectedJobId} onNewAnalysis={handleNewAnalysis} />
        ) : (
          <DashboardView
            onAnalysisStarted={handleAnalysisStarted}
            onViewAllHistory={() => setActiveTab('history')}
            onSelectJob={handleSelectJob}
          />
        )
      )}

      {activeTab === 'history' && (
        <HistoryView
          onSelectJob={handleSelectJob}
          onNewAnalysis={handleNewAnalysis}
        />
      )}
    </AppShell>
  );
};

export default App;
