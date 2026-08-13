import { TextStyle } from 'react-native';
import { colors } from './colors';

export const fontFamily = {
  regular: 'HankenGrotesk_400Regular',
  medium: 'HankenGrotesk_500Medium',
  semiBold: 'HankenGrotesk_600SemiBold',
  bold: 'HankenGrotesk_700Bold',
  extraBold: 'HankenGrotesk_800ExtraBold',
};

export const typography = {
  displayLg: {
    fontFamily: fontFamily.extraBold,
    fontSize: 40,
    lineHeight: 46,
    letterSpacing: -0.8,
    color: colors.brandDeep,
  } as TextStyle,

  headlineLg: {
    fontFamily: fontFamily.bold,
    fontSize: 30,
    lineHeight: 36,
    color: colors.brandDeep,
  } as TextStyle,

  headlineLgMobile: {
    fontFamily: fontFamily.bold,
    fontSize: 24,
    lineHeight: 30,
    color: colors.brandDeep,
  } as TextStyle,

  headlineMd: {
    fontFamily: fontFamily.semiBold,
    fontSize: 22,
    lineHeight: 28,
    color: colors.brandDeep,
  } as TextStyle,

  headlineSm: {
    fontFamily: fontFamily.semiBold,
    fontSize: 18,
    lineHeight: 24,
    color: colors.brandDeep,
  } as TextStyle,

  titleMd: {
    fontFamily: fontFamily.semiBold,
    fontSize: 16,
    lineHeight: 22,
    color: colors.brandDeep,
  } as TextStyle,

  bodyLg: {
    fontFamily: fontFamily.regular,
    fontSize: 18,
    lineHeight: 28,
    color: colors.onSurfaceVariant,
  } as TextStyle,

  bodyMd: {
    fontFamily: fontFamily.regular,
    fontSize: 16,
    lineHeight: 24,
    color: colors.onSurface,
  } as TextStyle,

  bodySm: {
    fontFamily: fontFamily.regular,
    fontSize: 14,
    lineHeight: 20,
    color: colors.onSurfaceVariant,
  } as TextStyle,

  labelMd: {
    fontFamily: fontFamily.semiBold,
    fontSize: 14,
    lineHeight: 18,
    letterSpacing: 0.5,
    color: colors.onSurface,
  } as TextStyle,

  labelSm: {
    fontFamily: fontFamily.medium,
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.3,
    color: colors.onSurfaceVariant,
  } as TextStyle,
};
