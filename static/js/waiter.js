/* ═══════════════════════════════════════════════════════════
   waiter.js — Premium v2
   ═══════════════════════════════════════════════════════════ */
requireRole('waiter', 'admin');

let waiterOrders = [];

function renderOrders() {
  const grid = document.getElementById('orders-grid');
  document.getElementById('w-stat-ready').textContent = waiterOrders.length;

  if (!waiterOrders.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <div class="empty-state-icon">✅</div>
      <div class="empty-state-text">No orders ready for delivery</div>
      <div style="font-size:0.75rem;color:var(--text-3);margin-top:0.2rem;">Orders will appear here once the kitchen marks them ready</div>
    </div>`;
    return;
  }
  grid.innerHTML = waiterOrders.map((o, i) => {
    const delay = Math.min(i * 0.06, 0.4);
    return `
    <div class="order-card" id="card-${o.order_ref}" data-status="${o.status}" style="animation-delay:${delay}s">
      <div class="order-card-header">
        <span class="order-ref">${o.order_ref}</span>
        ${statusBadge(o.status)}
      </div>
      <div class="order-customer">
        👤 ${o.customer_name}
        ${o.table_number
          ? `<span style="margin-left:0.5rem;padding:0.22rem 0.65rem;background:rgba(20,184,166,0.12);border:1px solid rgba(20,184,166,0.22);border-radius:99px;font-size:0.72rem;font-weight:800;color:var(--teal);">📍 Table ${o.table_number}</span>`
          : '<span style="margin-left:0.4rem;padding:0.22rem 0.65rem;background:rgba(167,139,250,0.1);border:1px solid rgba(167,139,250,0.2);border-radius:99px;font-size:0.72rem;font-weight:700;color:var(--purple);">📦 Takeaway</span>'}
      </div>
      <ul class="order-items-list">
        ${o.items.map(it => `<li>${it.item_name} <strong style="color:var(--text-1);">×${it.quantity}</strong></li>`).join('')}
      </ul>
      <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:var(--text-3);">
        <span>Ready ${timeAgo(o.ready_at || o.placed_at)}</span>
        <strong style="color:var(--amber);font-family:'Outfit',sans-serif;font-size:0.9rem;">$${o.total.toFixed(2)}</strong>
      </div>
      <div class="order-card-actions">
        <button class="btn btn-success" onclick="deliver('${o.order_ref}')" style="flex:1;">✅ Mark Delivered</button>
      </div>
    </div>`;
  }).join('');
}

async function deliver(ref) {
  try {
    const res = await api(`/api/orders/${ref}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status: 'delivered' }),
    });
    if (res.ok) {
      showToast(`Order ${ref} delivered! 🎉`, 'success');
      waiterOrders = waiterOrders.filter(o => o.order_ref !== ref);
      renderOrders();
    } else {
      const d = await res.json();
      showToast(d.error || 'Failed', 'error');
    }
  } catch { showToast('Network error', 'error'); }
}
window.deliver = deliver;

async function loadOrders() {
  try {
    const res = await api('/api/orders');
    if (!res.ok) return;
    waiterOrders = await res.json();
    renderOrders();
  } catch { showToast('Failed to load', 'error'); }
}
window.loadOrders = loadOrders;

// Real-time
const socket = getSocket();
socket.on('order_status_update', (order) => {
  if (order.status === 'ready') {
    if (!waiterOrders.find(o => o.order_ref === order.order_ref)) {
      waiterOrders.unshift(order);
      showToast(`🛎️ Order ${order.order_ref} is ready!`, 'success');
      setTimeout(() => {
        const card = document.getElementById(`card-${order.order_ref}`);
        if (card) card.classList.add('new-order');
      }, 50);
    }
  } else {
    waiterOrders = waiterOrders.filter(o => o.order_ref !== order.order_ref);
  }
  renderOrders();
});

document.addEventListener('DOMContentLoaded', loadOrders);
