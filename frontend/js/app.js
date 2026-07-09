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
        this.platforms = data.platforms || [];
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

    platformIcon(name) {
      const icons = {
        'YouTube': 'fa-youtube text-red-500',
        'Facebook': 'fa-facebook text-blue-500',
        'Instagram': 'fa-instagram text-pink-500',
        'TikTok': 'fa-tiktok',
        'X (Twitter)': 'fa-x-twitter',
        'Twitch': 'fa-twitch text-purple-500',
        'Vimeo': 'fa-vimeo text-blue-400',
        'SoundCloud': 'fa-soundcloud text-orange-500',
        'Reddit': 'fa-reddit text-orange-600',
      };
      return icons[name] || 'fa-globe';
    },

    formatBytes, formatDuration, formatEta, formatSpeed,
    Theme,
  };
}
