"""core/tenant.py — multi-tenant helpers"""
def filter_tenant(records, tenant_id: str, is_admin: bool = False):
    if is_admin:
        return records
    return [r for r in records if r.get("tenant_id", "default") == tenant_id]
