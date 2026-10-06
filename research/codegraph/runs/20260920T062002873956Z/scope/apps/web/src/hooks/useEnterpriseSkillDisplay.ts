'use client';

import React from 'react';
import {
  getEnterpriseSkillDisplayApi,
  getGlobalSkillDisplayApi,
  type SkillDisplayBundle,
} from '@/api';
import { ACTIVE_ENTERPRISE_CHANGED_EVENT, getActiveEnterpriseId } from '@/lib/enterprise-context';

export function useEnterpriseSkillDisplay() {
  const [enterpriseId, setEnterpriseId] = React.useState('');
  const [displayContext, setDisplayContext] = React.useState<SkillDisplayBundle | null>(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    const syncEnterpriseId = () => setEnterpriseId(getActiveEnterpriseId());
    syncEnterpriseId();
    window.addEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, syncEnterpriseId);
    return () => window.removeEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, syncEnterpriseId);
  }, []);

  React.useEffect(() => {
    let active = true;
    setLoading(true);

    const request = enterpriseId
      ? getEnterpriseSkillDisplayApi(enterpriseId)
      : getGlobalSkillDisplayApi();

    void request
      .then((response) => {
        if (!active) return;
        setDisplayContext(response);
      })
      .catch(() => {
        if (!active) return;
        setDisplayContext(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [enterpriseId]);

  return { enterpriseId, displayContext, loading };
}
