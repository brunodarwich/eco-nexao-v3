import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { apiClient } from '../../api/client';
import type { AdminRegionSchema, AdminRouteSchema } from '../../api/types';

export interface TerritoryEditorProps {
  initialRegions?: AdminRegionSchema[];
  initialRoutes?: AdminRouteSchema[];
  onSaved?: () => void;
}

export const TerritoryEditor: React.FC<TerritoryEditorProps> = ({
  initialRegions = [],
  initialRoutes = [],
  onSaved,
}) => {
  const [regions, setRegions] = useState<AdminRegionSchema[]>(initialRegions);
  const [routes, setRoutes] = useState<AdminRouteSchema[]>(initialRoutes);
  const [selectedRoute, setSelectedRoute] = useState<AdminRouteSchema | null>(null);

  const [title, setTitle] = useState(selectedRoute?.title || '');
  const [summary, setSummary] = useState(selectedRoute?.summary || '');
  const [city, setCity] = useState(selectedRoute?.city || 'Belterra');
  const [stateCode, setStateCode] = useState(selectedRoute?.state_code || 'PA');

  const [isLoadingData, setIsLoadingData] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchInitialData = async () => {
      if (initialRegions.length === 0) {
        try {
          const regionsRes = await apiClient.getAdminRegions();
          if (isMounted && regionsRes.data) {
            setRegions(regionsRes.data);
          }
        } catch {
          // Ignora falha de listagem
        }
      }
      if (initialRoutes.length === 0) {
        try {
          const routesRes = await apiClient.getAdminRoutes();
          if (isMounted && routesRes.data) {
            setRoutes(routesRes.data);
          }
        } catch {
          // Ignora falha de listagem
        }
      }
    };

    if (initialRegions.length === 0 || initialRoutes.length === 0) {
      void fetchInitialData();
    }
    return () => {
      isMounted = false;
    };
  }, [initialRegions.length, initialRoutes.length]);

  const handleSelectRoute = (route: AdminRouteSchema) => {
    setSelectedRoute(route);
    setTitle(route.title);
    setSummary(route.summary || '');
    setCity(route.city || 'Belterra');
    setStateCode(route.state_code || 'PA');
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  const handleNewRoute = () => {
    setSelectedRoute(null);
    setTitle('');
    setSummary('');
    setCity('Belterra');
    setStateCode('PA');
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  const handleSaveRoute = async () => {
    if (!title.trim()) {
      setErrorMessage('O título da rota é obrigatório.');
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      if (selectedRoute) {
        const response = await apiClient.updateAdminRoute(selectedRoute.id, {
          title: title.trim(),
          summary: summary.trim(),
          city: city.trim(),
          state_code: stateCode.trim(),
        });
        setRoutes((prev) =>
          prev.map((r) => (r.id === selectedRoute.id ? response.data : r))
        );
        setSelectedRoute(response.data);
        setSuccessMessage(`Rota '${response.data.title}' atualizada com sucesso!`);
      } else {
        const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
        const regionId = regions[0]?.id || '00000000-0000-0000-0000-000000000001';
        const response = await apiClient.createAdminRoute({
          region_id: regionId,
          title: title.trim(),
          slug: slug || `rota-${Date.now()}`,
          summary: summary.trim(),
          city: city.trim(),
          state_code: stateCode.trim(),
          status: 'draft',
          is_verified: false,
        });
        setRoutes((prev) => [response.data, ...prev]);
        setSelectedRoute(response.data);
        setSuccessMessage(`Rota '${response.data.title}' criada com sucesso!`);
      }
      onSaved?.();
    } catch (err: any) {
      if (err?.status === 409) {
        setErrorMessage('Conflito de edição (409): Outro editor modificou esta rota concorrentemente.');
      } else {
        setErrorMessage(err?.message || 'Falha ao salvar a rota territorial.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.headerRow}>
        <Text style={styles.headerTitle}>Editor Territorial & Rotas Comunitárias</Text>
        <TouchableOpacity
          style={styles.newButton}
          onPress={handleNewRoute}
          accessibilityRole="button"
          accessibilityLabel="Criar nova rota"
          accessibilityHint="Limpa o formulário para cadastro de uma nova rota territorial"
        >
          <Text style={styles.newButtonText}>+ Nova Rota</Text>
        </TouchableOpacity>
      </View>

      {/* Messages */}
      {errorMessage && (
        <View style={styles.errorBox} accessibilityRole="alert">
          <Text style={styles.errorText}>{errorMessage}</Text>
        </View>
      )}
      {successMessage && (
        <View style={styles.successBox} accessibilityRole="alert">
          <Text style={styles.successText}>{successMessage}</Text>
        </View>
      )}

      {/* Loading list indicator */}
      {isLoadingData && (
        <View style={styles.inlineLoading}>
          <ActivityIndicator size="small" color="#059669" />
          <Text style={styles.inlineLoadingText}>Carregando rotas cadastradas...</Text>
        </View>
      )}

      {/* Existing Routes Selector */}
      {routes.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Rotas no Território ({routes.length})</Text>
          <View style={styles.routesChipRow}>
            {routes.map((r) => (
              <TouchableOpacity
                key={r.id}
                style={[
                  styles.chip,
                  selectedRoute?.id === r.id && styles.activeChip,
                ]}
                onPress={() => handleSelectRoute(r)}
                accessibilityRole="button"
                accessibilityLabel={`Selecionar rota ${r.title}`}
              >
                <Text
                  style={[
                    styles.chipText,
                    selectedRoute?.id === r.id && styles.activeChipText,
                  ]}
                >
                  {r.title}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}

      {/* Route Form */}
      <View style={styles.formCard}>
        <Text style={styles.formTitle}>
          {selectedRoute ? `Editando: ${selectedRoute.title}` : 'Cadastrar Nova Rota Comunitária'}
        </Text>

        <View style={styles.fieldGroup}>
          <Text style={styles.label}>Título da Rota *</Text>
          <TextInput
            style={styles.input}
            value={title}
            onChangeText={setTitle}
            placeholder="Ex: Trilha das Praias de Pindobal"
            accessibilityLabel="Campo título da rota"
          />
        </View>

        <View style={styles.fieldGroup}>
          <Text style={styles.label}>Resumo Editorial</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={summary}
            onChangeText={setSummary}
            placeholder="Breve resumo sobre a rota territorial..."
            multiline
            numberOfLines={3}
            accessibilityLabel="Campo resumo da rota"
          />
        </View>

        <View style={styles.rowFields}>
          <View style={[styles.fieldGroup, { flex: 1 }]}>
            <Text style={styles.label}>Município</Text>
            <TextInput
              style={styles.input}
              value={city}
              onChangeText={setCity}
              accessibilityLabel="Campo município"
            />
          </View>

          <View style={[styles.fieldGroup, { flex: 1 }]}>
            <Text style={styles.label}>UF</Text>
            <TextInput
              style={styles.input}
              value={stateCode}
              onChangeText={setStateCode}
              accessibilityLabel="Campo UF"
            />
          </View>
        </View>

        <TouchableOpacity
          style={[styles.submitButton, isSaving && styles.disabledButton]}
          onPress={handleSaveRoute}
          disabled={isSaving}
          accessibilityRole="button"
          accessibilityLabel="Salvar dados territoriais da rota"
        >
          {isSaving ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.submitButtonText}>
              {selectedRoute ? 'Atualizar Rota' : 'Cadastrar Rota'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  contentContainer: {
    padding: 20,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
    flexWrap: 'wrap',
    gap: 12,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#0F172A',
  },
  newButton: {
    backgroundColor: '#059669',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
  },
  newButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  errorBox: {
    backgroundColor: '#FEE2E2',
    borderColor: '#FCA5A5',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    color: '#991B1B',
    fontSize: 14,
    fontWeight: '500',
  },
  successBox: {
    backgroundColor: '#D1FAE5',
    borderColor: '#6EE7B7',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  successText: {
    color: '#065F46',
    fontSize: 14,
    fontWeight: '500',
  },
  inlineLoading: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  inlineLoadingText: {
    fontSize: 13,
    color: '#64748B',
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 8,
  },
  routesChipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#E2E8F0',
  },
  activeChip: {
    backgroundColor: '#059669',
  },
  chipText: {
    fontSize: 13,
    color: '#334155',
    fontWeight: '500',
  },
  activeChipText: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  formCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  formTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 16,
  },
  fieldGroup: {
    marginBottom: 14,
  },
  rowFields: {
    flexDirection: 'row',
    gap: 12,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 6,
  },
  input: {
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#0F172A',
    backgroundColor: '#F8FAFC',
  },
  textArea: {
    minHeight: 70,
    textAlignVertical: 'top',
  },
  submitButton: {
    backgroundColor: '#059669',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  disabledButton: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});
