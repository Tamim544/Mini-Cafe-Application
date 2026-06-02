/* ═══════════════════════════════════════════════════════════
   menu.js  —  Customer menu: load items, cart, ordering
   Premium v2 — stagger animations, animated cart, better UX
   ═══════════════════════════════════════════════════════════ */

const ITEM_EMOJI = {
  'coffee':'☕','espresso':'☕','cappuccino':'☕','latte':'☕','americano':'☕','mocha':'☕',
  'tea':'🍵','chai':'🍵','matcha':'🍵',
  'iced':'🧋','cold brew':'🧋','frappe':'🧋',
  'lemonade':'🍋','juice':'🧃','smoothie':'🥤','water':'💧','soda':'🥤',
  'sandwich':'🥪','panini':'🥪','wrap':'🌯',
  'pizza':'🍕','burger':'🍔','pasta':'🍝',
  'cake':'🎂','pastry':'🥐','muffin':'🧁','cookie':'🍪','brownie':'🍫','croissant':'🥐',
  'salad':'🥗','soup':'🍲',
  'waffle':'🧇','pancake':'🥞',
  'bagel':'🥯','toast':'🍞','bread':'🍞',
};
function itemEmoji(name) {
  const lower = name.toLowerCase();
  for (const [key, emoji] of Object.entries(ITEM_EMOJI)) {
    if (lower.includes(key)) return emoji;
  }
  return '🍴';
}

let allCategories = [];
let cart = {};         // { itemId: { item, qty } }
let activeCategory = 'all';
let lastOrderRef = null;

// ── Load menu ─────────────────────────────────────────────────
async function loadMenu() {
  try {
    const res  = await fetch('/api/menu');
    const data = await res.json();
    allCategories = data;
    renderCategoryTabs();
    renderMenu();
    
    // Pre-fill track bar with last order
    const savedRef = localStorage.getItem('cafe_last_order');
    if (savedRef) {
      lastOrderRef = savedRef;
      const trackInput = document.getElementById('track-input');
      if (trackInput) trackInput.value = savedRef;
    }
  } catch {
    document.getElementById('menu-grid').innerHTML =
      '<div class="empty-state" style="grid-column:1/-1"><div class="empty-state-icon">⚠️</div><div class="empty-state-text">Could not load menu. Please refresh.</div></div>';
  }
}

function renderCategoryTabs() {
  const tabs = document.getElementById('cat-tabs');
  const allHTML = `<button class="cat-tab ${activeCategory==='all'?'active':''}" onclick="filterCat('all')">✨ All</button>`;
  const catHTML = allCategories.map(c =>
    `<button class="cat-tab ${activeCategory===c.category?'active':''}" onclick="filterCat('${c.category.replace(/'/g, "\\'")}')">${c.category}</button>`
  ).join('');
  tabs.innerHTML = allHTML + catHTML;
}

function filterCat(cat) {
  activeCategory = cat;
  renderCategoryTabs();
  renderMenu();
}

