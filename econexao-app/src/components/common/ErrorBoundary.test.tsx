import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { Text, TouchableOpacity, Platform, AccessibilityInfo } from 'react-native';
import { ErrorBoundary } from './ErrorBoundary';
import { setAccessibilityFocusSafely } from '../../utils/accessibility';

jest.mock('@expo/vector-icons', () => ({
  Ionicons: 'Ionicons',
}));

// Component helper that can trigger throw
const ProblemChild = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test crash in child component');
  }
  return <Text>Content loaded safely</Text>;
};

describe('ErrorBoundary component', () => {
  let originalConsoleError: typeof console.error;

  beforeEach(() => {
    originalConsoleError = console.error;
    console.error = jest.fn(); // Suppress React boundary / dev error logs in test output
  });

  afterEach(() => {
    console.error = originalConsoleError;
  });

  it('renders children normally when there is no error', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(
        <ErrorBoundary>
          <ProblemChild shouldThrow={false} />
        </ErrorBoundary>
      );
    });

    const root = tree.root;
    const textElements = root.findAllByType(Text);
    expect(textElements.length).toBe(1);
    expect(textElements[0].props.children).toBe('Content loaded safely');
  });

  it('catches exception and renders fallback UI with retry button', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(
        <ErrorBoundary>
          <ProblemChild shouldThrow={true} />
        </ErrorBoundary>
      );
    });

    const root = tree.root;
    const textElements = root.findAllByType(Text);
    const contents = textElements.map((el) => el.props.children);

    expect(contents).toContain('Ops! Algo deu errado');
    expect(contents).toContain(
      'Ocorreu um erro inesperado ao renderizar esta tela. Não se preocupe, seus dados estão seguros.'
    );

    const retryButton = root.findByType(TouchableOpacity);
    expect(retryButton).toBeTruthy();
    expect(retryButton.props.accessibilityLabel).toBe('Tentar novamente');
  });

  it('renders custom fallback when provided', async () => {
    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(
        <ErrorBoundary fallback={<Text>Custom Error Fallback</Text>}>
          <ProblemChild shouldThrow={true} />
        </ErrorBoundary>
      );
    });

    const root = tree.root;
    const textElements = root.findAllByType(Text);
    expect(textElements.length).toBe(1);
    expect(textElements[0].props.children).toBe('Custom Error Fallback');
  });

  it('resets error state when retry button is pressed', async () => {
    let resetCallbackCalled = false;

    const ParentComponent = () => {
      const [hasError, setHasError] = React.useState(true);

      return (
        <ErrorBoundary
          onReset={() => {
            resetCallbackCalled = true;
            setHasError(false);
          }}
        >
          <ProblemChild shouldThrow={hasError} />
        </ErrorBoundary>
      );
    };

    let tree!: renderer.ReactTestRenderer;
    await act(async () => {
      tree = renderer.create(<ParentComponent />);
    });

    // Check that fallback is shown
    const retryButtons = tree.root.findAllByType(TouchableOpacity);
    expect(retryButtons.length).toBe(1);

    // Press retry
    await act(async () => {
      retryButtons[0].props.onPress();
    });

    expect(resetCallbackCalled).toBe(true);

    // Expect children to be rendered again
    const textElements = tree.root.findAllByType(Text);
    const contents = textElements.map((el) => el.props.children);
    expect(contents).toContain('Content loaded safely');
  });
});

describe('setAccessibilityFocusSafely utility', () => {
  let originalPlatformOS: typeof Platform.OS;
  let originalConsoleWarn: typeof console.warn;

  beforeEach(() => {
    originalPlatformOS = Platform.OS;
    originalConsoleWarn = console.warn;
    console.warn = jest.fn();
  });

  afterEach(() => {
    Object.defineProperty(Platform, 'OS', {
      value: originalPlatformOS,
      configurable: true,
    });
    console.warn = originalConsoleWarn;
  });

  it('handles null, undefined or empty target gracefully without throwing', () => {
    expect(() => setAccessibilityFocusSafely(null)).not.toThrow();
    expect(() => setAccessibilityFocusSafely(undefined)).not.toThrow();
    expect(() => setAccessibilityFocusSafely({})).not.toThrow();
  });

  it('calls focus() on web target or ref without throwing', () => {
    Object.defineProperty(Platform, 'OS', {
      value: 'web',
      configurable: true,
    });

    const focusMock = jest.fn();
    // Direct DOM element mock
    setAccessibilityFocusSafely({ focus: focusMock });
    expect(focusMock).toHaveBeenCalledTimes(1);

    // React ref mock
    const refMock = { current: { focus: jest.fn() } };
    setAccessibilityFocusSafely(refMock);
    expect(refMock.current.focus).toHaveBeenCalledTimes(1);

    // Target without focus method
    expect(() => setAccessibilityFocusSafely({ current: {} })).not.toThrow();
  });

  it('calls AccessibilityInfo.setAccessibilityFocus on native platform', () => {
    Object.defineProperty(Platform, 'OS', {
      value: 'ios',
      configurable: true,
    });

    const mockSetAccessibilityFocus = jest.spyOn(AccessibilityInfo, 'setAccessibilityFocus');
    const mockRef = { current: 123 };

    expect(() => setAccessibilityFocusSafely(mockRef)).not.toThrow();
  });

  it('does not throw when an exception occurs inside execution', () => {
    Object.defineProperty(Platform, 'OS', {
      value: 'web',
      configurable: true,
    });

    const targetWithThrowingGetter = {
      get current() {
        throw new Error('Unexpected DOM error');
      },
    };

    expect(() => setAccessibilityFocusSafely(targetWithThrowingGetter)).not.toThrow();
  });
});
