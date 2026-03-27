const KEY = 'admin_permissions';

/** 任持有一项即可进入后台首页（仪表盘） */
export const MANAGE_HOME_ANY = [
  'admin.dashboard',
  'admin.commodity',
  'admin.commodity_apply',
  'admin.user.merchant',
  'admin.user.mall',
  'admin.user.platform',
  'admin.user.role',
  'admin.audit_seller',
  'admin.business',
  'admin.system_settings',
] as const;

export function setAdminPermissions(perms: string[]) {
  sessionStorage.setItem(KEY, JSON.stringify(perms));
}

export function getAdminPermissions(): string[] {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return [];
    const p = JSON.parse(raw) as string[];
    return Array.isArray(p) ? p : [];
  } catch {
    return [];
  }
}

export function hasAdminPermission(code: string): boolean {
  const p = getAdminPermissions();
  if (p.includes('*')) return true;
  return p.includes(code);
}

export function hasAnyAdminPermission(codes: string[]): boolean {
  const p = getAdminPermissions();
  if (p.includes('*')) return true;
  return codes.some((c) => p.includes(c));
}

export function clearAdminPermissions() {
  sessionStorage.removeItem(KEY);
}

export function canEnterManageHome(): boolean {
  return hasAnyAdminPermission([...MANAGE_HOME_ANY]);
}
