// Tokens de cores do DESIGN (1).md e eco-nexao-conceito.txt

export const colors = {
  // Paleta da Marca
  brandForest: '#33601E',   // Primary / Verde Floresta (Ações principais, botões, foco)
  brandDeep: '#1C3B0F',     // Deep / Verde Escuro (Tipografia principal, headers)
  brandLeaf: '#5D8D3E',     // Leaf / Verde Folha (Selo Verde, status positivo)
  brandSage: '#759B71',     // Sage / Verde Sálvia (Bordas, ícones secundários)
  brandSun: '#F8C900',      // Sun / Amarelo Sol (Pontos de destaque, alertas e ratings)

  // Superfícies e Fundos
  surfaceBackground: '#F9FAF7',       // Fundo neutro suave (reduce eye strain)
  surfaceWhite: '#FFFFFF',            // Superfície elevada (cards, inputs, modais)
  surfaceDim: '#D9DAD8',
  surfaceBright: '#F9FAF7',
  surfaceContainerLowest: '#FFFFFF',
  surfaceContainerLow: '#F3F4F1',
  surfaceContainer: '#EDEEEB',
  surfaceContainerHigh: '#E7E8E6',
  surfaceContainerHighest: '#E2E3E0',

  // Textos e On-Surfaces
  onSurface: '#191C1B',
  onSurfaceVariant: '#42493D',
  inverseSurface: '#2E312F',
  inverseOnSurface: '#F0F1EE',
  textMain: '#1C3B0F',
  onPrimary: '#FFFFFF',
  onSecondary: '#FFFFFF',
  onTertiary: '#FFFFFF',

  // Containers de Suporte
  primaryContainer: '#33601E',
  onPrimaryContainer: '#A5D988',
  secondaryContainer: '#C6EEB0',
  onSecondaryContainer: '#4B6D3B',
  tertiaryContainer: '#CEA700',
  onTertiaryContainer: '#4E3E00',

  // Estados Semânticos & Alertas
  success: '#5D8D3E',
  warning: '#F8C900',
  error: '#B91C1C',
  onError: '#FFFFFF',
  errorContainer: '#FFDAD6',
  onErrorContainer: '#93000A',

  // Bordas e Delimitadores
  outline: '#72796C',
  outlineVariant: '#C2C9B9',
  sageBorder: '#759B71',
} as const;

export type ColorToken = keyof typeof colors;
