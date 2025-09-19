'use client';

import { useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

export function useAuthMonitor() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (session?.error === 'RefreshAccessTokenError') {
      // Token refresh failed, sign out
      toast.error('Your session has expired. Please sign in again.');
      signOut({ callbackUrl: '/auth/signin' });
    }
  }, [session]);

  useEffect(() => {
    // Show warning before token expires
    if (session?.accessToken) {
      const checkExpiry = () => {
        const expiresAt = session.accessTokenExpires as number;
        const now = Date.now();
        const timeUntilExpiry = expiresAt - now;

        // Show warning 5 minutes before expiry
        if (timeUntilExpiry < 5 * 60 * 1000 && timeUntilExpiry > 4 * 60 * 1000) {
          toast.warning('Your session will expire soon. Activity will refresh it automatically.');
        }
      };

      // Check every minute
      const interval = setInterval(checkExpiry, 60 * 1000);
      checkExpiry(); // Check immediately

      return () => clearInterval(interval);
    }
  }, [session]);

  return { isAuthenticated: status === 'authenticated' && !session?.error };
}