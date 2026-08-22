import 'react-native-url-polyfill/auto';

import { createClient, processLock } from '@supabase/supabase-js';

import { authStorage } from './storage';

function requirePublicEnv(name: string, value: string | undefined): string {
  if (!value || value.includes('replace_me') || value.includes('your-project')) {
    throw new Error(`Configuração pública obrigatória ausente: ${name}`);
  }
  return value;
}

const supabaseUrl = requirePublicEnv(
  'EXPO_PUBLIC_SUPABASE_URL',
  process.env.EXPO_PUBLIC_SUPABASE_URL
);
const publishableKey = requirePublicEnv(
  'EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY',
  process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY || process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY
);

const parsedSupabaseUrl = new URL(supabaseUrl);
if (parsedSupabaseUrl.protocol !== 'https:' || !parsedSupabaseUrl.hostname.endsWith('.supabase.co')) {
  throw new Error('EXPO_PUBLIC_SUPABASE_URL deve ser uma URL HTTPS de projeto Supabase.');
}
if (!publishableKey.startsWith('sb_publishable_') && !publishableKey.startsWith('eyJ')) {
  throw new Error('A configuração do Expo deve usar uma chave pública válida do Supabase (sb_publishable_ ou eyJ...).');
}

export const supabase = createClient(supabaseUrl, publishableKey, {
  auth: {
    storage: authStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
    lock: processLock,
    storageKey: `econexao-auth-${parsedSupabaseUrl.hostname}`,
  },
});
