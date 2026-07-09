/**
 * Theme management (dark / light mode).
 */
const Theme = {
  current: localStorage.getItem('theme') || 'dark',

  init() {
    this.apply(this.current);
  },

  apply(theme) {
    this.current = theme;
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  },

  toggle() {
    this.apply(this.current === 'dark' ? 'light' : 'dark');
  },
};

Theme.init();
