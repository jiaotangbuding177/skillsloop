export const B2B_ENTERPRISE_KIND = 'b2b';
export const CONSUMER_ENTERPRISE_KIND = 'consumer';
export const EVOMIND_CONSUMER_ENTERPRISE_KIND = 'evomind_consumer';

export const ENTERPRISE_KINDS = [
  B2B_ENTERPRISE_KIND,
  CONSUMER_ENTERPRISE_KIND,
  EVOMIND_CONSUMER_ENTERPRISE_KIND,
] as const;

export type EnterpriseKind = (typeof ENTERPRISE_KINDS)[number];

export function isB2BEnterpriseKind(kind: string | null | undefined): kind is typeof B2B_ENTERPRISE_KIND {
  return kind === B2B_ENTERPRISE_KIND;
}

export function isConsumerEnterpriseKind(
  kind: string | null | undefined,
): kind is typeof CONSUMER_ENTERPRISE_KIND | typeof EVOMIND_CONSUMER_ENTERPRISE_KIND {
  return kind === CONSUMER_ENTERPRISE_KIND || kind === EVOMIND_CONSUMER_ENTERPRISE_KIND;
}

export function isDefaultQuotaAllowedKind(kind: string | null | undefined): kind is typeof B2B_ENTERPRISE_KIND {
  return isB2BEnterpriseKind(kind);
}

export const PURCHASE_MODE_CONTACT_ADMIN = 'contact_admin';
export const PURCHASE_MODE_ADMIN_PURCHASE = 'admin_purchase';
export const PURCHASE_MODE_SELF_PURCHASE = 'self_purchase';

export const PURCHASE_MODES = [
  PURCHASE_MODE_CONTACT_ADMIN,
  PURCHASE_MODE_ADMIN_PURCHASE,
  PURCHASE_MODE_SELF_PURCHASE,
] as const;

export type PurchaseMode = (typeof PURCHASE_MODES)[number];
