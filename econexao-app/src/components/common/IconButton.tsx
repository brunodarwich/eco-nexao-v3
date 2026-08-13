import React from 'react';
import { TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/theme';
import { makeAccessibleButton } from '../../utils/accessibility';

interface IconButtonProps {
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
  accessibilityLabel: string;
  accessibilityHint?: string;
  variant?: 'primary' | 'secondary' | 'surface' | 'ghost';
  size?: number;
  style?: ViewStyle;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  onPress,
  accessibilityLabel,
  accessibilityHint,
  variant = 'surface',
  size = 20,
  style,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: theme.colors.brandForest,
          color: theme.colors.onPrimary,
        };
      case 'secondary':
        return {
          backgroundColor: theme.colors.secondaryContainer,
          color: theme.colors.onSecondaryContainer,
        };
      case 'ghost':
        return {
          backgroundColor: 'transparent',
          color: theme.colors.brandForest,
        };
      case 'surface':
      default:
        return {
          backgroundColor: theme.colors.surfaceWhite,
          color: theme.colors.brandDeep,
        };
    }
  };

  const vStyles = getVariantStyles();

  return (
    <TouchableOpacity
      style={[
        styles.button,
        { backgroundColor: vStyles.backgroundColor },
        variant === 'surface' && theme.shadows.sm,
        style,
      ]}
      onPress={onPress}
      {...makeAccessibleButton(accessibilityLabel, accessibilityHint)}
    >
      <Ionicons name={icon} size={size} color={vStyles.color} />
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    minWidth: theme.spacing.touchMin,
    minHeight: theme.spacing.touchMin,
    borderRadius: theme.radii.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
