import { useMemo } from 'react';
import { TextStyle } from 'react-native';
import { colors as defaultColors } from './colors';
import { typography as defaultTypography } from './typography';
import { spacing } from './spacing';
import { radii } from './radii';
import { shadows } from './shadows';
import { useAppContext } from '../state/useAppContext';

export type AppThemeColors = Record<keyof typeof defaultColors, string>;

export function getHighContrastColors(baseColors: typeof defaultColors): AppThemeColors {
  return {
    ...baseColors,
    brandForest: '#1A4D0A',
    brandDeep: '#0B1E05',
    brandLeaf: '#2E6617',
    brandSage: '#2B5725',
    brandSun: '#946200',
    surfaceBackground: '#FFFFFF',
    surfaceWhite: '#FFFFFF',
    surfaceContainerLow: '#ECEEE9',
    surfaceContainer: '#DFE2DC',
    surfaceContainerHigh: '#D3D6D0',
    onSurface: '#000000',
    onSurfaceVariant: '#111810',
    outline: '#000000',
    outlineVariant: '#333A30',
    sageBorder: '#1A4D0A',
  };
}

export function scaleTypography(
  baseTypography: typeof defaultTypography,
  scale: number,
  colors: AppThemeColors
) {
  const scaled: Record<string, TextStyle> = {};

  for (const [key, val] of Object.entries(baseTypography)) {
    const fontSize = val.fontSize ? Math.round(val.fontSize * scale) : val.fontSize;
    const lineHeight = val.lineHeight ? Math.round(val.lineHeight * scale) : val.lineHeight;

    scaled[key] = {
      ...val,
      fontSize,
      lineHeight,
      color: colors.brandDeep,
    };
  }

  return scaled as typeof defaultTypography;
}

export function useAppTheme() {
  const { state } = useAppContext();
  const { highContrast, textScale, screenReaderMode, locale } = state.accessibility;

  const currentColors = useMemo<AppThemeColors>(() => {
    return highContrast ? getHighContrastColors(defaultColors) : (defaultColors as unknown as AppThemeColors);
  }, [highContrast]);

  const currentTypography = useMemo(() => {
    return scaleTypography(defaultTypography, textScale || 1.0, currentColors);
  }, [textScale, currentColors]);

  return useMemo(
    () => ({
      colors: currentColors,
      typography: currentTypography,
      spacing,
      radii,
      shadows,
      isHighContrast: highContrast,
      textScale: textScale || 1.0,
      screenReaderMode,
      locale,
    }),
    [currentColors, currentTypography, highContrast, textScale, screenReaderMode, locale]
  );
}
