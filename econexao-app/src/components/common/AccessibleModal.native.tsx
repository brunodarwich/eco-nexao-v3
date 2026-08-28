import React, { useRef } from 'react';
import { Modal, View, StyleSheet, ModalProps, StyleProp, ViewStyle } from 'react-native';
import { useModalFocus } from '../../utils/focusManager';

export interface AccessibleModalProps extends ModalProps {
  visible: boolean;
  onClose: () => void;
  initialFocusRef?: React.RefObject<any>;
  returnFocusRef?: React.RefObject<any>;
  accessibilityLabel?: string;
  contentStyle?: StyleProp<ViewStyle>;
}

export const AccessibleModal: React.FC<AccessibleModalProps> = ({
  visible,
  onClose,
  initialFocusRef,
  returnFocusRef,
  accessibilityLabel,
  contentStyle,
  children,
  transparent = true,
  animationType = 'fade',
  ...restProps
}) => {
  const containerRef = useRef<View>(null);

  useModalFocus({
    visible,
    onClose,
    initialFocusRef,
    returnFocusRef,
    containerRef,
  });

  return (
    <Modal
      visible={visible}
      transparent={transparent}
      animationType={animationType}
      onRequestClose={onClose}
      accessibilityViewIsModal
      aria-modal
      {...restProps}
    >
      <View
        ref={containerRef}
        style={[styles.fullScreen, contentStyle]}
        accessible
        accessibilityRole="header"
        accessibilityLabel={accessibilityLabel || 'Janela modal'}
      >
        {children}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  fullScreen: {
    flex: 1,
  },
});
