import React from 'react';
import { Image, Text, TouchableOpacity } from 'react-native';
import TestRenderer, { act } from 'react-test-renderer';

import { ActorCard } from './ActorCard';
import type { ActorSummary } from '../../api/types';

jest.mock('@expo/vector-icons', () => ({
  Ionicons: () => null,
}));

describe('ActorCard (ECO-2512)', () => {
  const baseActor: ActorSummary = {
    id: 'actor-1',
    slug: 'pousada-pindobal',
    name: 'Pousada Pindobal',
    category_slug: 'hospedagem',
    category_label: 'Hospedagem',
    address: 'Praia de Pindobal, Santarém - PA',
    latitude: -2.5,
    longitude: -54.9,
    green_badge_status: 'none',
    verification_status: 'unverified',
    google_rating: 4.8,
    cover_image_url: 'https://example.com/pousada.jpg',
    cover_media: {
      id: 'media-1',
      owner_type: 'actor',
      owner_id: 'actor-1',
      url: 'https://example.com/pousada.jpg',
      alt_text: 'Foto da Pousada Pindobal',
      credit: 'Foto SEMTUR',
      license_code: 'CC-BY-4.0',
      sort_order: 0,
    },
    is_favorite: false,
  };

  it('renders actor details, category tag, and Google rating', () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    act(() => {
      renderer = TestRenderer.create(<ActorCard actor={baseActor} />);
    });

    const texts = renderer.root.findAllByType(Text).map((t) => t.props.children);
    expect(texts).toContain('HOSPEDAGEM');
    expect(texts).toContain('Pousada Pindobal');
    expect(texts).toContain('4.8 Google');

    const image = renderer.root.findByType(Image);
    expect(image.props.source).toEqual({ uri: 'https://example.com/pousada.jpg' });
    expect(image.props.accessibilityLabel).toBe('Foto da Pousada Pindobal');
  });

  it('renders neutral, accessible SEMTUR inventory badge when verified', () => {
    const verifiedActor: ActorSummary = {
      ...baseActor,
      verification_status: 'verified',
    };

    let renderer!: TestRenderer.ReactTestRenderer;
    act(() => {
      renderer = TestRenderer.create(<ActorCard actor={verifiedActor} />);
    });

    const texts = renderer.root.findAllByType(Text).map((t) => t.props.children);
    expect(texts).toContain('Inventário SEMTUR');

    const semturBadge = renderer.root.find(
      (node) => node.props.accessibilityLabel === 'Origem dos dados: Inventário SEMTUR'
    );
    expect(semturBadge).toBeDefined();
    expect(semturBadge.props.accessibilityRole).toBe('text');
  });

  it('renders Green Seal badge when green_badge_status is verified', () => {
    const greenActor: ActorSummary = {
      ...baseActor,
      green_badge_status: 'verified',
    };

    let renderer!: TestRenderer.ReactTestRenderer;
    act(() => {
      renderer = TestRenderer.create(<ActorCard actor={greenActor} />);
    });

    const texts = renderer.root.findAllByType(Text).map((t) => t.props.children);
    expect(texts).toContain('Selo Verde');
  });

  it('handles favorite toggle button with accessible label', () => {
    const onToggle = jest.fn();
    let renderer!: TestRenderer.ReactTestRenderer;
    act(() => {
      renderer = TestRenderer.create(
        <ActorCard actor={baseActor} isFavorite={false} onToggleFavorite={onToggle} />
      );
    });

    const favButton = renderer.root.find(
      (node) => node.props.accessibilityLabel === 'Salvar ator nos favoritos'
    );
    expect(favButton).toBeDefined();

    act(() => {
      favButton.props.onPress({ stopPropagation: jest.fn() });
    });
    expect(onToggle).toHaveBeenCalledTimes(1);
  });
});
