import React from 'react';
import renderer, { act } from 'react-test-renderer';
import { Text } from 'react-native';

import { GooglePlacePhoto } from './GooglePlacePhoto';
import { ApiClientError } from '../../api/client';

describe('GooglePlacePhoto', () => {
  const photo = { proxy_url: '/api/v1/places/photos/opaque-token', expires_at: 1, width_px: 100, height_px: 80, author_attributions: [{ display_name: 'Ana', uri: 'https://maps.google.com/maps/contrib/1' }], google_maps_uri: 'https://www.google.com/maps/place/example' };

  it('renders visible accessible attribution and approved Maps links', async () => {
    let view: renderer.ReactTestRenderer;
    await act(async () => { view = renderer.create(<GooglePlacePhoto actorId="actor-1" alt="Fachada" loadPhoto={async () => ({ data: photo })} />); });
    const controls = view!.root.findAll(node => typeof node.props.accessibilityLabel === 'string');
    const labels = controls.map(node => node.props.accessibilityLabel);
    expect(labels).toEqual(expect.arrayContaining(['Foto fornecida pelo Google', 'Autor: Ana', 'Ver no Google Maps']));
    expect(view!.root.findAllByType(Text).map(node => node.props.children)).toContain('Foto do Google');
  });

  it('shows a retryable no-photo state without rendering an upstream URL', async () => {
    let view: renderer.ReactTestRenderer;
    await act(async () => { view = renderer.create(<GooglePlacePhoto actorId="actor-1" alt="Fachada" loadPhoto={async () => { throw new Error('https://googleusercontent.invalid'); }} />); });
    expect(view!.root.findAllByType(Text).map(node => node.props.children)).toContain('Foto indisponível.');
    expect(JSON.stringify(view!.toJSON())).not.toContain('googleusercontent');
    expect(view!.root.findByProps({ accessibilityLabel: 'Tentar novamente' })).toBeTruthy();
  });

  it('distinguishes a transient safe error from no photo and provides retry', async () => {
    let view: renderer.ReactTestRenderer;
    await act(async () => {
      view = renderer.create(
        <GooglePlacePhoto
          actorId="actor-1"
          alt="Fachada"
          loadPhoto={async () => { throw new ApiClientError('indisponível', 503); }}
        />
      );
    });
    expect(view!.root.findAllByType(Text).map(node => node.props.children)).toContain(
      'Não foi possível exibir esta foto.'
    );
    expect(view!.root.findByProps({ accessibilityLabel: 'Tentar novamente' })).toBeTruthy();
  });
});
