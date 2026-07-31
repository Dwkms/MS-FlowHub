type IconProps = { className?: string };

export function FlowMark({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 36 36" aria-hidden="true">
      <path d="M5 9.5 18 2l13 7.5v17L18 34 5 26.5z" fill="currentColor" opacity=".14" />
      <path
        d="M10 12.5 18 8l8 4.5v3.3L18 11l-8 4.8zm0 7 8 4.5 8-4.5v4L18 28l-8-4.5z"
        fill="currentColor"
      />
    </svg>
  );
}

export function BellIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z" stroke="currentColor" strokeWidth="1.7" />
      <path d="M10 21h4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

export function ArrowIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="m9 18 6-6-6-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
