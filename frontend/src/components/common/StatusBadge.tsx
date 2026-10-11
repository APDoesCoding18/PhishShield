import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, HelpCircle } from 'lucide-react';

export type RiskState = 'clean' | 'suspicious' | 'malicious' | 'unknown' | 'informational';

interface StatusBadgeProps {
  status: RiskState | string;
  label?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, size = 'md' }) => {
  const normalized = status.toLowerCase();

  let badgeClass = 'badge-unknown';
  let icon = <HelpCircle size={size === 'sm' ? 12 : 14} />;
  let defaultLabel = 'Unassessed';

  if (normalized === 'clean' || normalized === 'low' || normalized === 'informational') {
    badgeClass = 'badge-clean';
    icon = <ShieldCheck size={size === 'sm' ? 12 : 14} />;
    defaultLabel = 'Clean / Low Risk';
  } else if (normalized === 'suspicious' || normalized === 'medium' || normalized === 'caution') {
    badgeClass = 'badge-suspicious';
    icon = <AlertTriangle size={size === 'sm' ? 12 : 14} />;
    defaultLabel = 'Suspicious';
  } else if (normalized === 'malicious' || normalized === 'high' || normalized === 'critical') {
    badgeClass = 'badge-malicious';
    icon = <ShieldAlert size={size === 'sm' ? 12 : 14} />;
    defaultLabel = 'Malicious';
  }

  return (
    <span className={`badge ${badgeClass} ${size === 'sm' ? 'text-meta' : ''}`}>
      {icon}
      <span>{label || defaultLabel}</span>
    </span>
  );
};
