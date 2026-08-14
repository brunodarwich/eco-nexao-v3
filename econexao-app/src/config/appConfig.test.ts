import appJson from '../../app.json';
import * as fs from 'fs';
import * as path from 'path';

describe('ECO-1905: Identidade Expo, Configuração de Deep Links e Variáveis', () => {
  test('app.json define nome oficial, slug e bundle identifiers para iOS e Android', () => {
    expect(appJson.expo.name).toBe('ECOnexão');
    expect(appJson.expo.slug).toBe('econexao-app');
    expect(appJson.expo.scheme).toBe('econexao');
    expect(appJson.expo.android?.package).toBe('org.econexao.app');
    expect(appJson.expo.ios?.bundleIdentifier).toBe('org.econexao.app');
  });

  test('app.json inclui plugins essenciais sem upgrade indevido de SDK', () => {
    expect(appJson.expo.plugins).toContain('expo-router');
    expect(appJson.expo.plugins).toContain('expo-secure-store');
  });

  test('.env.example não contém credenciais reais ou chaves de serviço', () => {
    const envExamplePath = path.resolve(__dirname, '../../.env.example');
    const envContent = fs.readFileSync(envExamplePath, 'utf8');

    // Nenhuma chave de valor real ou secreta deve ser atribuída
    const valueLines = envContent.split('\n').filter((l) => l.trim() && !l.trim().startsWith('#'));
    const valuesJoined = valueLines.join('\n');

    expect(valuesJoined).not.toMatch(/sb_secret_/);
    expect(valuesJoined).not.toMatch(/service_role/);
    expect(valuesJoined).not.toMatch(/postgres:\/\//);
    expect(valuesJoined).not.toMatch(/postgresql:\/\//);
    expect(valuesJoined).toContain('EXPO_PUBLIC_API_URL');
    expect(valuesJoined).toContain('EXPO_PUBLIC_SUPABASE_URL');
    expect(valuesJoined).toContain('EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY');
  });
});
