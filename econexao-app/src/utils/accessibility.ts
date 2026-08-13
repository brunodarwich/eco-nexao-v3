import { AccessibilityProps } from 'react-native';

export function makeAccessibleButton(
  label: string,
  hint?: string,
  disabled: boolean = false
): AccessibilityProps {
  return {
    accessible: true,
    accessibilityRole: 'button',
    accessibilityLabel: label,
    accessibilityHint: hint,
    accessibilityState: { disabled },
  };
}

export function makeAccessibleHeader(label: string, level: number = 1): AccessibilityProps {
  return {
    accessible: true,
    accessibilityRole: 'header',
    accessibilityLabel: label,
  };
}
