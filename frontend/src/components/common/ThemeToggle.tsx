import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="theme-toggle-btn"
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '8px',
        borderRadius: 'var(--radius-md)',
        color: 'var(--text-sidebar, #CBD5E1)',
        backgroundColor: 'transparent',
        border: '1px solid var(--border-sidebar, rgba(255, 255, 255, 0.1))',
        transition: 'all var(--transition-fast)',
        cursor: 'pointer',
      }}
    >
      {theme === 'light' ? (
        <Moon size={18} strokeWidth={2} />
      ) : (
        <Sun size={18} strokeWidth={2} />
      )}
    </button>
  );
};
