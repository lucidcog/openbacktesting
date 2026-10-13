/* Material creates code-copy buttons dynamically; track without changing their behavior. */
(() => {
  document.addEventListener("click", event => {
    const button = event.target.closest('.md-code__button[data-md-type="copy"]');
    if (!button || button.disabled) return;
    try {
      const pending = window.umami?.track("docs-code-copy");
      pending?.catch(() => {});
    } catch {
      // Analytics must never interrupt copying when the tracker is unavailable.
    }
  }, true);
})();
