/* Copy the authored Markdown, including code, rather than scraping the page UI. */
(() => {
  const enable = () => {
    document.querySelectorAll("[data-copy-markdown]").forEach(button => {
      button.hidden = false;
    });
  };
  enable();
  if (typeof document$ !== "undefined") document$.subscribe(enable);

  document.addEventListener("click", async event => {
    const button = event.target.closest("[data-copy-markdown]");
    if (!button || button.disabled) return;
    const status = document.getElementById("ob-copy-status");
    const label = button.querySelector("[data-copy-label]");
    const fallback = document.querySelector(".ob-markdown-fallback");
    const textarea = document.getElementById("ob-markdown-text");
    button.disabled = true;
    label.textContent = "Copying…";
    status.textContent = "";
    fallback.hidden = true;
    try {
      const response = await fetch(button.dataset.markdownUrl);
      if (!response.ok) throw new Error("Markdown request failed");
      const markdown = await response.text();
      try {
        await navigator.clipboard.writeText(markdown);
        label.textContent = "Copied!";
        status.textContent = "Markdown copied to clipboard.";
      } catch {
        fallback.hidden = false;
        textarea.value = markdown;
        textarea.focus();
        textarea.select();
        label.textContent = "Copy as Markdown";
        status.textContent = "Clipboard access unavailable. Select and copy the Markdown below.";
      }
    } catch {
      label.textContent = "Copy as Markdown";
      status.textContent = "Could not load Markdown. Try again or use View Markdown.";
    } finally {
      button.disabled = false;
      setTimeout(() => { label.textContent = "Copy as Markdown"; }, 2500);
    }
  });
})();
