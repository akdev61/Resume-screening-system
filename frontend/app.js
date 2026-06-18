// ── API base ──────────────────────────────────────────────
const API = '/api';

function getToken() { return localStorage.getItem('token'); }
function setToken(t) { localStorage.setItem('token', t); }
function clearAuth() { localStorage.removeItem('token'); localStorage.removeItem('user'); }
function getUser() { try { return JSON.parse(localStorage.getItem('user') || 'null'); } catch { return null; } }
function setUser(u) { localStorage.setItem('user', JSON.stringify(u)); }

async function api(method, path, body, isForm = false) {
  const headers = {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!isForm) headers['Content-Type'] = 'application/json';

  const opts = { method, headers };
  if (body) opts.body = isForm ? body : JSON.stringify(body);

  const res = await fetch(API + path, opts);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { message: text }; }

  if (res.status === 401) {
    clearAuth();
    window.location.href = '/';
    return;
  }
  if (!res.ok) throw new Error(data.detail || data.message || 'Request failed');
  return data;
}

const http = {
  get: (p) => api('GET', p),
  post: (p, b) => api('POST', p, b),
  postForm: (p, b) => api('POST', p, b, true),
  put: (p, b) => api('PUT', p, b),
  delete: (p) => api('DELETE', p),
};

// ── Guard ─────────────────────────────────────────────────
function requireAuth() {
  if (!getToken()) { window.location.href = '/'; }
}

function requireGuest() {
  if (getToken()) { window.location.href = '/dashboard'; }
}

// ── Toast ─────────────────────────────────────────────────
let _toastTimer;
function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = `show ${type}`;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { el.className = ''; }, 3200);
}

// ── Sidebar user chip ──────────────────────────────────────
function renderUserChip() {
  const u = getUser();
  if (!u) return;
  const nameEl = document.getElementById('sidebar-user-name');
  const emailEl = document.getElementById('sidebar-user-email');
  const avatarEl = document.getElementById('sidebar-user-avatar');
  if (nameEl) nameEl.textContent = `${u.first_name} ${u.last_name}`;
  if (emailEl) emailEl.textContent = u.email;
  if (avatarEl) avatarEl.textContent = (u.first_name[0] + u.last_name[0]).toUpperCase();
}

// ── Logout ────────────────────────────────────────────────
function logout() {
  clearAuth();
  window.location.href = '/';
}

// ── Modal helpers ─────────────────────────────────────────
function openModal(id) {
  document.getElementById(id)?.classList.add('open');
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove('open');
}

// ── Date format ───────────────────────────────────────────
function fmtDate(iso) {
  if (!iso) return '—';
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(iso));
}

function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

// ── Initials avatar color ─────────────────────────────────
const _avatarColors = ['avatar-blue','avatar-green','avatar-amber','avatar-red'];
function avatarClass(name) {
  let h = 0;
  for (let c of name) h = (h * 31 + c.charCodeAt(0)) & 0xffffffff;
  return _avatarColors[Math.abs(h) % _avatarColors.length];
}

// ── Score helpers ─────────────────────────────────────────
function scoreColor(s) {
  if (s >= 60) return 'green';
  if (s >= 35) return 'amber';
  return 'red';
}
function barClass(s) {
  if (s >= 60) return 'bar-green';
  if (s >= 35) return 'bar-amber';
  return 'bar-red';
}
