'use client';

export const ACTIVE_ENTERPRISE_STORAGE_KEY = 'zclaw:active-enterprise-id';
export const ACTIVE_ENTERPRISE_DISPLAY_NAME_KEY = 'zclaw:active-enterprise-display-name';
export const ACTIVE_ENTERPRISE_CHANGED_EVENT = 'zclaw:active-enterprise-changed';
export const AGENT_DISPLAY_CHANGED_EVENT = 'zclaw:agent-display-changed';
export const SKILL_MARKET_CHANGED_EVENT = 'zclaw:skill-market-changed';
export const TOKEN_QUOTA_CHANGED_EVENT = 'zclaw:token-quota-changed';
export const ENTERPRISE_BRANDING_CHANGED_EVENT = 'zclaw:enterprise-branding-changed';
export const OPEN_BILLING_PURCHASE_EVENT = 'zclaw:open-billing-purchase';

export type BillingPurchaseTab = 'monthly' | 'storage' | 'token';

export function getActiveEnterpriseId() {
  if (typeof window === 'undefined') return '';
  return window.localStorage.getItem(ACTIVE_ENTERPRISE_STORAGE_KEY)?.trim() || '';
}

export function getActiveEnterpriseDisplayName() {
  if (typeof window === 'undefined') return '';
  return window.localStorage.getItem(ACTIVE_ENTERPRISE_DISPLAY_NAME_KEY)?.trim() || '';
}

export function setActiveEnterpriseDisplayName(name: string) {
  if (typeof window === 'undefined') return;
  const normalized = name.trim();
  if (normalized) {
    window.localStorage.setItem(ACTIVE_ENTERPRISE_DISPLAY_NAME_KEY, normalized);
  } else {
    window.localStorage.removeItem(ACTIVE_ENTERPRISE_DISPLAY_NAME_KEY);
  }
}

/** 仅主聊天页切换组织时需要清空会话并回到根路由 */
export function shouldResetChatWorkspaceOnEnterpriseChange(pathname: string) {
  return pathname === '/';
}

export function setActiveEnterpriseId(enterpriseId: string) {
  if (typeof window === 'undefined') return;
  const normalized = enterpriseId.trim();
  if (normalized) {
    window.localStorage.setItem(ACTIVE_ENTERPRISE_STORAGE_KEY, normalized);
  } else {
    window.localStorage.removeItem(ACTIVE_ENTERPRISE_STORAGE_KEY);
    window.localStorage.removeItem(ACTIVE_ENTERPRISE_DISPLAY_NAME_KEY);
  }
  window.dispatchEvent(new CustomEvent(ACTIVE_ENTERPRISE_CHANGED_EVENT, { detail: { enterpriseId: normalized } }));
}

export function emitAgentDisplayChanged() {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(AGENT_DISPLAY_CHANGED_EVENT));
}

export function emitSkillMarketChanged() {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(SKILL_MARKET_CHANGED_EVENT));
}

export function emitTokenQuotaChanged() {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(TOKEN_QUOTA_CHANGED_EVENT));
}

export function emitEnterpriseBrandingChanged(enterpriseId: string) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(
    new CustomEvent(ENTERPRISE_BRANDING_CHANGED_EVENT, {
      detail: { enterpriseId: enterpriseId.trim() },
    }),
  );
}

export function emitOpenBillingPurchase(tab?: BillingPurchaseTab) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(
    new CustomEvent(OPEN_BILLING_PURCHASE_EVENT, { detail: { tab: tab ?? 'monthly' } }),
  );
}

export function withActiveEnterpriseHeader(headersInit?: HeadersInit) {
  const headers = new Headers(headersInit || {});
  const enterpriseId = getActiveEnterpriseId();
  if (enterpriseId) {
    headers.set('x-enterprise-id', enterpriseId);
  } else {
    headers.delete('x-enterprise-id');
  }
  return headers;
}
