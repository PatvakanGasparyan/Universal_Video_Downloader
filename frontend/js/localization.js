/**
 * Client-side localization with instant language switching.
 */
const I18n = {
  lang: localStorage.getItem('lang') || 'en',
  strings: {},

  async load(lang) {
    this.lang = lang || this.lang;
    localStorage.setItem('lang', this.lang);
    const res = await fetch(`/static/localization/${this.lang}.json`);
    if (!res.ok) {
      console.error(`Locale file not found: /static/localization/${this.lang}.json`);
      if (this.lang !== 'en') {
        return this.load('en');
      }
      throw new Error(`Failed to load locale: ${this.lang}`);
    }
    this.strings = await res.json();
    document.documentElement.lang = this.lang;
    window.dispatchEvent(new CustomEvent('lang-changed', { detail: { lang: this.lang } }));
    return this.strings;
  },

  t(key, strings = null) {
    const table = strings || this.strings;
    return table[key] || key;
  },

  /** Alpine.js mixin — keeps strings on the component for proper reactivity. */
  mixin() {
    return {
      currentLang: I18n.lang,
      strings: {},
      i18nReady: false,

      t(key) {
        return I18n.t(key, this.strings);
      },

      async initI18n() {
        const loaded = await I18n.load(I18n.lang);
        this.strings = { ...loaded };
        this.currentLang = I18n.lang;
        this.i18nReady = true;
      },

      async changeLang(lang) {
        const loaded = await I18n.load(lang);
        this.strings = { ...loaded };
        this.currentLang = I18n.lang;
        this.i18nReady = true;
      },
    };
  },
};
