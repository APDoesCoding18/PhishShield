import React from 'react';
import { Logo } from '../common/Logo';
import { ThemeToggle } from '../common/ThemeToggle';
import { Shield, History, FileText, Menu, X } from 'lucide-react';

export type NavTab = 'dashboard' | 'report' | 'history';

interface AppShellProps {
  activeTab: NavTab;
  onNavigate: (tab: NavTab) => void;
  children: React.ReactNode;
  reportAvailable?: boolean;
}

export const AppShell: React.FC<AppShellProps> = ({
  activeTab,
  onNavigate,
  children,
  reportAvailable = false,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const navItems = [
    {
      id: 'dashboard' as NavTab,
      label: 'Dashboard / New Analysis',
      icon: <Shield size={18} />,
      enabled: true,
    },
    {
      id: 'report' as NavTab,
      label: 'Analysis Report',
      icon: <FileText size={18} />,
      enabled: reportAvailable,
      badge: reportAvailable ? 'Active' : undefined,
    },
    {
      id: 'history' as NavTab,
      label: 'Analysis History',
      icon: <History size={18} />,
      enabled: true,
    },
  ];

  const handleTabClick = (tab: NavTab, enabled: boolean) => {
    if (!enabled) return;
    onNavigate(tab);
    setMobileMenuOpen(false);
  };

  return (
    <div className="app-layout">
      {/* Sidebar for Desktop */}
      <aside className={`app-sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          <Logo />
          <button
            className="mobile-close-btn"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        <div className="sidebar-section-label">ANALYSIS PORTAL</div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleTabClick(item.id, item.enabled)}
              disabled={!item.enabled}
              className={`nav-item ${activeTab === item.id ? 'active' : ''} ${
                !item.enabled ? 'disabled' : ''
              }`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <ThemeToggle />
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="app-main-wrapper">
        <header className="mobile-header">
          <Logo />
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ThemeToggle />
            <button
              className="mobile-menu-btn"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open navigation menu"
            >
              <Menu size={22} />
            </button>
          </div>
        </header>

        <main className="app-main-content">
          <div className="content-container">{children}</div>
        </main>
      </div>

      <style>{`
        .app-layout {
          display: flex;
          min-height: 100vh;
          width: 100%;
        }

        .app-sidebar {
          width: var(--sidebar-width);
          background-color: var(--bg-sidebar);
          color: var(--text-sidebar);
          display: flex;
          flex-direction: column;
          border-right: 1px solid var(--border-sidebar);
          position: fixed;
          top: 0;
          bottom: 0;
          left: 0;
          z-index: 50;
          transition: transform var(--transition-normal);
        }

        .sidebar-header {
          height: var(--header-height);
          padding: 0 var(--space-5);
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid var(--border-sidebar);
        }

        .mobile-close-btn {
          display: none;
          color: var(--text-sidebar);
          padding: 4px;
        }

        .sidebar-section-label {
          padding: var(--space-4) var(--space-5) var(--space-2);
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.05em;
          color: var(--text-dim);
        }

        .sidebar-nav {
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
          padding: 0 var(--space-3);
          flex: 1;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: 10px 14px;
          border-radius: var(--radius-md);
          color: var(--text-sidebar);
          font-size: 14px;
          font-weight: 500;
          text-align: left;
          width: 100%;
          transition: all var(--transition-fast);
        }

        .nav-item:hover:not(.disabled) {
          background-color: var(--bg-sidebar-hover);
          color: var(--text-sidebar-active);
        }

        .nav-item.active {
          background-color: var(--bg-sidebar-active);
          color: var(--text-sidebar-active);
          font-weight: 600;
          border-left: 3px solid var(--color-action-blue);
        }

        .nav-item.disabled {
          opacity: 0.45;
          cursor: not-allowed;
        }

        .nav-icon {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .nav-label {
          flex: 1;
        }

        .nav-badge {
          font-size: 10px;
          background-color: var(--color-action-blue);
          color: #ffffff;
          padding: 2px 6px;
          border-radius: var(--radius-full);
          font-weight: 600;
        }

        .sidebar-footer {
          padding: var(--space-4) var(--space-5);
          border-top: 1px solid var(--border-sidebar);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .system-status {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: var(--text-dim);
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background-color: var(--risk-clean);
          box-shadow: 0 0 6px var(--risk-clean);
        }

        .app-main-wrapper {
          flex: 1;
          margin-left: var(--sidebar-width);
          display: flex;
          flex-direction: column;
          min-width: 0;
          background-color: var(--bg-page);
        }

        .mobile-header {
          display: none;
          height: var(--header-height);
          padding: 0 var(--space-4);
          background-color: var(--bg-sidebar);
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid var(--border-sidebar);
        }

        .mobile-menu-btn {
          color: var(--text-sidebar);
          padding: 4px;
        }

        .app-main-content {
          flex: 1;
          padding: var(--space-8) var(--space-6);
        }

        .content-container {
          max-width: var(--content-max-width);
          margin: 0 auto;
          width: 100%;
        }

        /* Responsive Mobile Layout */
        @media (max-width: 768px) {
          .app-sidebar {
            transform: translateX(-100%);
          }

          .app-sidebar.mobile-open {
            transform: translateX(0);
          }

          .mobile-close-btn {
            display: block;
          }

          .app-main-wrapper {
            margin-left: 0;
          }

          .mobile-header {
            display: flex;
          }

          .app-main-content {
            padding: var(--space-4);
          }
        }
      `}</style>
    </div>
  );
};
