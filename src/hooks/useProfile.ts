import { useEffect, useState } from 'react';
import type { Profile } from '@/types/database';
import { fetchProfile } from '@/lib/authService';

/**
 * Fetches and caches the user profile whenever userId changes.
 */
export function useProfile(userId: string | undefined): {
  profile: Profile | null;
  clearProfile: () => void;
} {
  const [profile, setProfile] = useState<Profile | null>(null);

  useEffect(() => {
    if (!userId) {
      setProfile(null);
      return;
    }

    let cancelled = false;

    fetchProfile(userId).then((p) => {
      if (!cancelled) setProfile(p);
    });

    return () => {
      cancelled = true;
    };
  }, [userId]);

  const clearProfile = () => setProfile(null);

  return { profile, clearProfile };
}
