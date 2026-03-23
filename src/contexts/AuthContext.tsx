import { createContext, useContext, useCallback, ReactNode } from 'react';
import { User } from '@supabase/supabase-js';
import type { Profile } from '@/types/database';
import { useAuthSession } from '@/hooks/useAuthSession';
import { useProfile } from '@/hooks/useProfile';
import {
  signInWithPassword,
  signOutUser,
  moveSessionToSessionStorage,
} from '@/lib/authService';

// ─── Types ───────────────────────────────────────────────────────────────────

interface AuthContextType {
  user: User | null;
  profile: Profile | null;
  loading: boolean;
  signIn: (email: string, password: string, keepConnected?: boolean) => Promise<void>;
  signOut: () => Promise<void>;
}

// ─── Context ─────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ─── Provider ────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const { user, loading } = useAuthSession();
  const { profile, clearProfile } = useProfile(user?.id);

  const signIn = useCallback(
    async (email: string, password: string, keepConnected = true) => {
      await signInWithPassword(email, password);

      if (!keepConnected) {
        // Defer so the session is fully written to localStorage first
        setTimeout(() => moveSessionToSessionStorage(), 0);
      }
    },
    [],
  );

  const signOut = useCallback(async () => {
    clearProfile();
    await signOutUser();
  }, [clearProfile]);

  return (
    <AuthContext.Provider value={{ user, profile, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
