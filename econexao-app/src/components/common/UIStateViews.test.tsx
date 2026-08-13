import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { ActivityIndicator, Text, TouchableOpacity } from 'react-native';
import { LoadingView, EmptyStateView, ErrorStateView } from './UIStateViews';

jest.mock('@expo/vector-icons', () => ({
  Ionicons: 'Ionicons',
}));

describe('UIStateViews components', () => {
  describe('LoadingView', () => {
    it('renders default loading message and ActivityIndicator', async () => {
      let tree!: renderer.ReactTestRenderer;
      await act(async () => {
        tree = renderer.create(<LoadingView />);
      });
      const root = tree.root;

      const textElements = root.findAllByType(Text);
      expect(textElements.length).toBe(1);
      expect(textElements[0].props.children).toBe('Carregando dados da rota...');

      const indicator = root.findByType(ActivityIndicator);
      expect(indicator).toBeTruthy();
      expect(indicator.props.size).toBe('large');
    });

    it('renders custom loading message when message prop is provided', async () => {
      const customMessage = 'Buscando produtores locais...';
      let tree!: renderer.ReactTestRenderer;
      await act(async () => {
        tree = renderer.create(<LoadingView message={customMessage} />);
      });
      const root = tree.root;

      const textElements = root.findAllByType(Text);
      expect(textElements.length).toBe(1);
      expect(textElements[0].props.children).toBe(customMessage);
    });
  });

  describe('EmptyStateView', () => {
    it('renders default title and message without reset button when onReset is not provided', async () => {
      let tree!: renderer.ReactTestRenderer;
      await act(async () => {
        tree = renderer.create(<EmptyStateView />);
      });
      const root = tree.root;

      const textElements = root.findAllByType(Text);
      const textContents = textElements.map((el: renderer.ReactTestInstance) => el.props.children);

      expect(textContents).toContain('Nenhum resultado encontrado');
      expect(textContents).toContain(
        'Tente ajustar seus termos de busca ou selecionar outra categoria.'
      );

      const buttons = root.findAllByType(TouchableOpacity);
      expect(buttons.length).toBe(0);
    });

    it('renders custom title and message', async () => {
      const customTitle = 'Sem feiras disponíveis';
      const customMessage = 'Nenhuma feira orgânica cadastrada nesta região.';
      let tree!: renderer.ReactTestRenderer;
      await act(async () => {
        tree = renderer.create(
          <EmptyStateView title={customTitle} message={customMessage} />
        );
      });
      const root = tree.root;

      const textElements = root.findAllByType(Text);
      const textContents = textElements.map((el: renderer.ReactTestInstance) => el.props.children);

      expect(textContents).toContain(customTitle);
      expect(textContents).toContain(customMessage);
    });

    it('renders reset button with correct accessibility properties when onReset is provided', async () => {
      const handleReset = jest.fn();
      let tree!: renderer.ReactTestRenderer;
      await act(async () => {
        tree = renderer.create(<EmptyStateView onReset={handleReset} />);
      });
      const root = tree.root;

      const button = root.findByType(TouchableOpacity);
      expect(button).toBeTruthy();

      expect(button.props.accessible).toBe(true);
      expect(button.props.accessibilityRole).toBe('button');
      expect(button.props.accessibilityLabel).toBe('Limpar Filtros');
      expect(button.props.accessibilityHint).toBe(
        'Redefine a busca e os filtros aplicados'
      );
      expect(button.props.accessibilityState).toEqual({ disabled: false });

      const buttonText = button.findByType(Text);
      expect(buttonText.props.children).toBe('Limpar Filtros');
    });

    it('calls onReset callback when the reset button is pressed', async () => {
      const handleReset = jest.fn();
      let tree!: renderer.ReactTestRenderer;
      await act(async () => {
        tree = renderer.create(<EmptyStateView onReset={handleReset} />);
      });
      const root = tree.root;

      const button = root.findByType(TouchableOpacity);
      await act(async () => {
        button.props.onPress();
      });

      expect(handleReset).toHaveBeenCalledTimes(1);
    });
  });

  describe('ErrorStateView', () => {
    it('renders default title and message without retry button when onRetry is not provided', async () => {
      let tree!: renderer.ReactTestRenderer;
      await act(async () => {
        tree = renderer.create(<ErrorStateView />);
      });
      const root = tree.root;

      const textElements = root.findAllByType(Text);
      const textContents = textElements.map((el: renderer.ReactTestInstance) => el.props.children);

      expect(textContents).toContain('Erro de Carregamento');
      expect(textContents).toContain(
        'Não foi possível conectar com os dados da rota no momento.'
      );

      const buttons = root.findAllByType(TouchableOpacity);
      expect(buttons.length).toBe(0);
    });

    it('renders custom title and message', async () => {
      const customTitle = 'Falha de Conexão';
      const customMessage = 'Verifique sua conexão de internet e tente novamente.';
      let tree!: renderer.ReactTestRenderer;
      await act(async () => {
        tree = renderer.create(
          <ErrorStateView title={customTitle} message={customMessage} />
        );
      });
      const root = tree.root;

      const textElements = root.findAllByType(Text);
      const textContents = textElements.map((el: renderer.ReactTestInstance) => el.props.children);

      expect(textContents).toContain(customTitle);
      expect(textContents).toContain(customMessage);
    });

    it('renders retry button with correct accessibility properties when onRetry is provided', async () => {
      const handleRetry = jest.fn();
      let tree!: renderer.ReactTestRenderer;
      await act(async () => {
        tree = renderer.create(<ErrorStateView onRetry={handleRetry} />);
      });
      const root = tree.root;

      const button = root.findByType(TouchableOpacity);
      expect(button).toBeTruthy();

      expect(button.props.accessible).toBe(true);
      expect(button.props.accessibilityRole).toBe('button');
      expect(button.props.accessibilityLabel).toBe('Tentar Novamente');
      expect(button.props.accessibilityHint).toBe(
        'Recarrega as informações da rota'
      );
      expect(button.props.accessibilityState).toEqual({ disabled: false });

      const buttonText = button.findByType(Text);
      expect(buttonText.props.children).toBe('Tentar Novamente');
    });

    it('calls onRetry callback when the retry button is pressed', async () => {
      const handleRetry = jest.fn();
      let tree!: renderer.ReactTestRenderer;
      await act(async () => {
        tree = renderer.create(<ErrorStateView onRetry={handleRetry} />);
      });
      const root = tree.root;

      const button = root.findByType(TouchableOpacity);
      await act(async () => {
        button.props.onPress();
      });

      expect(handleRetry).toHaveBeenCalledTimes(1);
    });
  });
});
