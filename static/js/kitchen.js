/* ═══════════════════════════════════════════════════════════
   kitchen.js — Premium v2
   ═══════════════════════════════════════════════════════════ */
requireRole('kitchen', 'admin');

let kitchenOrders = [];
let currentFilter = 'all';

function setFilter(f, btn) {
  currentFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderOrders();
}
window.setFilter = setFilter;

function updateStats() {
  const placed = kitchenOrders.filter(o => o.status === 'placed').length;
  const progress = kitchenOrders.filter(o => ['accepted','preparing'].includes(o.status)).length;
  document.getElementById('k-stat-new').textContent = placed;
  document.getElementById('k-stat-progress').textContent = progress;
}

function renderOrders() {
  const grid = document.getElementById('orders-grid');
  let list = kitchenOrders;
  if (currentFilter !== 'all') list = list.filter(o => o.status === currentFilter);

  updateStats();

  if (!list.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <div class="empty-state-icon">✅</div>
      <div class="empty-state-text">No active orders</div>
      <div style="font-size:0.75rem;color:var(--text-3);margin-top:0.2rem;">New orders will appear here in real-time</div>
    </div>`;
    return;
  }
  grid.innerHTML = list.map((o, i) => orderCardHTML(o, i)).join('');
}

function orderCardHTML(o, idx) {
  const actions = {
    placed:    [{ label:'✔ Accept',     cls:'btn-success', next:'accepted'  }, { label:'✖ Decline', cls:'btn-danger', next:'cancelled' }],
    accepted:  [{ label:'🔥 Start Prep', cls:'btn-teal',    next:'preparing' }],
    preparing: [{ label:'🛎 Mark Ready', cls:'btn-primary', next:'ready'     }],
  };
  const btns = (actions[o.status] || []).map(a =>
    `<button class="btn ${a.cls} btn-sm" onclick="updateStatus('${o.order_ref}','${a.next}')">${a.label}</button>`
  ).join('');

  const elapsed = timeAgo(o.placed_at);
  const delay = Math.min(idx * 0.05, 0.4);

  return `<div class="order-card" id="card-${o.order_ref}" data-status="${o.status}" style="animation-delay:${delay}s">
    <div class="order-card-header">
      <span class="order-ref">${o.order_ref}</span>
      ${statusBadge(o.status)}
    </div>
    <div class="order-customer">
      👤 ${o.customer_name}
      ${o.table_number
        ? `<span style="margin-left:0.5rem;padding:0.18rem 0.55rem;background:rgba(20,184,166,0.1);border:1px solid rgba(20,184,166,0.2);border-radius:99px;font-size:0.7rem;font-weight:700;color:var(--teal);">Table ${o.table_number}</span>`
        : '<span style="margin-left:0.4rem;font-size:0.72rem;color:var(--text-3);">Takeaway</span>'}
    </div>
    <ul class="order-items-list">
      ${o.items.map(i => `<li>${i.item_name} <strong style="color:var(--text-1);">×${i.quantity}</strong></li>`).join('')}
    </ul>
    ${o.notes ? `<div style="font-size:0.76rem;color:var(--text-2);background:rgba(255,255,255,0.025);padding:0.45rem 0.65rem;border-radius:var(--radius-sm);border:1px solid var(--glass-border);">📝 ${o.notes}</div>` : ''}
    <div style="display:flex;justify-content:space-between;align-items:center;font-size:0.75rem;color:var(--text-3);">
      <span>⏱ ${elapsed}</span>
      <strong style="color:var(--amber);font-family:'Outfit',sans-serif;font-size:0.9rem;">$${o.total.toFixed(2)}</strong>
    </div>
    <div class="order-card-actions">${btns}</div>
  </div>`;
}

async function updateStatus(ref, newStatus) {
  try {
    const res = await api(`/api/orders/${ref}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus }),
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`${ref} → ${newStatus}`, 'success');
      const idx = kitchenOrders.findIndex(o => o.order_ref === ref);
      if (idx >= 0) {
        if (['ready','delivered','cancelled'].includes(newStatus)) {
          kitchenOrders.splice(idx, 1);
        } else {
          kitchenOrders[idx] = data;
        }
      }
      renderOrders();
    } else {
      showToast(data.error || 'Update failed', 'error');
    }
  } catch { showToast('Network error', 'error'); }
}
window.updateStatus = updateStatus;

async function loadOrders() {
  try {
    const res = await api('/api/orders');
    if (!res.ok) { if (res.status === 403) { requireRole('kitchen','admin'); return; } }
    kitchenOrders = await res.json();
    renderOrders();
  } catch { showToast('Failed to load orders', 'error'); }
}
window.loadOrders = loadOrders;

// Real-time
const socket = getSocket();
socket.on('new_order', (order) => {
  kitchenOrders.unshift(order);
  renderOrders();
  showToast(`🆕 New order ${order.order_ref} from ${order.customer_name}`, 'info');
  setTimeout(() => {
    const card = document.getElementById(`card-${order.order_ref}`);
    if (card) card.classList.add('new-order');
  }, 50);

  const cnt = document.getElementById('notif-count');
  if (cnt) {
    const n = (parseInt(cnt.textContent) || 0) + 1;
    cnt.textContent = n;
    cnt.style.display = 'flex';
  }
});

socket.on('order_status_update', (order) => {
  const idx = kitchenOrders.findIndex(o => o.order_ref === order.order_ref);
  if (idx >= 0) {
    if (['ready','delivered','cancelled'].includes(order.status)) {
      kitchenOrders.splice(idx, 1);
    } else {
      kitchenOrders[idx] = order;
    }
    renderOrders();
  }
});

document.addEventListener('DOMContentLoaded', loadOrders);