function renderMenu() {
  const grid = document.getElementById('menu-grid');
  const cats = activeCategory === 'all' ? allCategories : allCategories.filter(c => c.category === activeCategory);

  if (!cats.length || !cats.some(c => c.items.length)) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1"><div class="empty-state-icon">🍽️</div><div class="empty-state-text">No items available</div></div>';
    return;
  }

  let html = '';
  let idx = 0;
  for (const cat of cats) {
    if (activeCategory === 'all') {
      html += `<div style="grid-column:1/-1;padding:0.75rem 0 0.35rem;display:flex;align-items:center;gap:0.5rem;animation:fadeUp 0.3s ease ${idx*0.04}s both;">
        <span style="font-size:0.72rem;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:0.09em;">${cat.category}</span>
        <span style="flex:1;height:1px;background:var(--glass-border);"></span>
        <span style="font-size:0.68rem;color:var(--text-3);font-weight:500;">${cat.items.length} items</span>
      </div>`;
      idx++;
    }
    for (const item of cat.items) {
      const inCart = cart[item.id]?.qty || 0;
      const delay = idx * 0.04;
      html += `
        <div class="item-card ${inCart > 0 ? 'selected' : ''}" data-id="${item.id}" style="animation-delay:${delay}s; cursor:pointer;" onclick="openItemModal('${item.id}')">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            ${item.image_url 
              ? `<div style="width: 50px; height: 50px; border-radius: var(--radius); overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                   <img src="${item.image_url}" alt="${item.name}" style="width: 100%; height: 100%; object-fit: cover;" />
                 </div>`
              : `<div class="item-emoji">${itemEmoji(item.name)}</div>`
            }
            ${inCart > 0 ? `<span style="background:var(--amber);color:#000;font-size:0.65rem;font-weight:800;min-width:20px;height:20px;border-radius:99px;display:flex;align-items:center;justify-content:center;padding:0 5px;">${inCart}</span>` : ''}
          </div>
          <div class="item-name">${item.name}</div>
          <div class="item-desc">${item.description || ''}</div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-top:auto;padding-top:0.4rem;">
            <div class="item-price">$${(item.price || 0).toFixed(2)}</div>
            <div class="item-add-icon" style="color:var(--amber);font-size:1.2rem;">+</div>
          </div>
        </div>`;
      idx++;
    }
  }
  grid.innerHTML = html;
}

// ── Item Modal Logic ──────────────────────────────────────────
let currentModalItem = null;
let currentModalQty = 1;

function openItemModal(id) {
  const strId = String(id);
  for (const cat of allCategories) {
    const item = cat.items.find(i => String(i.id) === strId);
    if (item) {
      currentModalItem = item;
      currentModalQty = 1;
      renderItemModal();
      document.getElementById('item-modal').classList.add('open');
      return;
    }
  }
}

function closeItemModal() {
  document.getElementById('item-modal').classList.remove('open');
  currentModalItem = null;
}

function changeModalQty(delta) {
  currentModalQty = Math.max(1, currentModalQty + delta);
  renderItemModal();
}

function addToCartFromModal() {
  if (!currentModalItem) return;
  const strId = String(currentModalItem.id);
  
  if (!cart[strId]) {
    cart[strId] = { 
      id: currentModalItem.id, 
      name: currentModalItem.name, 
      price: currentModalItem.price || 0, 
      qty: 0 
    };
  }
  
  cart[strId].qty += currentModalQty;
  closeItemModal();
  renderCartUI();
  renderMenu();
}

function renderItemModal() {
  if (!currentModalItem) return;
  const item = currentModalItem;
  const body = document.getElementById('item-modal-body');
  
  const total = (item.price * currentModalQty).toFixed(2);
  
  let imageHTML = `<div class="item-emoji" style="font-size:4rem;margin-bottom:1rem;">${itemEmoji(item.name)}</div>`;
  if (item.image_url) {
    imageHTML = `<div style="width:120px;height:120px;margin:0 auto 1rem;border-radius:50%;overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,0.3);border:2px solid var(--glass-border);">
                   <img src="${item.image_url}" alt="${item.name}" style="width:100%;height:100%;object-fit:cover;" />
                 </div>`;
  }

  body.innerHTML = `
    ${imageHTML}
    <h3 style="font-size:1.5rem;font-weight:800;margin-bottom:0.5rem;color:var(--text-1);">${item.name}</h3>
    <p style="font-size:0.9rem;color:var(--text-3);margin-bottom:1.5rem;line-height:1.5;">${item.description || ''}</p>
    
    <div style="display:flex;align-items:center;justify-content:center;gap:1rem;margin-bottom:2rem;">
      <button class="qty-btn" style="width:40px;height:40px;font-size:1.2rem;" onclick="changeModalQty(-1)">−</button>
      <span style="font-size:1.5rem;font-weight:800;font-family:'Outfit',sans-serif;width:40px;">${currentModalQty}</span>
      <button class="qty-btn" style="width:40px;height:40px;font-size:1.2rem;border-color:var(--amber);color:var(--amber);background:var(--amber-glow);" onclick="changeModalQty(1)">+</button>
    </div>
    
    <button class="btn btn-primary btn-full" style="padding:1rem;font-size:1.1rem;" onclick="addToCartFromModal()">
      Add to Cart — $${total}
    </button>
  `;
}

