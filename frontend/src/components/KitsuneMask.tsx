/**
 * Stylized, hand-drawn version of the Rinko Digital kitsune mask reference
 * (painted fox mask, cherry blossoms, red moon). This is a minimalist
 * line-art reduction, not a recreation of that illustration — the goal is
 * the two things that actually read as "kitsune mask" at small size: the
 * elongated snout and the tear-streak markings fanning down from the eyes.
 */
export function KitsuneMask({ size = 96 }: { size?: number }) {
  return (
    <svg width={size} height={(size * 132) / 120} viewBox="0 0 120 132" fill="none" aria-hidden="true">
      {/* face + ears */}
      <path
        d="M60,34
           C50,22 34,10 16,4
           C10,16 12,28 26,36
           C14,42 4,54 6,66
           C8,84 20,100 34,112
           C44,121 53,127 60,130
           C67,127 76,121 86,112
           C100,100 112,84 114,66
           C116,54 106,42 94,36
           C108,28 110,16 104,4
           C86,10 70,22 60,34 Z"
        stroke="var(--paper)"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />

      {/* inner ear */}
      <path d="M22,14 C20,22 24,30 32,34 C28,25 26,18 26,12 Z" fill="var(--crimson-deep)" opacity="0.8" />
      <path d="M98,14 C100,22 96,30 88,34 C92,25 94,18 94,12 Z" fill="var(--crimson-deep)" opacity="0.8" />

      {/* eyes */}
      <path
        d="M32,58 C38,53 46,53 52,57 C46,61 38,61 32,58 Z"
        fill="var(--crimson-glow)"
      />
      <path
        d="M88,58 C82,53 74,53 68,57 C74,61 82,61 88,58 Z"
        fill="var(--crimson-glow)"
      />

      {/* kitsune tear streaks fanning down from each eye — the signature detail */}
      <path
        d="M35,56 C28,68 20,80 14,94 M42,58 C37,72 30,86 24,100 M49,60 C46,76 42,92 38,106"
        stroke="var(--crimson)"
        strokeWidth="1.6"
        strokeLinecap="round"
        opacity="0.85"
      />
      <path
        d="M85,56 C92,68 100,80 106,94 M78,58 C83,72 90,86 96,100 M71,60 C74,76 78,92 82,106"
        stroke="var(--crimson)"
        strokeWidth="1.6"
        strokeLinecap="round"
        opacity="0.85"
      />

      {/* nose bridge + nose tip */}
      <line x1="60" y1="66" x2="60" y2="118" stroke="var(--paper)" strokeWidth="1" opacity="0.35" />
      <ellipse cx="60" cy="122" rx="5" ry="3.5" fill="var(--ink)" stroke="var(--paper)" strokeWidth="1" />
    </svg>
  );
}
