import React from 'react';

interface LogoProps {
  size?: number;
  className?: string;
  showText?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ size = 28, className = '', showText = true }) => {
  return (
    <div
      className={`logo-container ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '10px',
        userSelect: 'none',
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        {/* Outer Shield Frame */}
        <path
          d="M16 3L5 7.5V14.5C5 21.6 9.7 28.1 16 30C22.3 28.1 27 21.6 27 14.5V7.5L16 3Z"
          fill="#10243A"
          stroke="#2563EB"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        {/* Inner Shield Shading */}
        <path
          d="M16 5.5L7.5 9V14.5C7.5 20.3 11.2 25.7 16 27.4C20.8 25.7 24.5 20.3 24.5 14.5V9L16 5.5Z"
          fill="#1E3A5F"
          fillOpacity="0.5"
        />
        {/* Verification Checkmark */}
        <path
          d="M11 16.5L14.5 20L21.5 13"
          stroke="#10B981"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {showText && (
        <span
          style={{
            fontWeight: 700,
            fontSize: '18px',
            letterSpacing: '-0.02em',
            color: 'var(--text-sidebar-active, #FFFFFF)',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          Phish<span style={{ color: 'var(--color-action-blue, #2563EB)' }}>Shield</span>
        </span>
      )}
    </div>
  );
};
