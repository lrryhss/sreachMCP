'use client';

import { useAuthMonitor } from '@/hooks/use-auth-monitor';

export function AuthMonitor({ children }: { children: React.ReactNode }) {
  useAuthMonitor();
  return <>{children}</>;
}