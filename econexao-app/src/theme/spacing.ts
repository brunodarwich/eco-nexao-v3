export const spacing = {
  unit: 4,
  stackSm: 8,
  stackMd: 16,
  stackLg: 32,
  marginMobile: 16,
  marginDesktop: 64,
  gutter: 24,
  touchMin: 48, // Área de toque mínima acessível (a11y)
} as const;

export type SpacingToken = keyof typeof spacing;
