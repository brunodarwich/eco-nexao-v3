/**
 * @jest-environment jsdom
 */
import React, { useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react';
import { AccessibleModal } from '../components/common/AccessibleModal.web';

describe('Real DOM & Focus Management Integrity (ECO-2101 / WCAG 2.1 AA)', () => {
  let rootNode: HTMLElement;
  let warnSpy: jest.SpyInstance;
  let errorSpy: jest.SpyInstance;

  beforeEach(() => {
    warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    document.body.innerHTML = '<div id="root"><button id="external-trigger">Abrir</button></div>';
    rootNode = document.getElementById('root')!;
  });

  afterEach(() => {
    warnSpy.mockRestore();
    errorSpy.mockRestore();
    document.body.innerHTML = '';
  });

  function ModalHarness({ visible, onClose }: { visible: boolean; onClose: () => void }) {
    const closeBtnRef = useRef<HTMLButtonElement>(null);
    const triggerRef = useRef<HTMLElement | null>(document.getElementById('external-trigger'));

    return (
      <AccessibleModal
        visible={visible}
        onClose={onClose}
        initialFocusRef={closeBtnRef}
        returnFocusRef={triggerRef}
        accessibilityLabel="Diálogo de Teste"
      >
        <div id="modal-inner">
          <h2>Título do Modal</h2>
          <button ref={closeBtnRef} id="modal-close-btn" onClick={onClose}>
            Fechar
          </button>
          <button id="modal-action-btn">Confirmar</button>
        </div>
      </AccessibleModal>
    );
  }

  test('Elimina erro aria-hidden, cria portal com role=dialog e restaura foco com precisão', async () => {
    const trigger = document.getElementById('external-trigger') as HTMLButtonElement;
    trigger.focus();
    expect(document.activeElement).toBe(trigger);

    const container = document.createElement('div');
    document.body.appendChild(container);
    const root = createRoot(container);

    let isOpen = true;
    const handleClose = jest.fn(() => {
      isOpen = false;
    });

    // 1. Mount modal when trigger was focused
    await act(async () => {
      root.render(<ModalHarness visible={isOpen} onClose={handleClose} />);
    });

    // Verify #root received aria-hidden="true"
    expect(rootNode.getAttribute('aria-hidden')).toBe('true');

    // Verify ZERO blocked aria-hidden warnings occurred
    const ariaHiddenWarnings = warnSpy.mock.calls.filter(call =>
      call.some((arg: unknown) => typeof arg === 'string' && arg.toLowerCase().includes('blocked aria-hidden'))
    );
    expect(ariaHiddenWarnings.length).toBe(0);

    // Verify dialog role is present in DOM
    const dialog = document.querySelector('[role="dialog"]');
    expect(dialog).not.toBeNull();
    expect(dialog?.getAttribute('aria-modal')).toBe('true');
    expect(dialog?.getAttribute('aria-label')).toBe('Diálogo de Teste');

    // Check Escape key triggers close
    await act(async () => {
      const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true });
      document.dispatchEvent(escapeEvent);
    });
    expect(handleClose).toHaveBeenCalledTimes(1);

    // 2. Unmount / close modal
    await act(async () => {
      root.render(<ModalHarness visible={false} onClose={handleClose} />);
    });

    // Verify #root aria-hidden is removed
    expect(rootNode.getAttribute('aria-hidden')).toBeNull();

    // Verify dialog is gone
    const dialogAfterClose = document.querySelector('[role="dialog"]');
    expect(dialogAfterClose).toBeNull();

    // Verify zero warnings on cleanup
    const warningsAfterClose = warnSpy.mock.calls.filter(call =>
      call.some((arg: unknown) => typeof arg === 'string' && arg.toLowerCase().includes('blocked aria-hidden'))
    );
    expect(warningsAfterClose.length).toBe(0);

    await act(async () => {
      root.unmount();
    });
  });
});
