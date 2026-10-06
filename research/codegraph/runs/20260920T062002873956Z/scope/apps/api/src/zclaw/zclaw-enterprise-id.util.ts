export function readEnterpriseId(req: {
  headers?: Record<string, unknown>;
  query?: Record<string, unknown>;
  body?: Record<string, unknown>;
}) {
  const fromHeader = req.headers?.['x-enterprise-id'];
  const fromQuery = req.query?.enterpriseId;
  const fromBody = req.body?.enterpriseId;
  const value =
    typeof fromHeader === 'string'
      ? fromHeader
      : typeof fromQuery === 'string'
        ? fromQuery
        : typeof fromBody === 'string'
          ? fromBody
          : '';
  return value.trim() || null;
}