// ── Cart logic ────────────────────────────────────────────────
function changeQty(id, delta, e) {
  try {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    const strId = String(id);
    if (!cart[strId]) {
      let found = null;
      for (const cat of allCategories) {
        found = cat.items.find(i => String(i.id) === strId);
        if (found) break;
      }
      if (found) {
        cart[strId] = { id: found.id, name: found.name, price: found.price || 0, qty: 0 };
      }
    }
    
    if (!cart[strId]) {
      console.warn("Item not found:", strId);
      return;
    }
    
    cart[strId].qty = Math.max(0, cart[strId].qty + delta);
    if (cart[strId].qty === 0) {
      delete cart[strId];
    }
    
    renderCartUI();
    renderMenu();
  } catch (err) {
    alert("Error adding item: " + err.message);
    console.error(err);
  }
}

function clearCart() {
  cart = {};
  renderCartUI();
  renderMenu();
}
function resetCart() {
  cart = {};
  renderCartUI();
  renderMenu();
}

function renderCartUI() {
  try {
    const container = document.getElementById('cart-items');
    const footer    = document.getElementById('cart-footer');
    const totalVal  = document.getElementById('cart-total-val');
    const countEl   = document.getElementById('cart-count');
    const clearBtn  = document.getElementById('clear-cart-btn');
    
    if (!container || !footer || !totalVal || !countEl || !clearBtn) {
      console.error("Missing DOM elements for cart UI");
      return;
    }

    const items     = Object.values(cart);
    const totalQty  = items.reduce((s,i) => s + i.qty, 0);

    if (items.length === 0) {
      container.innerHTML = `<div class="empty-state" style="padding:2rem 1rem;">
        <div class="empty-state-icon" style="font-size:2.2rem;">🛒</div>
        <div class="empty-state-text" style="font-size:0.8rem;">Your cart is empty</div>
        <div style="font-size:0.72rem;color:var(--text-3);margin-top:0.2rem;">Add items from the menu</div>
      </div>`;
      footer.classList.remove('visible');
      countEl.classList.remove('visible');
      clearBtn.style.display = 'none';
      return;
    }

    let total = 0;
    container.innerHTML = items.map((i, idx) => {
      const sub = (i.price || 0) * (i.qty || 0); 
      total += sub;
      return `<div class="cart-item" style="animation-delay:${idx*0.04}s">
        <span class="cart-item-name">${i.name}</span>
        <span class="cart-item-qty">×${i.qty}</span>
        <span class="cart-item-price">$${sub.toFixed(2)}</span>
        <button class="cart-remove-btn" data-id="${i.id}" data-delta="-1" title="Remove one">−</button>
      </div>`;
    }).join('');

    totalVal.textContent = `$${total.toFixed(2)}`;
    footer.classList.add('visible');
    countEl.textContent = totalQty;
    countEl.classList.add('visible');
    clearBtn.style.display = 'block';
  } catch (err) {
    alert("Error rendering cart: " + err.message);
    console.error(err);
  }
}

