import React from 'react';
import { Platform } from 'react-native';
import { AccessibleModal as WebAccessibleModal } from './AccessibleModal.web';
import { AccessibleModal as NativeAccessibleModal, AccessibleModalProps } from './AccessibleModal.native';

export type { AccessibleModalProps };

export const AccessibleModal: React.FC<AccessibleModalProps> = (props) => {
  if (Platform.OS === 'web' || typeof document !== 'undefined') {
    return <WebAccessibleModal {...props} />;
  }
  return <NativeAccessibleModal {...props} />;
};
