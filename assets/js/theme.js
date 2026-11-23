(() => {
  const root = document.documentElement;
  const storageKey = 'cmlab-theme';

  function apply(light) {
    if (light) root.dataset.theme = 'light';
    else delete root.dataset.theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', light ? '#f5f7fd' : '#070b15');
  }

  try {
    apply(localStorage.getItem(storageKey) === 'light');
  } catch {
    apply(false);
  }

  document.addEventListener('DOMContentLoaded', () => {
    const button = document.querySelector('.theme-toggle');
    if (!button) return;
    button.hidden = false;
    button.setAttribute('aria-pressed', String(root.dataset.theme === 'light'));
    button.addEventListener('click', () => {
      const light = root.dataset.theme !== 'light';
      apply(light);
      button.setAttribute('aria-pressed', String(light));
      try {
        localStorage.setItem(storageKey, light ? 'light' : 'dark');
      } catch {
        // The theme still works for the current page if storage is disabled.
      }
    });
  });
})();
