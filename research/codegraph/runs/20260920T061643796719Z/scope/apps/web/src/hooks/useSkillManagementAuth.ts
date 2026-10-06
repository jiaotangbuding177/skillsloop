'use client';

import { usePathname, useRouter } from '@/i18n/navigation';
import React from 'react';
import { getCurrentUser, onSessionChange } from '@/lib/user';
import { useScopedAdminAccess } from '@/hooks/useScopedAdminAccess';

export type SkillManagementAuthState = 'checking' | 'unauthenticated' | 'unauthorized' | 'authorized';

export function useSkillManagementAuth() {
  const router = useRouter();
  const pathname = usePathname();
  const { ready, canAccessSkillManagement } = useScopedAdminAccess();
  const [authState, setAuthState] = React.useState<SkillManagementAuthState>('checking');

  React.useEffect(() => {
    const syncAuthState = () => {
      const user = getCurrentUser();
      if (!user) {
        setAuthState('unauthenticated');
        return;
      }
      if (!ready) {
        setAuthState('checking');
        return;
      }
      setAuthState(canAccessSkillManagement ? 'authorized' : 'unauthorized');
    };

    syncAuthState();
    const unsubSession = onSessionChange(syncAuthState);
    return unsubSession;
  }, [ready, canAccessSkillManagement]);

  React.useEffect(() => {
    if (authState === 'unauthenticated') {
      const redirect = pathname || '/admin/skills';
      router.replace(`/login?redirect=${encodeURIComponent(redirect)}`);
      return;
    }
    if (authState === 'unauthorized') {
      router.replace('/');
    }
  }, [authState, pathname, router]);

  return authState;
}
