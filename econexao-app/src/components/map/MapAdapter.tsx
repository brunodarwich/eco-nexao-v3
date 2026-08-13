// Metro selects MapAdapter.native.tsx on Android/iOS and MapAdapter.web.tsx on web.
// This fallback keeps non-platform-aware tooling aligned with the native contract.
export { MapAdapter } from './MapAdapter.native';
export type { MapAdapterProps } from './MapAdapter.types';
