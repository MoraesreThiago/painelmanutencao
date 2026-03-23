import { useEffect, useState, useCallback } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';

interface AuthSessionState {
  user: User | null;
  loading: boolean;
}

/**
 * Manages Supabase auth session lifecycle (subscribe + initial fetch).
 * Returns the current user and a loading flag.
 */
export function useAuthSession(): AuthSessionState {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const handleSession = useCallback((session: Session | null) => {
    setUser(session?.user ?? null);
    setLoading(false);
  }, []);

  useEffect(() => {
    // 1. Subscribe to auth changes FIRST (per Supabase best practices)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      handleSession(session);
    });

    // 2. Then fetch existing session
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (error && import.meta.env.DEV) {
        console.warn('[Auth] getSession error:', error.message);
      }
      handleSession(session);
    });

    return () => subscription.unsubscribe();
  }, [handleSession]);

  return { user, loading };
}