// ── Checkout ──────────────────────────────────────────────────
function openCheckout() {
  const items = Object.values(cart);
  if (!items.length) return;

  let total = 0;
  const summary = document.getElementById('order-summary');
  summary.innerHTML = items.map(i => {
    const sub = i.price * i.qty; total += sub;
    return `<div style="display:flex;justify-content:space-between;padding:0.28rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
      <span style="color:var(--text-2)">${i.name} <span style="color:var(--text-3);font-weight:600;">×${i.qty}</span></span>
      <strong style="color:var(--text-1);">$${sub.toFixed(2)}</strong>
    </div>`;
  }).join('') + `<div style="display:flex;justify-content:space-between;padding-top:0.65rem;margin-top:0.25rem;border-top:1px solid var(--glass-border);font-weight:800;font-size:1.05rem;">
    <span>Total</span><span style="color:var(--amber);font-family:'Outfit',sans-serif;">$${total.toFixed(2)}</span>
  </div>`;

  openModal('checkout-modal');
}

async function submitOrder() {
  const name = document.getElementById('cust-name').value.trim();
  if (!name) { showToast('Please enter your name.', 'error'); return; }

  const items = Object.values(cart).map(i => ({ id: i.id, quantity: i.qty }));
  const btn = document.getElementById('submit-order-btn');
  btn.disabled = true;
  btn.textContent = 'Placing order…';

  try {
    const res = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_name: name,
        table_number:  document.getElementById('cust-table').value.trim(),
        notes:         document.getElementById('cust-notes').value.trim(),
        items,
      }),
    });
    const data = await res.json();
    if (res.ok) {
      lastOrderRef = data.order_ref;
      localStorage.setItem('cafe_last_order', data.order_ref);
      closeModal('checkout-modal');
      showSuccess(data);
      cart = {};
      renderCartUI();
      renderMenu();
    } else {
      showToast(data.error || 'Order failed.', 'error');
    }
  } catch {
    showToast('Network error. Try again.', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Confirm & Place Order';
  }
}

function showSuccess(order) {
  document.getElementById('success-ref').textContent = order.order_ref;
  document.getElementById('success-total').textContent = `Total: $${order.total.toFixed(2)}`;
  document.getElementById('receipt-link').href = `/api/orders/${order.order_ref}/receipt`;

  const qrContainer = document.getElementById('qr-container');
  if (order.qr_code_path) {
    qrContainer.innerHTML = `
      <img src="${order.qr_code_path}" alt="Order QR code"
           style="width:130px;height:130px;border-radius:var(--radius);border:2px solid rgba(245,158,11,0.3);box-shadow:0 8px 24px rgba(0,0,0,0.3);" />
      <p style="font-size:0.72rem;color:var(--text-3);margin-top:0.5rem;">Scan to track your order</p>`;
  } else {
    qrContainer.innerHTML = '';
  }

  openModal('success-modal');
}

function trackOrder() {
  if (lastOrderRef) window.location.href = `/track/${lastOrderRef}`;
}

function goTrackOrder() {
  const input = document.getElementById('track-input');
  const ref = (input ? input.value : '').trim().toUpperCase();
  if (!ref) {
    showToast('Please enter your Order ID.', 'error');
    return;
  }
  window.location.href = `/track/${ref}`;
}

// Expose for template onclick
window.filterCat          = filterCat;
window.changeQty          = changeQty;
window.clearCart          = clearCart;
window.resetCart          = resetCart;
window.openCheckout       = openCheckout;
window.submitOrder        = submitOrder;
window.trackOrder         = trackOrder;
window.goTrackOrder       = goTrackOrder;
window.openItemModal      = openItemModal;
window.closeItemModal     = closeItemModal;
window.changeModalQty     = changeModalQty;
window.addToCartFromModal = addToCartFromModal;

// Event Delegation for all quantity buttons to completely bypass inline onclick parsing bugs
document.addEventListener('click', function(e) {
  const btn = e.target.closest('.qty-btn, .cart-remove-btn');
  if (!btn) return;
  
  e.preventDefault();
  e.stopPropagation();
  
  const id = btn.getAttribute('data-id');
  const delta = parseInt(btn.getAttribute('data-delta'), 10);
  
  if (id && !isNaN(delta)) {
    changeQty(id, delta, e);
  }
});

document.addEventListener('DOMContentLoaded', loadMenu);
