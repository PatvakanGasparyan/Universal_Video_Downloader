/**
 * API client for Universal Video Downloader backend.
 */

/**
 * Build a rich Error from a backend response body. Supports the structured
 * envelope { success, error, message, solution } and FastAPI's { detail }.
 */
function buildApiError(body, fallback = 'Request failed') {
  if (body && typeof body === 'object' && (body.error || body.solution) && body.message) {
    const err = new Error(body.message);
    err.code = body.error || '';
    err.solution = body.solution || '';
    return err;
  }
  const err = new Error(formatApiError(body && body.detail, fallback));
  err.code = '';
  err.solution = '';
  return err;
}

function formatApiError(detail, fallback = 'Request failed') {
  if (detail == null || detail === '') return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const message = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          const loc = Array.isArray(item.loc)
            ? item.loc.filter((part) => part !== 'body').join('.')
            : '';
          const msg = item.msg || item.message || '';
          return loc ? `${loc}: ${msg}` : msg;
        }
        return String(item);
      })
      .filter(Boolean)
      .join('; ');
    return message || fallback;
  }
  if (typeof detail === 'object') {
    return detail.msg || detail.message || fallback;
  }
  return String(detail);
}

const API = {
  base: '',

  async request(path, options = {}) {
    const res = await fetch(`${this.base}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw buildApiError(body, res.statusText || 'Request failed');
    }
    return res.json();
  },

  getInfo(url) {
    return this.request('/api/info', { method: 'POST', body: JSON.stringify({ url }) });
  },

  startDownload(payload) {
    return this.request('/api/download', { method: 'POST', body: JSON.stringify(payload) });
  },

  getStatus(id) {
    return this.request(`/api/status/${id}`);
  },

  pauseDownload(id) {
    return this.request(`/api/download/${id}/pause`, { method: 'POST' });
  },

  resumeDownload(id) {
    return this.request(`/api/download/${id}/resume`, { method: 'POST' });
  },

  cancelDownload(id) {
    return this.request(`/api/download/${id}/cancel`, { method: 'POST' });
  },

  getHistory(query = '', favoriteOnly = false) {
    const params = new URLSearchParams({ query, favorite_only: favoriteOnly });
    return this.request(`/api/history?${params}`);
  },

  deleteHistory(id) {
    return this.request(`/api/history/${id}`, { method: 'DELETE' });
  },

  toggleFavorite(id) {
    return this.request(`/api/history/${id}/favorite`, { method: 'POST' });
  },

  getSettings() {
    return this.request('/api/settings');
  },

  saveSettings(settings) {
    return this.request('/api/settings', { method: 'POST', body: JSON.stringify(settings) });
  },

  getFormats() {
    return this.request('/api/formats');
  },

  getCookiesStatus() {
    return this.request('/api/settings/cookies');
  },

  async uploadCookies({ file = null, content = '' } = {}) {
    const form = new FormData();
    if (file) form.append('file', file);
    if (content) form.append('content', content);
    const res = await fetch(`${this.base}/api/settings/cookies`, {
      method: 'POST',
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw buildApiError(body, res.statusText || 'Upload failed');
    }
    return res.json();
  },

  connectWebSocket(downloadId, onMessage) {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const qs = downloadId ? `?download_id=${downloadId}` : '';
    const ws = new WebSocket(`${proto}//${location.host}/ws/download${qs}`);
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)); } catch {}
    };
    ws.onopen = () => setInterval(() => ws.readyState === 1 && ws.send('ping'), 30000);
    return ws;
  },
};

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let val = bytes;
  while (val >= 1024 && i < units.length - 1) { val /= 1024; i++; }
  return `${val.toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
}

function formatDuration(seconds) {
  if (!seconds) return '00:00';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function formatEta(seconds) {
  if (!seconds) return '--:--';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function formatSpeed(bps) {
  if (!bps) return '0 B/s';
  return `${formatBytes(bps)}/s`;
}
