export interface AccessibilityPreferences {
  screenReaderMode: boolean;
  highContrast: boolean;
  textScale: number;
  locale: string;
}

export interface AppState {
  activeRegionId: string | null;
  accessibility: AccessibilityPreferences;
}

export type AppAction =
  | { type: 'SET_ACTIVE_REGION'; payload: string | null }
  | { type: 'SET_ACCESSIBILITY'; payload: Partial<AccessibilityPreferences> };

export const initialAppState: AppState = {
  activeRegionId: null,
  accessibility: {
    screenReaderMode: false,
    highContrast: false,
    textScale: 1,
    locale: 'pt-BR',
  },
};

export function appReducer(state: AppState, action: AppAction): AppState {
  if (action.type === 'SET_ACTIVE_REGION') {
    return { ...state, activeRegionId: action.payload };
  }
  if (action.type === 'SET_ACCESSIBILITY') {
    return {
      ...state,
      accessibility: { ...state.accessibility, ...action.payload },
    };
  }
  return state;
}
