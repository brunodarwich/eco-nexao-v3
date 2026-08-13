import { Platform, ViewStyle } from 'react-native';

export const shadows = {
  sm: Platform.select({
    web: {
      boxShadow: '0px 2px 8px rgba(28, 59, 15, 0.04)',
    } as any,
    default: {
      shadowColor: '#1C3B0F',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.04,
      shadowRadius: 8,
      elevation: 2,
    } as ViewStyle,
  }),

  card: Platform.select({
    web: {
      boxShadow: '0px 4px 20px rgba(28, 59, 15, 0.06)',
    } as any,
    default: {
      shadowColor: '#1C3B0F',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.06,
      shadowRadius: 20,
      elevation: 4,
    } as ViewStyle,
  }),

  cardHover: Platform.select({
    web: {
      boxShadow: '0px 6px 24px rgba(28, 59, 15, 0.1)',
    } as any,
    default: {
      shadowColor: '#1C3B0F',
      shadowOffset: { width: 0, height: 6 },
      shadowOpacity: 0.1,
      shadowRadius: 24,
      elevation: 6,
    } as ViewStyle,
  }),

  hero: Platform.select({
    web: {
      boxShadow: '0px 8px 16px rgba(0, 0, 0, 0.15)',
    } as any,
    default: {
      shadowColor: '#000000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.15,
      shadowRadius: 16,
      elevation: 8,
    } as ViewStyle,
  }),
};
