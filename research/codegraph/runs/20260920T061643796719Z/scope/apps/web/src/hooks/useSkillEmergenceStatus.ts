'use client';

import React from 'react';
import {
  getSkillEmergenceAccessApi,
  putSkillEmergencePreferenceApi,
  type SkillEmergenceAccessResponse,
} from '@/api';
import {
  ACTIVE_ENTERPRISE_CHANGED_EVENT,
  getActiveEnterpriseId,
} from '@/lib/enterprise-context';

export const SKILL_EMERGENCE_CHANGED_EVENT = 'skill-emergence-changed';

export function emitSkillEmergenceChanged() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(SKILL_EMERGENCE_CHANGED_EVENT));
  }
}

export function useSkillEmergenceStatus(enabled = true) {
  const [access, setAccess] = React.useState<SkillEmergenceAccessResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [updating, setUpdating] = React.useState(false);
  const [enterpriseId, setEnterpriseId] = React.useState(() => getActiveEnterpriseId());

  React.useEffect(() => {
    const syncEnterpriseId = () => {
      setEnterpriseId(getActiveEnterpriseId());
    };
    syncEnterpriseId();
    window.addEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, syncEnterpriseId);
    window.addEventListener('storage', syncEnterpriseId);
    return () => {
      window.removeEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, syncEnterpriseId);
      window.removeEventListener('storage', syncEnterpriseId);
    };
  }, []);

  const refresh = React.useCallback(async () => {
    if (!enabled) return null;
    const activeEnterpriseId = getActiveEnterpriseId();
    if (!activeEnterpriseId) {
      setAccess(null);
      return null;
    }
    setLoading(true);
    try {
      const next = await getSkillEmergenceAccessApi();
      setAccess(next);
      return next;
    } catch {
      setAccess(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  React.useEffect(() => {
    void refresh();
  }, [refresh, enterpriseId]);

  React.useEffect(() => {
    const refreshStatus = () => void refresh();
    window.addEventListener(SKILL_EMERGENCE_CHANGED_EVENT, refreshStatus);
    return () => window.removeEventListener(SKILL_EMERGENCE_CHANGED_EVENT, refreshStatus);
  }, [refresh]);

  const setPreference = React.useCallback(
    async (payload: {
      enabled: boolean;
      intervalDays?: number;
      autoAcceptPersonal?: boolean;
    }) => {
      setUpdating(true);
      try {
        await putSkillEmergencePreferenceApi(payload);
        return await refresh();
      } finally {
        setUpdating(false);
      }
    },
    [refresh],
  );

  return {
    access,
    loading,
    updating,
    refresh,
    setPreference,
    isConsumer: Boolean(access?.isConsumer),
    canTogglePreference: Boolean(access?.canTogglePreference),
  };
}
