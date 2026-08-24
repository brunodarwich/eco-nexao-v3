import { AccessibilityInfo, AccessibilityProps, findNodeHandle, Platform } from 'react-native';

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

/**
 * Safely sets accessibility focus to a React component or node across Web and Native.
 * Never throws an exception.
 */
export function setAccessibilityFocusSafely(target: any): void {
  try {
    if (!target) return;

    if (Platform.OS === 'web') {
      const el = target?.current ?? target;
      if (el && typeof el.focus === 'function') {
        el.focus();
      }
      return;
    }

    const node = target?.current ? findNodeHandle(target.current) : findNodeHandle(target);
    if (node != null && AccessibilityInfo?.setAccessibilityFocus) {
      AccessibilityInfo.setAccessibilityFocus(node);
    }
  } catch (err) {
    // Fail silently to ensure stability across platforms and edge runtime states
    if (__DEV__) {
      console.warn('Failed to set accessibility focus safely:', err);
    }
  }
}
