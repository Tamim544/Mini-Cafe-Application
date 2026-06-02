/* ═══════════════════════════════════════════════════════════
   app.js  —  Auth state, navbar, toast system
   ═══════════════════════════════════════════════════════════ */

// ── Auth helpers ──────────────────────────────────────────────
const Auth = {
  get token()   { return localStorage.getItem('cafe_token'); },
  get refresh() { return localStorage.getItem('cafe_refresh'); },
  get user()    { const u = localStorage.getItem('cafe_user'); return u ? JSON.parse(u) : null; },

  save(data) {
    localStorage.setItem('cafe_token',   data.access_token);
    localStorage.setItem('cafe_refresh', data.refresh_token);
    localStorage.setItem('cafe_user',    JSON.stringify(data.user));
  },
  clear() {
    ['cafe_token','cafe_refresh','cafe_user'].forEach(k => localStorage.removeItem(k));
  },
  isLoggedIn() { return !!this.token; },
  role()       { return this.user?.role || null; },
};

// ── API fetch wrapper ─────────────────────────────────────────
async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (Auth.token) headers['Authorization'] = `Bearer ${Auth.token}`;

  const res = await fetch(path, { ...opts, headers });

  if (res.status === 401 && Auth.refresh) {
    // Try to refresh token
    const rRes = await fetch('/auth/refresh', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${Auth.refresh}` },
    });
    if (rRes.ok) {
      const rData = await rRes.json();
      localStorage.setItem('cafe_token', rData.access_token);
      headers['Authorization'] = `Bearer ${rData.access_token}`;
      return fetch(path, { ...opts, headers });
    } else {
      Auth.clear();
      window.location.href = '/login';
      return;
    }
  }
  return res;
}

// ── Toast notifications ───────────────────────────────────────
function showToast(message, type = 'info') {
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span class="toast-icon">${icons[type]}</span><span class="toast-msg">${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 5200);
}
window.showToast = showToast;

// ── Navbar builder ────────────────────────────────────────────
const NAV_LINKS = {
  customer: [
    { href: '/', label: '🍽️ Menu' },
  ],
  kitchen: [
    { href: '/', label: '🍽️ Menu' },
    { href: '/kitchen', label: '👨‍🍳 Kitchen' },
  ],
  waiter: [
    { href: '/', label: '🍽️ Menu' },
    { href: '/waiter', label: '🛎️ Waiter' },
  ],
  admin: [
    { href: '/', label: '🍽️ Menu' },
    { href: '/admin', label: '📊 Dashboard' },
    { href: '/admin/orders', label: '📋 Orders' },
    { href: '/admin/menu', label: '🗂️ Menu' },
    { href: '/admin/staff', label: '👥 Staff' },
    { href: '/kitchen', label: '👨‍🍳 Kitchen' },
    { href: '/waiter', label: '🛎️ Waiter' },
  ],
};

function buildNavbar() {
  const navLinks = document.getElementById('nav-links');
  const navUser  = document.getElementById('nav-user');
  if (!navLinks) return;

  const role = Auth.isLoggedIn() ? Auth.role() : 'customer';
  const links = NAV_LINKS[role] || NAV_LINKS.customer;
  const current = window.location.pathname;

  navLinks.innerHTML = links.map(l =>
    `<a href="${l.href}" class="nav-link ${current === l.href || (l.href !== '/' && current.startsWith(l.href)) ? 'active' : ''}">${l.label}</a>`
  ).join('');

  // Always add visible logout link in nav for staff
  if (Auth.isLoggedIn()) {
    navLinks.innerHTML += `<a href="#" class="nav-link" onclick="event.preventDefault();logout()" style="color:var(--danger);margin-left:auto;">🚪 Logout</a>`;
  }

  if (Auth.isLoggedIn() && navUser) {
    navUser.style.display = 'flex';
    navUser.style.alignItems = 'center';
    navUser.style.gap = '0.6rem';
    const roleColors = { admin:'var(--amber)', kitchen:'var(--teal)', waiter:'var(--info)' };
    const color = roleColors[role] || 'var(--text-2)';
    navUser.innerHTML = `
      <span style="padding:0.25rem 0.7rem;border-radius:99px;border:1px solid ${color}33;color:${color};font-size:0.75rem;font-weight:700;text-transform:uppercase">
        ${Auth.user()?.username || role}
      </span>
      <button onclick="logout()" class="btn btn-secondary btn-sm">Logout</button>
    `;

    // Show bell for staff
    if (['admin','kitchen'].includes(role)) {
      document.getElementById('notif-bell').style.display = 'flex';
    }

    // Hide "Staff Login" link in hero when already logged in
    const staffLink = document.getElementById('staff-login-link');
    if (staffLink) staffLink.style.display = 'none';
  }
}

// ── Logout ────────────────────────────────────────────────────
function logout() {
  Auth.clear();
  window.location.href = '/';
}
window.logout = logout;

// ── Guard: redirect staff pages to login if not authenticated ─
function requireRole(...roles) {
  if (!Auth.isLoggedIn()) { window.location.href = '/login'; return false; }
  if (roles.length && !roles.includes(Auth.role())) {
    showToast('Access denied.', 'error');
    setTimeout(() => window.location.href = '/', 1200);
    return false;
  }
  return true;
}
window.requireRole = requireRole;

// ── Relative time helper ──────────────────────────────────────
function timeAgo(isoStr) {
  if (!isoStr) return '';
  const diff = Date.now() - new Date(isoStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)  return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h/24)}d ago`;
}
window.timeAgo = timeAgo;

// ── Status badge HTML ──────────────────────────────────────────
function statusBadge(status) {
  const icons = { placed:'🕐', accepted:'✔️', preparing:'🔥', ready:'🛎️', delivered:'✅', cancelled:'✖️' };
  return `<span class="status-badge status-${status}">${icons[status]||''} ${status}</span>`;
}
window.statusBadge = statusBadge;

// ── Modal helpers ─────────────────────────────────────────────
function openModal(id)  { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }
window.openModal = openModal;
window.closeModal = closeModal;

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', buildNavbar);
