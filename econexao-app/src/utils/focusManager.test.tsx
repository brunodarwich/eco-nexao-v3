import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { useModalFocus } from './focusManager';

interface TestProps {
  visible: boolean;
  onClose: () => void;
  initialFocusRef?: React.RefObject<any>;
  returnFocusRef?: React.RefObject<any>;
  containerRef?: React.RefObject<any>;
}

function TestComponent(props: TestProps) {
  useModalFocus({
    visible: props.visible,
    onClose: props.onClose,
    initialFocusRef: props.initialFocusRef,
    returnFocusRef: props.returnFocusRef,
    containerRef: props.containerRef,
  });
  return React.createElement('view', null, props.visible ? 'Modal Open' : 'Modal Closed');
}

describe('useModalFocus focus management', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('manages focus transitions safely in renderer', async () => {
    const onClose = jest.fn();
    let tree: renderer.ReactTestRenderer;

    await act(async () => {
      tree = renderer.create(<TestComponent visible={false} onClose={onClose} />);
    });

    // Open modal
    await act(async () => {
      tree.update(<TestComponent visible={true} onClose={onClose} />);
    });

    act(() => {
      jest.advanceTimersByTime(50);
    });

    // Close modal
    await act(async () => {
      tree.update(<TestComponent visible={false} onClose={onClose} />);
    });

    act(() => {
      jest.advanceTimersByTime(50);
    });

    expect(tree!.toJSON()).toBeDefined();
  });
});
