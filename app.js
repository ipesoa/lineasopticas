(() => {
  "use strict";

  const config = window.LINEAS_OPTICAS_CONFIG || {};
  const state = {
    all: [],
    visible: [],
    page: 1,
    mode: "all"
  };

  const grid = document.querySelector("#newsGrid");
  const status = document.querySelector("#status");
  const prev = document.querySelector("#prevPage");
  const next = document.querySelector("#nextPage");
  const indicator = document.querySelector("#pageIndicator");
  const modalLayer = document.querySelector("#modalLayer");
  const modalContent = document.querySelector("#modalContent");
  const modalClose = document.querySelector("#modalClose");
  const template = document.querySelector("#articleCardTemplate");
  const horizontalScroll = document.querySelector("#horizontalScroll");
  const horizontalRange = document.querySelector("#horizontalRange");
  const featuredButton = document.querySelector('[data-action="featured"]');

  const normalize = raw => {
    const list = Array.isArray(raw) ? raw : raw.articles || raw.news || [];
    return list
      .filter(Boolean)
      .map((item, index) => ({
        id: String(item.id ?? item.slug ?? `noticia-${index + 1}`),
        slug: String(item.slug ?? item.id ?? `noticia-${index + 1}`),
        title: String(item.title ?? item.titular ?? "Sin titular"),
        summary: String(item.summary ?? item.excerpt ?? item.resumen ?? ""),
        content: String(item.content ?? item.body ?? item.text ?? item.texto ?? ""),
        publishedAt: item.publishedAt ?? item.date ?? item.fecha ?? new Date().toISOString(),
        updatedAt: item.updatedAt ?? item.publishedAt ?? item.date ?? item.fecha ?? new Date().toISOString(),
        author: String(item.author ?? item.autor ?? config.publicationName ?? "Líneas Ópticas"),
        section: String(item.section ?? item.seccion ?? "Actualidad"),
        featured: Boolean(item.featured ?? item.destacada ?? false),
        tags: Array.isArray(item.tags ?? item.etiquetas)
          ? (item.tags ?? item.etiquetas).map(String)
          : [],
        hiddenTags: Array.isArray(item.hiddenTags ?? item.etiquetasOcultas)
          ? (item.hiddenTags ?? item.etiquetasOcultas).map(String)
          : []
      }))
      .sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));
  };

  const escapeHtml = value => String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const paragraphs = value => escapeHtml(value)
    .split(/\n{2,}/)
    .filter(Boolean)
    .map(paragraph => `<p>${paragraph.replaceAll("\n", "<br>")}</p>`)
    .join("");

  const formatDate = value => new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));

  const pageCount = () => Math.max(
    1,
    Math.ceil(state.visible.length / Number(config.itemsPerPage || 40))
  );

  const cleanPreviewText = value => String(value || "")
    .replace(/\s+/g, " ")
    .trim();

  const fitTitle = container => {
    const text = container.querySelector(".card-title-text");
    if (!text) return;

    text.style.fontSize = "";
    text.style.transform = "none";

    const maximumSize = parseFloat(getComputedStyle(container).fontSize);
    const minimumSize = window.innerWidth < 740 ? 18 : 22;
    const safetyMargin = window.innerWidth < 740 ? 12 : 18;
    const availableWidth = Math.max(
      1,
      container.clientWidth - safetyMargin
    );

    let low = minimumSize;
    let high = maximumSize;

    for (let iteration = 0; iteration < 20; iteration += 1) {
      const middle = (low + high) / 2;
      text.style.fontSize = `${middle}px`;

      if (text.scrollWidth <= availableWidth) {
        low = middle;
      } else {
        high = middle;
      }
    }

    text.style.fontSize = `${Math.max(minimumSize, low - 0.6)}px`;
  };

  const fitPreview = element => {
    const completeText = cleanPreviewText(element.dataset.fullText ?? element.textContent);
    element.textContent = completeText;

    if (!completeText) return;

    const styles = getComputedStyle(element);
    const lineHeight = parseFloat(styles.lineHeight);
    const maximumHeight = lineHeight * 8 + 1;
    element.style.maxHeight = `${maximumHeight}px`;

    if (element.scrollHeight <= maximumHeight + 1) return;

    const words = completeText.split(" ");
    let low = 0;
    let high = words.length;
    let best = "";

    while (low <= high) {
      const middle = Math.floor((low + high) / 2);
      const candidate = `${words.slice(0, middle).join(" ").replace(/[\s,;:.!?—-]+$/u, "")}…`;
      element.textContent = candidate;

      if (element.scrollHeight <= maximumHeight + 1) {
        best = candidate;
        low = middle + 1;
      } else {
        high = middle - 1;
      }
    }

    element.textContent = best || "…";
  };

  const syncHorizontalControl = () => {
    if (!horizontalRange || window.innerWidth < 740) return;

    const maximumScroll = Math.max(0, grid.scrollWidth - grid.clientWidth);
    const ratio = maximumScroll > 0 ? grid.scrollLeft / maximumScroll : 0;

    horizontalRange.value = String(Math.round(ratio * 1000));
    horizontalRange.disabled = false;
  };

  const enableHorizontalControls = () => {
    horizontalRange.addEventListener("input", () => {
      const maximumScroll = Math.max(0, grid.scrollWidth - grid.clientWidth);
      grid.scrollLeft = (Number(horizontalRange.value) / 1000) * maximumScroll;
    });

    grid.addEventListener("wheel", event => {
      if (window.innerWidth < 740 || grid.scrollWidth <= grid.clientWidth) return;

      const movement = Math.abs(event.deltaX) > Math.abs(event.deltaY)
        ? event.deltaX
        : event.deltaY;

      if (!movement) return;

      event.preventDefault();
      grid.scrollLeft += movement * 2.8;
    }, { passive: false });
  };

  const render = () => {
    grid.replaceChildren();

    if (!state.visible.length) {
      grid.innerHTML = '<div class="empty">NO HAY NOTICIAS.</div>';
      indicator.textContent = "0 / 0";
      prev.disabled = true;
      next.disabled = true;
      horizontalScroll.hidden = true;
      return;
    }

    horizontalScroll.hidden = false;

    const totalPages = pageCount();
    state.page = Math.min(Math.max(state.page, 1), totalPages);
    const start = (state.page - 1) * Number(config.itemsPerPage || 40);
    const pageItems = state.visible.slice(
      start,
      start + Number(config.itemsPerPage || 40)
    );

    pageItems.forEach(article => {
      const node = template.content.cloneNode(true);
      const card = node.querySelector(".article-card");
      const title = node.querySelector(".card-title");
      const titleText = node.querySelector(".card-title-text");
      const preview = node.querySelector(".card-summary");
      const date = node.querySelector(".card-date");
      const read = node.querySelector(".read-more");

      const open = event => {
        if (event && (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)) return;
        event?.preventDefault();
        openArticle(article, true);
      };

      titleText.textContent = article.title;
      preview.dataset.fullText = article.content || article.summary;
      preview.textContent = article.content || article.summary;
      date.textContent = formatDate(article.publishedAt);
      date.dateTime = article.publishedAt;

      card.dataset.articleId = article.id;
      card.href = canonicalArticleUrl(article);
      card.setAttribute("aria-label", `Leer ${article.title}`);
      card.addEventListener("click", open);
      read.setAttribute("aria-hidden", "true");

      grid.append(node);
    });

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        grid.querySelectorAll(".card-title").forEach(fitTitle);
        grid.querySelectorAll(".card-summary").forEach(fitPreview);
        grid.scrollLeft = 0;
        syncHorizontalControl();
      });
    });

    indicator.textContent = `${state.page} / ${totalPages}`;
    prev.disabled = state.page <= 1;
    next.disabled = state.page >= totalPages;
    status.textContent = "";
    featuredButton.setAttribute(
      "aria-pressed",
      String(state.mode === "featured")
    );
  };

  const siteRoot = () => `${String(config.siteUrl || new URL(".", window.location.href)).replace(/\/$/, "")}/`;

  const canonicalArticleUrl = article =>
    `${siteRoot()}${String(config.articlePath || "noticias").replace(/^\/+|\/+$/g, "")}/${encodeURIComponent(article.slug)}/`;

  const articleImageUrl = article =>
    `${siteRoot()}${String(config.imagePath || "media/noticias").replace(/^\/+|\/+$/g, "")}/${encodeURIComponent(article.slug)}.svg`;

  const sameOriginHistoryUrl = targetUrl => {
    const target = new URL(targetUrl, window.location.href);
    if (target.origin === window.location.origin) return target.toString();

    const local = new URL(window.location.href);
    local.search = "";
    local.hash = "";
    return local.toString();
  };

  const slugFromLocation = () => {
    const url = new URL(window.location.href);
    const querySlug = url.searchParams.get("article");
    if (querySlug) return querySlug;

    try {
      const rootPath = new URL(siteRoot()).pathname.replace(/\/$/, "");
      const relative = url.pathname.startsWith(rootPath)
        ? url.pathname.slice(rootPath.length)
        : url.pathname;
      const match = relative.match(/^\/?noticias\/([^/]+)\/?$/);
      return match ? decodeURIComponent(match[1]) : null;
    } catch {
      return null;
    }
  };

  const openModal = html => {
    modalContent.innerHTML = html;
    modalLayer.hidden = false;
    document.body.classList.add("modal-open");
    modalContent.scrollTop = 0;
    modalClose.focus();
  };

  const closeModal = ({ clearUrl = true } = {}) => {
    modalLayer.hidden = true;
    document.body.classList.remove("modal-open");
    modalContent.replaceChildren();

    if (clearUrl) {
      history.replaceState({}, "", sameOriginHistoryUrl(siteRoot()));
    }
  };

  const openArticle = (article, updateUrl = false) => {
    const shareUrl = canonicalArticleUrl(article);
    const imageUrl = articleImageUrl(article);
    const shareDescription = cleanPreviewText(article.content).slice(0, 180);

    openModal(`
      <article>
        <h1 id="modalTitle" class="article-modal-title">${escapeHtml(article.title)}</h1>
        <div class="article-body">${paragraphs(article.content || article.summary)}</div>

        <section class="share-panel" aria-label="Compartir noticia">
          <div class="share-actions">
            <button class="share-action" id="nativeShare" type="button">compartir</button>
            <button class="share-image-button" id="imageShare" type="button" aria-label="Compartir ${escapeHtml(article.title)}">
              <img class="share-image" src="${escapeHtml(imageUrl)}" width="1200" height="1200"
                alt="Composición tipográfica del titular ${escapeHtml(article.title)}">
            </button>
            <button class="share-action" id="copyLink" type="button">copiar link</button>
          </div>
        </section>
      </article>
    `);

    if (updateUrl) {
      const target = new URL(shareUrl);
      const historyUrl = target.origin === window.location.origin
        ? shareUrl
        : `${sameOriginHistoryUrl(siteRoot())}?article=${encodeURIComponent(article.slug)}`;
      history.pushState({ article: article.slug }, "", historyUrl);
    }

    const copyButton = document.querySelector("#copyLink");
    const shareButtons = [
      document.querySelector("#nativeShare"),
      document.querySelector("#imageShare")
    ];

    const copyLink = async button => {
      try {
        await navigator.clipboard.writeText(shareUrl);
        const previous = button.textContent;
        button.textContent = "link copiado";
        window.setTimeout(() => { button.textContent = previous; }, 1800);
      } catch {
        window.prompt("Copia este enlace:", shareUrl);
      }
    };

    copyButton.addEventListener("click", () => copyLink(copyButton));

    shareButtons.forEach(button => button.addEventListener("click", async () => {
      try {
        if (navigator.share) {
          await navigator.share({
            title: article.title,
            text: shareDescription,
            url: shareUrl
          });
        } else {
          await copyLink(document.querySelector("#nativeShare"));
        }
      } catch (error) {
        if (error?.name !== "AbortError") console.error(error);
      }
    }));
  };

  const openSearch = () => {
    openModal(`
      <section>
        <h1 id="modalTitle" class="utility-title">BUSCAR</h1>
        <form class="search-form" id="searchForm">
          <input id="searchInput" type="search" autocomplete="off"
            placeholder="TITULAR, TEXTO, FECHA O ETIQUETA"
            aria-label="Buscar noticias">
          <button class="modal-button" type="submit">BUSCAR</button>
        </form>
        <div id="searchResults" class="result-list"></div>
      </section>
    `);

    const input = document.querySelector("#searchInput");
    const results = document.querySelector("#searchResults");

    const runSearch = () => {
      const query = input.value.trim().toLocaleLowerCase("es");
      const matches = !query ? [] : state.all.filter(article => {
        const searchable = [
          article.title,
          article.summary,
          article.content,
          formatDate(article.publishedAt),
          ...article.tags,
          ...article.hiddenTags
        ].join(" ").toLocaleLowerCase("es");

        return searchable.includes(query);
      });

      results.innerHTML = matches.length
        ? matches.map(article => `
            <a class="result-item" href="${escapeHtml(canonicalArticleUrl(article))}" data-id="${escapeHtml(article.id)}">
              <strong>${escapeHtml(article.title)}</strong>
              <time>${formatDate(article.publishedAt)}</time>
            </a>
          `).join("")
        : query
          ? "<p>NO HAY RESULTADOS.</p>"
          : "<p>ESCRIBE PARA BUSCAR.</p>";

      results.querySelectorAll("[data-id]").forEach(link => {
        link.addEventListener("click", event => {
          if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
          event.preventDefault();
          const article = state.all.find(item => item.id === link.dataset.id);
          if (article) openArticle(article, true);
        });
      });
    };

    document.querySelector("#searchForm").addEventListener("submit", event => {
      event.preventDefault();
      runSearch();
    });

    input.addEventListener("input", runSearch);
    input.focus();
  };

  const openDonation = () => {
    openModal(`
      <section class="donation-panel">
        <h1 id="modalTitle" class="utility-title">DONACIÓN</h1>

        <p class="donation-copy">
          La aportación es voluntaria y se destina a apoyar la continuidad de este diario y la futura
          producción de proyectos editoriales. Se realiza a título gratuito y sin contraprestación:
          no constituye una compra, preventa o reserva, ni otorga derecho a recibir un ejemplar,
          devolución, descuento u otra prestación. Se formula conforme al concepto de donación del
          artículo 618 del Código Civil y al artículo 3.1.b de la Ley 29/1987, del Impuesto sobre
          Sucesiones y Donaciones.
        </p>

        <div class="donation-actions">
          <a class="modal-button" href="${escapeHtml(config.stripe.donationUrl)}"
            target="_blank" rel="noopener noreferrer">DONAR DESDE 5 €</a>
          <a class="modal-button" href="${escapeHtml(config.stripe.monthlyUrl)}"
            target="_blank" rel="noopener noreferrer">APOYO MENSUAL 5 €</a>
        </div>

        <p class="stripe-note">
          El pago se realiza de forma segura a través de Stripe. Líneas Ópticas no recibe ni
          almacena los datos de la tarjeta.
        </p>
      </section>
    `);
  };

  const load = async () => {
    status.textContent = "CARGANDO...";

    try {
      const response = await fetch(config.apiUrl, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      state.all = normalize(await response.json());
      state.visible = [...state.all];
      status.textContent = "";
      render();

      const slug = slugFromLocation();
      if (slug) {
        const article = state.all.find(
          item => item.slug === slug || item.id === slug
        );
        if (article) openArticle(article, false);
      }
    } catch (error) {
      console.error(error);

      // La portada compilada ya contiene las noticias en HTML. Si el JSON no
      // puede cargarse (por ejemplo, al abrir index.html directamente desde
      // el disco), se conserva ese contenido en lugar de dejar la web vacía.
      const staticCards = grid.querySelectorAll(".article-card");
      if (staticCards.length) {
        status.textContent = "";
        horizontalScroll.hidden = window.innerWidth < 740;
        indicator.textContent = "1 / 1";
        prev.disabled = true;
        next.disabled = true;
        requestAnimationFrame(() => {
          grid.querySelectorAll(".card-title").forEach(fitTitle);
          grid.querySelectorAll(".card-summary").forEach(fitPreview);
          syncHorizontalControl();
        });
        return;
      }

      status.textContent = "NO SE PUDO LEER LA API.";
      grid.innerHTML = `
        <div class="empty">
          REVISA config.js, LA URL DEL JSON Y LOS PERMISOS CORS.
        </div>
      `;
    }
  };

  document.querySelector('[data-action="search"]')
    .addEventListener("click", openSearch);

  document.querySelector('[data-action="donation"]')
    .addEventListener("click", openDonation);

  featuredButton.addEventListener("click", () => {
    state.mode = state.mode === "featured" ? "all" : "featured";
    state.visible = state.mode === "featured"
      ? state.all.filter(article => article.featured)
      : [...state.all];
    state.page = 1;
    render();
  });

  prev.addEventListener("click", () => {
    if (state.page <= 1) return;
    state.page -= 1;
    render();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  next.addEventListener("click", () => {
    if (state.page >= pageCount()) return;
    state.page += 1;
    render();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  modalClose.addEventListener("click", () => closeModal());

  modalLayer.addEventListener("click", event => {
    if (event.target === modalLayer) closeModal();
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !modalLayer.hidden) closeModal();
  });

  window.addEventListener("popstate", () => {
    const slug = slugFromLocation();

    if (!slug) {
      closeModal({ clearUrl: false });
      return;
    }

    const article = state.all.find(
      item => item.slug === slug || item.id === slug
    );
    if (article) openArticle(article, false);
  });

  grid.addEventListener("scroll", syncHorizontalControl, { passive: true });

  window.addEventListener("resize", () => {
    grid.querySelectorAll(".card-title").forEach(fitTitle);
    grid.querySelectorAll(".card-summary").forEach(fitPreview);
    syncHorizontalControl();
  });

  enableHorizontalControls();
  load();
})();
