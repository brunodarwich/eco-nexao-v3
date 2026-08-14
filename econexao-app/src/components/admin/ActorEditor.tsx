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
import type { AdminActorSchema } from '../../api/types';

export interface ActorEditorProps {
  initialActors?: AdminActorSchema[];
  onSaved?: () => void;
}

export const ActorEditor: React.FC<ActorEditorProps> = ({
  initialActors = [],
  onSaved,
}) => {
  const [actors, setActors] = useState<AdminActorSchema[]>(initialActors);
  const [selectedActor, setSelectedActor] = useState<AdminActorSchema | null>(null);

  const [name, setName] = useState(selectedActor?.name || '');
  const [description, setDescription] = useState(selectedActor?.description || '');
  const [latitude, setLatitude] = useState(
    selectedActor?.latitude ? String(selectedActor.latitude) : '-2.4542'
  );
  const [longitude, setLongitude] = useState(
    selectedActor?.longitude ? String(selectedActor.longitude) : '-54.9124'
  );

  // Gallery metadata input fields (ADR 0008)
  const [coverAltText, setCoverAltText] = useState('Foto do estabelecimento local');
  const [coverCredit, setCoverCredit] = useState('Acervo Comunidade Pindobal');

  const [isLoadingData, setIsLoadingData] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchInitialActors = async () => {
      if (initialActors.length === 0) {
        try {
          const response = await apiClient.getAdminActors();
          if (isMounted && response.data) {
            setActors(response.data);
          }
        } catch {
          // Ignora falha silenciosa
        }
      }
    };

    if (initialActors.length === 0) {
      void fetchInitialActors();
    }
    return () => {
      isMounted = false;
    };
  }, [initialActors.length]);

  const handleSelectActor = (actor: AdminActorSchema) => {
    setSelectedActor(actor);
    setName(actor.name);
    setDescription(actor.description || '');
    setLatitude(actor.latitude ? String(actor.latitude) : '-2.4542');
    setLongitude(actor.longitude ? String(actor.longitude) : '-54.9124');
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  const handleNewActor = () => {
    setSelectedActor(null);
    setName('');
    setDescription('');
    setLatitude('-2.4542');
    setLongitude('-54.9124');
    setCoverAltText('Foto do estabelecimento local');
    setCoverCredit('Acervo Comunidade Pindobal');
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  const handleSaveActor = async () => {
    if (!name.trim()) {
      setErrorMessage('O nome do ator/estabelecimento é obrigatório.');
      return;
    }

    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);
    if (isNaN(lat) || lat < -90 || lat > 90) {
      setErrorMessage('A latitude deve ser um número válido entre -90 e 90.');
      return;
    }
    if (isNaN(lng) || lng < -180 || lng > 180) {
      setErrorMessage('A longitude deve ser um número válido entre -180 e 180.');
      return;
    }

    if (!coverAltText.trim() || !coverCredit.trim()) {
      setErrorMessage('Metadados de imagem (Alt Text e Créditos) são obrigatórios conforme ADR 0008.');
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      if (selectedActor) {
        const response = await apiClient.updateAdminActor(selectedActor.id, {
          name: name.trim(),
          description: description.trim(),
          latitude: lat,
          longitude: lng,
        });
        setActors((prev) =>
          prev.map((a) => (a.id === selectedActor.id ? response.data : a))
        );
        setSelectedActor(response.data);
        setSuccessMessage(`Ator '${response.data.name}' atualizado com sucesso!`);
      } else {
        const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
        const response = await apiClient.createAdminActor({
          category_id: '00000000-0000-0000-0000-000000000001',
          name: name.trim(),
          slug: slug || `ator-${Date.now()}`,
          description: description.trim(),
          latitude: lat,
          longitude: lng,
          green_badge_status: 'none',
          verification_status: 'unverified',
        });
        setActors((prev) => [response.data, ...prev]);
        setSelectedActor(response.data);
        setSuccessMessage(`Ator '${response.data.name}' cadastrado com sucesso!`);
      }
      onSaved?.();
    } catch (err: any) {
      setErrorMessage(err?.message || 'Falha ao salvar o ator comunitário.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.headerRow}>
        <Text style={styles.headerTitle}>Gestão de Atores & Estabelecimentos Sustentáveis</Text>
        <TouchableOpacity
          style={styles.newButton}
          onPress={handleNewActor}
          accessibilityRole="button"
          accessibilityLabel="Cadastrar novo ator"
          accessibilityHint="Limpa o formulário para cadastro de um novo estabelecimento comunitário"
        >
          <Text style={styles.newButtonText}>+ Novo Ator</Text>
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

      {/* Loading indicator */}
      {isLoadingData && (
        <View style={styles.inlineLoading}>
          <ActivityIndicator size="small" color="#059669" />
          <Text style={styles.inlineLoadingText}>Carregando atores cadastrados...</Text>
        </View>
      )}

      {/* Existing Actors Chips */}
      {actors.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Atores no Território ({actors.length})</Text>
          <View style={styles.chipsRow}>
            {actors.map((actor) => (
              <TouchableOpacity
                key={actor.id}
                style={[
                  styles.chip,
                  selectedActor?.id === actor.id && styles.activeChip,
                ]}
                onPress={() => handleSelectActor(actor)}
                accessibilityRole="button"
                accessibilityLabel={`Selecionar ator ${actor.name}`}
              >
                <Text
                  style={[
                    styles.chipText,
                    selectedActor?.id === actor.id && styles.activeChipText,
                  ]}
                >
                  {actor.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}

      {/* Form Card */}
      <View style={styles.formCard}>
        <Text style={styles.formTitle}>
          {selectedActor ? `Editando: ${selectedActor.name}` : 'Cadastrar Novo Ator Comunitário'}
        </Text>

        <View style={styles.fieldGroup}>
          <Text style={styles.label}>Nome do Estabelecimento / Ator *</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="Ex: Artesanato Dona Maria"
            accessibilityLabel="Campo nome do ator"
          />
        </View>

        <View style={styles.fieldGroup}>
          <Text style={styles.label}>Descrição das Atividades</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={description}
            onChangeText={setDescription}
            placeholder="Produtos sustentáveis, história e práticas locais..."
            multiline
            numberOfLines={3}
            accessibilityLabel="Campo descrição do ator"
          />
        </View>

        <View style={styles.rowFields}>
          <View style={[styles.fieldGroup, { flex: 1 }]}>
            <Text style={styles.label}>Latitude *</Text>
            <TextInput
              style={styles.input}
              value={latitude}
              onChangeText={setLatitude}
              keyboardType="numeric"
              accessibilityLabel="Campo latitude"
            />
          </View>

          <View style={[styles.fieldGroup, { flex: 1 }]}>
            <Text style={styles.label}>Longitude *</Text>
            <TextInput
              style={styles.input}
              value={longitude}
              onChangeText={setLongitude}
              keyboardType="numeric"
              accessibilityLabel="Campo longitude"
            />
          </View>
        </View>

        {/* Media Metadata per ADR 0008 */}
        <View style={styles.metaContainer}>
          <Text style={styles.metaTitle}>Metadados de Imagem & Direitos (ADR 0008)</Text>
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Texto Alternativo (Alt Text) *</Text>
            <TextInput
              style={styles.input}
              value={coverAltText}
              onChangeText={setCoverAltText}
              accessibilityLabel="Campo texto alternativo da foto"
            />
          </View>

          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Crédito Fotográfico *</Text>
            <TextInput
              style={styles.input}
              value={coverCredit}
              onChangeText={setCoverCredit}
              accessibilityLabel="Campo crédito fotográfico"
            />
          </View>
        </View>

        <TouchableOpacity
          style={[styles.submitButton, isSaving && styles.disabledButton]}
          onPress={handleSaveActor}
          disabled={isSaving}
          accessibilityRole="button"
          accessibilityLabel="Salvar dados do ator comunitário"
        >
          {isSaving ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.submitButtonText}>
              {selectedActor ? 'Atualizar Ator' : 'Cadastrar Ator'}
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
    flex: 1,
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
  chipsRow: {
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
  metaContainer: {
    backgroundColor: '#F1F5F9',
    padding: 16,
    borderRadius: 8,
    marginVertical: 10,
  },
  metaTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 10,
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
