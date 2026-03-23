import { supabase } from '@/integrations/supabase/client';
import type { Profile } from '@/types/database';

const IS_DEV = import.meta.env.DEV;

function log(...args: unknown[]) {
  if (IS_DEV) console.log('[Auth]', ...args);
}

function warn(...args: unknown[]) {
  if (IS_DEV) console.warn('[Auth]', ...args);
}

// ─── Session ─────────────────────────────────────────────────────────────────

export async function signInWithPassword(
  email: string,
  password: string,
) {
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
}

export async function signOutUser() {
  // Clear any sessionStorage keys before signing out
  clearSessionKeys();
  const { error } = await supabase.auth.signOut();
  if (error) warn('signOut error:', error.message);
}

/**
 * Moves Supabase auth tokens from localStorage to sessionStorage.
 * This makes the session ephemeral — it clears when the tab/browser closes.
 */
export function moveSessionToSessionStorage() {
  const keys = Object.keys(localStorage).filter((k) => k.startsWith('sb-'));
  keys.forEach((k) => {
    const val = localStorage.getItem(k);
    if (val) sessionStorage.setItem(k, val);
    localStorage.removeItem(k);
  });
  log('Session moved to sessionStorage (ephemeral)');
}

function clearSessionKeys() {
  const lsKeys = Object.keys(localStorage).filter((k) => k.startsWith('sb-'));
  lsKeys.forEach((k) => localStorage.removeItem(k));
  const ssKeys = Object.keys(sessionStorage).filter((k) => k.startsWith('sb-'));
  ssKeys.forEach((k) => sessionStorage.removeItem(k));
}

// ─── Profile ─────────────────────────────────────────────────────────────────

export async function fetchProfile(userId: string): Promise<Profile | null> {
  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single();

  if (error) {
    warn('fetchProfile error:', error.message);
    return null;
  }

  return data as Profile;
}
