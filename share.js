(() => {
  "use strict";

  const copyUrl = async (button, url) => {
    try {
      await navigator.clipboard.writeText(url);
      const previous = button.textContent;
      button.textContent = "link copiado";
      window.setTimeout(() => { button.textContent = previous; }, 1800);
    } catch {
      window.prompt("Copia este enlace:", url);
    }
  };

  const share = async panel => {
    const data = {
      title: panel.dataset.shareTitle || document.title,
      text: panel.dataset.shareText || "",
      url: panel.dataset.shareUrl || window.location.href
    };

    try {
      if (typeof navigator.share === "function") {
        await navigator.share(data);
      } else {
        const message = [data.title, data.text, data.url]
          .filter(Boolean)
          .join("\n\n");
        window.location.assign(
          `https://wa.me/?text=${encodeURIComponent(message)}`
        );
      }
    } catch (error) {
      if (error?.name !== "AbortError") console.error(error);
    }
  };

  document.querySelectorAll("[data-share-panel]").forEach(panel => {
    panel.querySelectorAll("[data-share]").forEach(button => {
      button.addEventListener("click", () => share(panel));
    });

    panel.querySelectorAll("[data-copy]").forEach(button => {
      button.addEventListener("click", () => copyUrl(button, panel.dataset.shareUrl || window.location.href));
    });
  });
})();
