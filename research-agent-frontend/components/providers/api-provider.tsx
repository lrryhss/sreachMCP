'use client';

import { useEffect } from 'react';
import { useSession } from 'next-auth/react';
import api from '@/lib/api';

export function ApiProvider({ children }: { children: React.ReactNode }) {
  const { data: session, update } = useSession();

  useEffect(() => {
    // Update the API client's tokens whenever the session changes
    if (session?.accessToken && session?.refreshToken) {
      api.setTokens(session.accessToken as string, session.refreshToken as string);
    } else if (session?.accessToken) {
      api.setAccessToken(session.accessToken as string);
    } else {
      api.setTokens(null, null);
    }
  }, [session]);

  useEffect(() => {
    // Listen for token refresh events
    const handleTokenRefresh = async (event: CustomEvent) => {
      const { accessToken, refreshToken } = event.detail;

      // Update the session with new tokens
      if (update) {
        await update({
          accessToken,
          refreshToken,
        });
      }
    };

    window.addEventListener('token-refreshed', handleTokenRefresh as EventListener);

    return () => {
      window.removeEventListener('token-refreshed', handleTokenRefresh as EventListener);
    };
  }, [update]);

  return <>{children}</>;
}