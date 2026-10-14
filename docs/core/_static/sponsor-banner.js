/* Dismiss only the content banner on the current documentation page. */
(() => {
  const storageKey = banner => `openbacktesting:sponsor-banner:dismissed:${banner.dataset.sponsorPage}`;

  const restore = () => {
    document.querySelectorAll("[data-sponsor-page]").forEach(banner => {
      try {
        banner.hidden = localStorage.getItem(storageKey(banner)) === "1";
      } catch {
        // Keep the banner usable when browser storage is unavailable.
      }
      banner.querySelector(".ob-sponsor-banner__close").hidden = false;
    });
  };

  restore();
  if (typeof document$ !== "undefined") document$.subscribe(restore);

  document.addEventListener("click", event => {
    const button = event.target.closest(".ob-sponsor-banner__close");
    if (!button) return;
    const banner = button.closest("[data-sponsor-page]");
    banner.hidden = true;
    try {
      localStorage.setItem(storageKey(banner), "1");
    } catch {
      // Closing still works for this visit if persistence is blocked.
    }
  });
})();
