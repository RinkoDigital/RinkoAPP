export function KitsuneMask({ size = 88 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" fill="none" aria-hidden="true">
      <path
        d="M60,26
           C55,20 40,10 30,8
           C22,14 16,24 20,32
           C10,44 8,55 14,64
           C20,80 38,98 60,108
           C82,98 100,80 106,64
           C112,55 110,44 100,32
           C104,24 98,14 90,8
           C80,10 65,20 60,26 Z"
        stroke="var(--paper)"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <line x1="60" y1="46" x2="60" y2="78" stroke="var(--paper)" strokeWidth="1" opacity="0.5" />
      <path d="M60,78 L54,88 L66,88 Z" fill="var(--paper)" opacity="0.6" />

      <ellipse cx="42" cy="50" rx="11" ry="5.5" transform="rotate(-16 42 50)" fill="var(--crimson-glow)" />
      <ellipse cx="78" cy="50" rx="11" ry="5.5" transform="rotate(16 78 50)" fill="var(--crimson-glow)" />

      <path
        d="M22,68 L34,72 M22,78 L34,80"
        stroke="var(--crimson)"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.7"
      />
      <path
        d="M98,68 L86,72 M98,78 L86,80"
        stroke="var(--crimson)"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.7"
      />
    </svg>
  );
}
