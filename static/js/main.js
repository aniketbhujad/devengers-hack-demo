/* ===================================================================
   LearnMate – Main JavaScript
   =================================================================== */

// ── Theme Management ──────────────────────────────────────────────
const ThemeManager = (() => {
  const KEY = 'lm-theme';
  let current = localStorage.getItem(KEY) || 'dark';

  function apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const icon = document.getElementById('themeIcon');
    if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    localStorage.setItem(KEY, theme);
    current = theme;
  }

  function toggle() { apply(current === 'dark' ? 'light' : 'dark'); }

  function init() { apply(current); }

  return { init, toggle, current: () => current };
})();


// ── Sidebar ───────────────────────────────────────────────────────
const Sidebar = (() => {
  function init() {
    const sidebar  = document.getElementById('sidebar');
    const overlay  = document.getElementById('sidebarOverlay');
    const toggleBtn = document.getElementById('sidebarToggle');
    if (!sidebar) return;

    function open()  { sidebar.classList.add('open'); overlay.classList.add('active'); }
    function close() { sidebar.classList.remove('open'); overlay.classList.remove('active'); }

    if (toggleBtn)  toggleBtn.addEventListener('click', () => sidebar.classList.contains('open') ? close() : open());
    if (overlay)    overlay.addEventListener('click', close);

    // Close on nav link click (mobile)
    sidebar.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => { if (window.innerWidth < 769) close(); });
    });
  }
  return { init };
})();


// ── Toast Notifications ───────────────────────────────────────────
const Toast = (() => {
  function show(message, type = 'info', duration = 3500) {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container-custom';
      document.body.appendChild(container);
    }

    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const toast = document.createElement('div');
    toast.className = `toast-custom ${type}`;
    toast.innerHTML = `
      <span style="font-size:1rem">${icons[type] || icons.info}</span>
      <div class="toast-body">${message}</div>
      <button class="toast-close" onclick="this.closest('.toast-custom').remove()">✕</button>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), duration);
  }
  return { show };
})();


// ── Markdown Renderer (lightweight) ──────────────────────────────
const MD = (() => {
  function render(text) {
    if (!text) return '';
    return text
      // Code blocks
      .replace(/```[\s\S]*?```/g, m => `<pre><code>${escHtml(m.slice(3,-3).replace(/^\w+\n/,''))}</code></pre>`)
      // Headers
      .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      // Bold / italic
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // HR
      .replace(/^---+$/gm, '<hr>')
      // Blockquote
      .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
      // Unordered lists
      .replace(/^[\*\-] (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>[\s\S]+?<\/li>)/g, '<ul>$1</ul>')
      // Ordered lists
      .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
      // Paragraphs (double newline)
      .replace(/\n\n/g, '</p><p>')
      // Single newlines
      .replace(/\n/g, '<br>');
  }

  function escHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  return { render };
})();


// ── Copy to clipboard ─────────────────────────────────────────────
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '✅ Copied!';
    setTimeout(() => { btn.innerHTML = orig; }, 2000);
    Toast.show('Copied to clipboard!', 'success', 2000);
  }).catch(() => Toast.show('Could not copy.', 'error'));
}


// ── Auto-resize textarea ──────────────────────────────────────────
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}


// ── Format timestamp ──────────────────────────────────────────────
function timeAgo(dateStr) {
  const d = new Date(dateStr);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)   return 'just now';
  if (mins < 60)  return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)   return `${hrs}h ago`;
  return `${Math.floor(hrs/24)}d ago`;
}


// ── Delete with confirmation ──────────────────────────────────────
async function deleteItem(url, onSuccess) {
  if (!confirm('Are you sure you want to delete this item?')) return;
  try {
    const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
    const data = await res.json();
    if (data.success) {
      Toast.show('Deleted successfully.', 'success');
      if (onSuccess) onSuccess();
    } else {
      Toast.show('Delete failed.', 'error');
    }
  } catch (e) {
    Toast.show('Network error.', 'error');
  }
}


// ── AI Stream-like typewriter effect ─────────────────────────────
function typewriterRender(container, text, delay = 8) {
  container.innerHTML = '';
  const rendered = MD.render(text);
  // Insert rendered HTML char-by-char simulation (faster: word-by-word)
  const words = text.split(' ');
  let i = 0;
  function next() {
    if (i >= words.length) {
      container.innerHTML = `<div class="ai-response">${MD.render(text)}</div>`;
      return;
    }
    i += Math.ceil(words.length / 60); // ~60 chunks
    const partial = words.slice(0, i).join(' ');
    container.innerHTML = `<div class="ai-response">${MD.render(partial)}</div>`;
    container.scrollTop = container.scrollHeight;
    setTimeout(next, delay);
  }
  next();
}


// ── Bootstrap flash messages auto-dismiss ────────────────────────
function initFlashMessages() {
  document.querySelectorAll('.alert-dismissible').forEach(el => {
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transition = 'opacity .5s';
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });
}


// ── Global init ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
  Sidebar.init();
  initFlashMessages();

  // Theme toggle button
  const themeBtn = document.getElementById('themeToggle');
  if (themeBtn) themeBtn.addEventListener('click', ThemeManager.toggle);
});
