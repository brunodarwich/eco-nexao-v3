import { colors } from './colors';
import { typography } from './typography';
import { spacing } from './spacing';
import { radii } from './radii';
import { shadows } from './shadows';

export const theme = {
  colors,
  typography,
  spacing,
  radii,
  shadows,
};

export type Theme = typeof theme;
export { useAppTheme } from './useAppTheme';

