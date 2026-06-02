/* ═══════════════════════════════════════════════════════════
   socket.js  —  Socket.IO client setup
   ═══════════════════════════════════════════════════════════ */

let _socket = null;

function getSocket() {
  if (_socket) return _socket;

  const opts = { transports: ['websocket', 'polling'] };
  if (Auth.isLoggedIn()) {
    opts.auth = { token: Auth.token };
  }

  _socket = io(opts);

  _socket.on('connect', () => {
    console.log('🔌 Socket connected:', _socket.id);
  });
  _socket.on('disconnect', () => {
    console.log('🔌 Socket disconnected');
  });
  _socket.on('connect_error', (err) => {
    console.warn('Socket error:', err.message);
  });

  return _socket;
}

// Expose globally so page scripts can subscribe
window.getSocket = getSocket;
