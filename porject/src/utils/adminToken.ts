import axios from 'axios';
import { clearAdminPermissions, setAdminPermissions } from './adminPermission';

const API_BASE = 'http://127.0.0.1:8000/api';

function applyPermFromResponse(data: Record<string, unknown>) {
  if (Array.isArray(data.permissions)) {
    setAdminPermissions(data.permissions as string[]);
  }
}

export async function fetchAdminSession(): Promise<boolean> {
  if (sessionStorage.getItem('admin_permissions')) return true;
  const t = localStorage.getItem('admin_access_token');
  if (!t) return false;
  try {
    const { data } = await axios.get(`${API_BASE}/manage_session`, {
      headers: { 'access-token': t },
    });
    if (data.current && Array.isArray(data.permissions)) {
      applyPermFromResponse(data);
      return true;
    }
  } catch {
    /* ignore */
  }
  return false;
}

export async function tryRefreshAdminTokens(): Promise<boolean> {
  const rt = localStorage.getItem('admin_refresh_token');
  if (!rt) return false;
  try {
    const { data } = await axios.post(`${API_BASE}/manage_admin_refresh`, {
      refresh_token: rt,
    });
    if (data.current && (data.access_token || data.token)) {
      const at = data.access_token || data.token;
      localStorage.setItem('admin_access_token', `Bearer ${at}`);
      if (data.refresh_token) localStorage.setItem('admin_refresh_token', data.refresh_token);
      applyPermFromResponse(data);
      return true;
    }
  } catch {
    /* ignore */
  }
  return false;
}

export function clearAdminSession() {
  localStorage.removeItem('admin_access_token');
  localStorage.removeItem('admin_refresh_token');
  clearAdminPermissions();
}
