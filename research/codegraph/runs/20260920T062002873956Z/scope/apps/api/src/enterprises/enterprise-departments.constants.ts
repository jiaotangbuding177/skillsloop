export const DEFAULT_ENTERPRISE_DEPARTMENTS = [
  '管理',
  '研发',
  '销售',
  '财务',
  '交付',
  'HR',
] as const;

export function buildDefaultEnterpriseDepartmentCreates() {
  return DEFAULT_ENTERPRISE_DEPARTMENTS.map((name, sortOrder) => ({
    name,
    sortOrder,
  }));
}
