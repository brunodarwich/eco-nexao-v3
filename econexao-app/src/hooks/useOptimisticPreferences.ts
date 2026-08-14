import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AccessibilityInfo } from 'react-native';
import { apiClient } from '../api/client';
import { queryKeys } from '../api/queryKeys';
import { useAuth } from './useAuth';
import { useAppContext } from '../state/useAppContext';
import { UserPreferencesEnvelope, UserPreferencesUpdate } from '../api/types';

export function useOptimisticPreferences() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { dispatch } = useAppContext();
  const userId = user?.id ?? '';

  return useMutation({
    mutationFn: async (updates: UserPreferencesUpdate) => {
      return apiClient.updateMyPreferences(updates);
    },
    onMutate: async (updates: UserPreferencesUpdate) => {
      // 1. Cancelar queries concorrentes
      await queryClient.cancelQueries({ queryKey: queryKeys.myPreferences(userId) });
      await queryClient.cancelQueries({ queryKey: queryKeys.bootstrap(userId) });

      // 2. Snapshot do estado anterior
      const previousPrefs = queryClient.getQueryData<UserPreferencesEnvelope>(
        queryKeys.myPreferences(userId)
      );

      // 3. Atualização otimista no cache do React Query
      if (previousPrefs?.data) {
        const updatedPrefs: UserPreferencesEnvelope = {
          ...previousPrefs,
          data: {
            ...previousPrefs.data,
            ...updates,
            screen_reader_mode:
              updates.screen_reader_mode !== undefined && updates.screen_reader_mode !== null
                ? updates.screen_reader_mode
                : previousPrefs.data.screen_reader_mode ?? false,
            high_contrast:
              updates.high_contrast !== undefined && updates.high_contrast !== null
                ? updates.high_contrast
                : previousPrefs.data.high_contrast ?? false,
            text_scale:
              updates.text_scale !== undefined && updates.text_scale !== null
                ? updates.text_scale
                : previousPrefs.data.text_scale ?? 1.0,
            locale:
              updates.locale !== undefined && updates.locale !== null
                ? updates.locale
                : previousPrefs.data.locale ?? 'pt-BR',
          },
        };
        queryClient.setQueryData(queryKeys.myPreferences(userId), updatedPrefs);
      }

      // 4. Atualização otimista no AppContext (Acessibilidade)
      dispatch({
        type: 'SET_ACCESSIBILITY',
        payload: {
          ...(updates.screen_reader_mode !== undefined &&
            updates.screen_reader_mode !== null && {
              screenReaderMode: updates.screen_reader_mode,
            }),
          ...(updates.high_contrast !== undefined &&
            updates.high_contrast !== null && {
              highContrast: updates.high_contrast,
            }),
          ...(updates.text_scale !== undefined &&
            updates.text_scale !== null && {
              textScale: updates.text_scale,
            }),
          ...(updates.locale !== undefined &&
            updates.locale !== null && {
              locale: updates.locale,
            }),
        },
      });

      return { previousPrefs };
    },
    onError: (_error, _updates, context) => {
      // Rollback no cache e no AppContext
      if (context?.previousPrefs?.data) {
        queryClient.setQueryData(
          queryKeys.myPreferences(userId),
          context.previousPrefs
        );
        const prev = context.previousPrefs.data;
        dispatch({
          type: 'SET_ACCESSIBILITY',
          payload: {
            screenReaderMode: prev.screen_reader_mode ?? false,
            highContrast: prev.high_contrast ?? false,
            textScale: prev.text_scale ?? 1.0,
            locale: prev.locale ?? 'pt-BR',
          },
        });
      }
      AccessibilityInfo.announceForAccessibility(
        'Erro ao salvar preferências de acessibilidade. Alterações revertidas.'
      );
    },
    onSuccess: () => {
      AccessibilityInfo.announceForAccessibility(
        'Preferências de acessibilidade atualizadas com sucesso.'
      );
      void queryClient.invalidateQueries({ queryKey: queryKeys.myPreferences(userId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.bootstrap(userId) });
    },
  });
}
