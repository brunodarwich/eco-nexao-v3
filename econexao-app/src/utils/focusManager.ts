import React, { useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import { setAccessibilityFocusSafely } from './accessibility';

export interface UseModalFocusOptions {
  visible: boolean;
  onClose?: () => void;
  initialFocusRef?: React.RefObject<any>;
  returnFocusRef?: React.RefObject<any>;
  containerRef?: React.RefObject<any>;
}

/**
 * Hook to manage accessible focus for modal dialogs, bottom sheets, and overlays.
 * - Prevents "Blocked aria-hidden because its descendant retained focus" on web.
 * - Traps keyboard Tab / Shift+Tab cycling within the modal.
 * - Handles Escape key to trigger onClose.
 * - Restores focus to the opener element upon modal dismissal.
 */
const useIsomorphicLayoutEffect =
  typeof window !== 'undefined' ? React.useLayoutEffect : React.useEffect;

export function useModalFocus({
  visible,
  onClose,
  initialFocusRef,
  returnFocusRef,
  containerRef,
}: UseModalFocusOptions) {
  const previousActiveElementRef = useRef<HTMLElement | null>(null);
  const wasVisibleRef = useRef<boolean>(false);

  useIsomorphicLayoutEffect(() => {
    if (Platform.OS !== 'web') {
      if (visible && initialFocusRef) {
        setAccessibilityFocusSafely(initialFocusRef);
      }
      return;
    }

    if (typeof document === 'undefined') return;

    if (visible && !wasVisibleRef.current) {
      wasVisibleRef.current = true;
      // Capture currently focused element before modal opens
      if (document.activeElement instanceof HTMLElement) {
        previousActiveElementRef.current = document.activeElement;
        // Blur synchronously in layout phase to ensure #root doesn't retain focus when aria-hidden is applied
        document.activeElement.blur();
      }

      // Schedule focus transition to the modal container or initial element
      const timer = setTimeout(() => {
        if (initialFocusRef?.current) {
          setAccessibilityFocusSafely(initialFocusRef);
        } else if (containerRef?.current) {
          const container = containerRef.current;
          const target = (container && container.tabIndex >= 0)
            ? container
            : container?.querySelector?.('button, [tabindex="0"], input, a');
          if (target && typeof target.focus === 'function') {
            target.focus();
          } else {
            setAccessibilityFocusSafely(containerRef);
          }
        }
      }, 16);

      return () => clearTimeout(timer);
    }

    if (!visible && wasVisibleRef.current) {
      wasVisibleRef.current = false;
      const targetToRestore = returnFocusRef?.current || previousActiveElementRef.current;
      if (targetToRestore) {
        const timer = setTimeout(() => {
          if (typeof targetToRestore.focus === 'function') {
            targetToRestore.focus();
          } else {
            setAccessibilityFocusSafely(targetToRestore);
          }
        }, 32);
        return () => clearTimeout(timer);
      }
    }
  }, [visible, initialFocusRef, returnFocusRef, containerRef]);

  // Handle Tab trapping and Escape key on Web
  useEffect(() => {
    if (Platform.OS !== 'web' || !visible || typeof document === 'undefined') return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose?.();
        return;
      }

      if (e.key === 'Tab' && containerRef?.current) {
        const containerNode = containerRef.current as HTMLElement;
        const focusableElements = containerNode.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement || !containerNode.contains(document.activeElement)) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement || !containerNode.contains(document.activeElement)) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [visible, onClose, containerRef]);
}
