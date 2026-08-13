export const radii = {
  sm: 4,          // 0.25rem
  default: 8,     // 0.5rem (base do design system)
  md: 12,         // 0.75rem
  lg: 16,         // 1rem
  xl: 24,         // 1.5rem
  full: 9999,     // Pill shape para chips e badges
} as const;

export type RadiiToken = keyof typeof radii;
