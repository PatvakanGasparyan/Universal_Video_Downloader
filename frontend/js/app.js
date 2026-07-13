/**
 * Main downloader application (Alpine.js component).
 */
function downloaderApp() {
  return {
    ...I18n.mixin(),
    url: '',
    metadata: null,
    progress: null,
    completed: false,
    loading: false,
    downloading: false,
    error: '',
    dragOver: false,
    downloadId: null,
    ws: null,
    selectedQuality: 'best',
    selectedFormat: 'mp4',
    qualities: ['best', '8k', '4k', '1440p', '1080p', '720p', '480p', '360p'],
    formats: ['mp4', 'mkv', 'webm', 'avi', 'mov', 'mp3', 'aac', 'm4a', 'flac', 'wav', 'ogg'],
    platforms: [],

    async init() {
      await this.initI18n();
      document.title = this.t('app_title');
      try {
        const data = await API.getFormats();
        const list = data.platforms || [];
        // Support both legacy string[] and {name,url,icon}[]
        this.platforms = list.map((p) => (
          typeof p === 'string'
            ? { name: p, url: '#', icon: p.toLowerCase() }
            : p
        ));
      } catch {}
      document.addEventListener('paste', (e) => this.handlePaste(e));
    },

    async analyze() {
      this.error = '';
      this.metadata = null;
      this.progress = null;
      this.completed = false;
      if (!this.url.trim()) {
        this.error = this.t('error_invalid_url');
        return;
      }
      this.loading = true;
      try {
        this.metadata = await API.getInfo(this.url.trim());
      } catch (e) {
        this.error = this.formatError(e);
      } finally {
        this.loading = false;
      }
    },

    async startDownload() {
      this.downloading = true;
      this.completed = false;
      this.progress = { percent: 0, status: 'queued', message: this.t('status_queued') };
      try {
        const audioOnly = ['mp3','aac','m4a','flac','wav','ogg'].includes(this.selectedFormat);
        const res = await API.startDownload({
          url: this.url.trim(),
          quality: this.selectedQuality,
          format: this.selectedFormat,
          audio_only: audioOnly,
        });
        this.downloadId = res.download_id;
        this.ws = API.connectWebSocket(this.downloadId, (data) => {
          this.progress = data;
          if (data.status === 'completed') {
            this.completed = true;
            this.downloading = false;
          }
          if (data.status === 'failed' || data.status === 'cancelled') {
            this.downloading = false;
          }
        });
      } catch (e) {
        this.error = this.formatError(e);
        this.downloading = false;
      }
    },

    formatError(e) {
      const msg = e?.message || this.t('error_fetch_info');
      if (/not a bot|cookies-from-browser|--cookies/i.test(msg)) {
        return `${msg}\n\n${this.t('cookies_required_hint')}`;
      }
      return msg;
    },

    async pauseResume() {
      if (!this.downloadId) return;
      if (this.progress?.status === 'paused') {
        await API.resumeDownload(this.downloadId);
      } else {
        await API.pauseDownload(this.downloadId);
      }
    },

    async cancelDownload() {
      if (this.downloadId) await API.cancelDownload(this.downloadId);
      this.downloading = false;
    },

    reset() {
      this.url = '';
      this.metadata = null;
      this.progress = null;
      this.completed = false;
      this.downloadId = null;
      if (this.ws) this.ws.close();
    },

    handleDrop(e) {
      this.dragOver = false;
      const text = e.dataTransfer.getData('text');
      if (text) { this.url = text.trim(); this.analyze(); }
    },

    handlePaste(e) {
      const text = e.clipboardData?.getData('text') || '';
      if (text.match(/^https?:\/\//)) {
        this.url = text.trim();
      }
    },

    platformIconHtml(platform) {
      const key = (platform.icon || platform.name || '').toLowerCase();
      const fa = {
        youtube: '<i class="fab fa-youtube" style="color:#ef4444"></i>',
        facebook: '<i class="fab fa-facebook" style="color:#3b82f6"></i>',
        instagram: '<i class="fab fa-instagram" style="color:#ec4899"></i>',
        tiktok: '<i class="fab fa-tiktok"></i>',
        x: '<i class="fab fa-x-twitter"></i>',
        twitter: '<i class="fab fa-x-twitter"></i>',
        twitch: '<i class="fab fa-twitch" style="color:#a855f7"></i>',
        vimeo: '<i class="fab fa-vimeo-v" style="color:#60a5fa"></i>',
        soundcloud: '<i class="fab fa-soundcloud" style="color:#f97316"></i>',
        reddit: '<i class="fab fa-reddit" style="color:#ea580c"></i>',
        vk: '<i class="fab fa-vk" style="color:#3b82f6"></i>',
        threads: '<i class="fab fa-threads"></i>',
        bilibili: '<i class="fab fa-bilibili" style="color:#00a1d6"></i>',
      };
      if (fa[key]) return fa[key];

      // Custom SVGs for brands missing reliable FA glyphs
      const svg = {
        rutube: `<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#ff4e45" d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm6 3.5v9l7-4.5-7-4.5z"/></svg>`,
        dailymotion: `<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#00aaff" d="M3 3h8.5c3.6 0 6.5 2.6 6.5 6.1 0 2.7-1.7 5-4.2 5.8L21 21h-3.3l-6.3-5.6H9.5V21H3V3zm6.5 3.2v5.8H11c1.9 0 3.2-1.2 3.2-2.9S12.9 6.2 11 6.2H9.5z"/></svg>`,
      };
      if (svg[key]) return svg[key];
      return '<i class="fas fa-globe"></i>';
    },

    formatBytes, formatDuration, formatEta, formatSpeed,
    Theme,
  };
}
