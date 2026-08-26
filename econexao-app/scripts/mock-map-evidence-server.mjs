import http from 'node:http';

const routeId = 'route-pindobal';
const originId = 'origin-porto';

const pins = [
  {
    id: 'pin-restaurante', actor_id: 'actor-restaurante', name: 'Restaurante da Praia',
    category_slug: 'alimentacao', category_label: 'Alimentação', color: '#D97706',
    icon: 'utensils', latitude: -2.548, longitude: -54.934,
    distance_from_origin_m: 8200, layer: 'route_corridor',
  },
  {
    id: 'pin-pousada', actor_id: 'actor-pousada', name: 'Pousada Pindobal',
    category_slug: 'hospedagem', category_label: 'Hospedagem', color: '#2563EB',
    icon: 'bed', latitude: -2.575, longitude: -54.952,
    distance_from_origin_m: 12100, layer: 'route_corridor',
  },
  {
    id: 'pin-terminal', actor_id: 'actor-terminal', name: 'Terminal Rodoviário',
    category_slug: 'transporte', category_label: 'Transporte', color: '#7C3AED',
    icon: 'bus', latitude: -2.443, longitude: -54.708,
    distance_from_origin_m: 900, layer: 'both',
  },
  {
    id: 'pin-ubs', actor_id: 'actor-ubs', name: 'Unidade de Saúde Central',
    category_slug: 'saude', category_label: 'Saúde', color: '#DC2626',
    icon: 'heart-pulse', latitude: -2.438, longitude: -54.718,
    distance_from_origin_m: null, layer: 'citywide_essential',
  },
  {
    id: 'pin-delegacia', actor_id: 'actor-delegacia', name: 'Delegacia de Polícia',
    category_slug: 'seguranca', category_label: 'Segurança', color: '#1D4ED8',
    icon: 'shield', latitude: -2.426, longitude: -54.733,
    distance_from_origin_m: null, layer: 'citywide_essential',
  },
];

const legend = [
  ['alimentacao', 'Alimentação', '#D97706', 'utensils'],
  ['hospedagem', 'Hospedagem', '#2563EB', 'bed'],
  ['transporte', 'Transporte', '#7C3AED', 'bus'],
  ['saude', 'Saúde', '#DC2626', 'heart-pulse'],
  ['seguranca', 'Segurança', '#1D4ED8', 'shield'],
].map(([category_slug, label, color, icon], sort_order) => ({
  category_slug, label, color, icon, sort_order: sort_order + 1,
  count: pins.filter((pin) => pin.category_slug === category_slug).length,
}));

const mapPayload = {
  data: {
    route_id: routeId,
    selected_origin_id: originId,
    bounds: { min_lat: -2.60, max_lat: -2.42, min_lng: -54.98, max_lng: -54.69 },
    city_bounds: { min_lat: -2.64, max_lat: -2.37, min_lng: -55.04, max_lng: -54.62 },
    geometry: {
      id: 'geometry-porto', route_origin_id: originId, provider: 'fixture-evidence',
      distance_m: 45229, duration_s: 4200,
      geojson: {
        type: 'LineString',
        coordinates: [
          [-54.708, -2.443], [-54.755, -2.465], [-54.820, -2.500],
          [-54.885, -2.535], [-54.934, -2.548], [-54.952, -2.575],
        ],
      },
    },
    pins,
    legend,
  },
};

const actorPayload = {
  data: pins.map((pin) => ({
    id: pin.actor_id,
    slug: pin.actor_id,
    name: pin.name,
    category_slug: pin.category_slug,
    category_label: pin.category_label,
    address: pin.layer === 'citywide_essential' ? 'Centro de Santarém, PA' : 'Rota Pindobal, PA',
  })),
  meta: { total: pins.length, limit: 20, next_cursor: null },
};

const server = http.createServer((request, response) => {
  response.setHeader('Access-Control-Allow-Origin', '*');
  response.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Request-ID');
  response.setHeader('Content-Type', 'application/json; charset=utf-8');
  if (request.method === 'OPTIONS') {
    response.writeHead(204);
    response.end();
    return;
  }
  const url = new URL(request.url ?? '/', 'http://localhost:8000');
  if (url.pathname === `/api/v1/routes/${routeId}/map`) {
    response.writeHead(200);
    response.end(JSON.stringify(mapPayload));
    return;
  }
  if (url.pathname === `/api/v1/routes/${routeId}/actors`) {
    response.writeHead(200);
    response.end(JSON.stringify(actorPayload));
    return;
  }
  response.writeHead(404);
  response.end(JSON.stringify({ error: { code: 'NOT_FOUND', message: 'Fixture endpoint not found.' } }));
});

server.listen(8000, '127.0.0.1', () => {
  process.stdout.write('Map evidence fixture API listening at http://127.0.0.1:8000\n');
});
