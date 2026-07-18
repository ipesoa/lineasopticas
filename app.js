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
  const horizontalTrack = document.querySelector("#horizontalTrack");
  const horizontalThumb = document.querySelector("#horizontalThumb");
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

  const fitTitle = element => {
    element.style.fontSize = "";
    const max = parseFloat(getComputedStyle(element).fontSize);
    const min = 12;
    const availableWidth = element.clientWidth - 2;
    let low = min;
    let high = max;

    for (let iteration = 0; iteration < 18; iteration += 1) {
      const middle = (low + high) / 2;
      element.style.fontSize = `${middle}px`;

      if (element.scrollWidth <= availableWidth) {
        low = middle;
      } else {
        high = middle;
      }
    }

    element.style.fontSize = `${Math.max(min, low - 0.15)}px`;
  };

  const fitPreview = element => {
    const completeText = cleanPreviewText(element.dataset.fullText);
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

  const syncHorizontalThumb = () => {
    if (!horizontalScroll || window.innerWidth < 740) return;

    const maximumScroll = Math.max(0, grid.scrollWidth - grid.clientWidth);
    const availableTravel = Math.max(
      0,
      horizontalTrack.clientWidth - horizontalThumb.offsetWidth
    );
    const ratio = maximumScroll > 0 ? grid.scrollLeft / maximumScroll : 0;

    horizontalThumb.style.transform = `translateX(${ratio * availableTravel}px)`;
    horizontalScroll.hidden = window.innerWidth < 740;
  };

  const enableHorizontalControls = () => {
    let dragging = false;
    let startPointerX = 0;
    let startScrollLeft = 0;

    horizontalThumb.addEventListener("pointerdown", event => {
      dragging = true;
      startPointerX = event.clientX;
      startScrollLeft = grid.scrollLeft;
      horizontalThumb.setPointerCapture(event.pointerId);
      event.preventDefault();
    });

    horizontalThumb.addEventListener("pointermove", event => {
      if (!dragging) return;

      const maximumScroll = Math.max(0, grid.scrollWidth - grid.clientWidth);
      const availableTravel = Math.max(
        1,
        horizontalTrack.clientWidth - horizontalThumb.offsetWidth
      );
      const pointerMovement = event.clientX - startPointerX;

      grid.scrollLeft = startScrollLeft
        + pointerMovement * (maximumScroll / availableTravel) * 1.65;
    });

    const stopDragging = event => {
      dragging = false;
      if (horizontalThumb.hasPointerCapture?.(event.pointerId)) {
        horizontalThumb.releasePointerCapture(event.pointerId);
      }
    };

    horizontalThumb.addEventListener("pointerup", stopDragging);
    horizontalThumb.addEventListener("pointercancel", stopDragging);

    horizontalTrack.addEventListener("pointerdown", event => {
      if (event.target === horizontalThumb) return;

      const bounds = horizontalTrack.getBoundingClientRect();
      const thumbWidth = horizontalThumb.offsetWidth;
      const availableTravel = Math.max(1, bounds.width - thumbWidth);
      const pointerPosition = Math.min(
        Math.max(event.clientX - bounds.left - thumbWidth / 2, 0),
        availableTravel
      );
      const maximumScroll = Math.max(0, grid.scrollWidth - grid.clientWidth);

      grid.scrollLeft = (pointerPosition / availableTravel) * maximumScroll;
      syncHorizontalThumb();
    });

    grid.addEventListener("wheel", event => {
      if (window.innerWidth < 740 || grid.scrollWidth <= grid.clientWidth) return;

      const movement = Math.abs(event.deltaX) > Math.abs(event.deltaY)
        ? event.deltaX
        : event.deltaY;

      if (!movement) return;

      event.preventDefault();
      grid.scrollLeft += movement * 2.35;
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
      const preview = node.querySelector(".card-summary");
      const date = node.querySelector(".card-date");
      const read = node.querySelector(".read-more");

      const open = () => openArticle(article, true);

      title.textContent = article.title;
      preview.dataset.fullText = article.content || article.summary;
      preview.textContent = article.content || article.summary;
      date.textContent = formatDate(article.publishedAt);
      date.dateTime = article.publishedAt;

      card.dataset.articleId = article.id;
      card.tabIndex = 0;
      card.setAttribute("role", "button");
      card.setAttribute("aria-label", `Leer ${article.title}`);
      card.addEventListener("click", open);
      card.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          open();
        }
      });

      read.addEventListener("click", event => {
        event.stopPropagation();
        open();
      });

      grid.append(node);
    });

    requestAnimationFrame(() => {
      grid.querySelectorAll(".card-title").forEach(fitTitle);
      grid.querySelectorAll(".card-summary").forEach(fitPreview);
      grid.scrollLeft = 0;
      syncHorizontalThumb();
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

  const canonicalArticleUrl = article => {
    const url = new URL(window.location.href);
    url.searchParams.set("article", article.slug);
    return url.toString();
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
      const url = new URL(window.location.href);
      url.searchParams.delete("article");
      history.replaceState({}, "", url);
    }
  };

  const openArticle = (article, updateUrl = false) => {
    const shareUrl = canonicalArticleUrl(article);
    const encodedUrl = encodeURIComponent(shareUrl);
    const encodedText = encodeURIComponent(article.title);
    const shareDescription = cleanPreviewText(article.content).slice(0, 180);

    openModal(`
      <article>
        <h1 id="modalTitle" class="article-modal-title">${escapeHtml(article.title)}</h1>
        <div class="article-body">${paragraphs(article.content || article.summary)}</div>

        <section class="share-panel" aria-label="Compartir noticia">
          <div class="share-actions">
            <button class="share-action" id="nativeShare" type="button">compartir</button>
            <button class="share-action" id="copyLink" type="button">copiar link</button>
            <a class="share-action" target="_blank" rel="noopener noreferrer"
              href="https://wa.me/?text=${encodedText}%20${encodedUrl}">whatsapp</a>
          </div>
        </section>
      </article>
    `);

    if (updateUrl) {
      history.pushState({ article: article.slug }, "", shareUrl);
    }

    document.querySelector("#copyLink").addEventListener("click", async event => {
      try {
        await navigator.clipboard.writeText(shareUrl);
        event.currentTarget.textContent = "link copiado";
      } catch {
        window.prompt("Copia este enlace:", shareUrl);
      }
    });

    document.querySelector("#nativeShare").addEventListener("click", async event => {
      try {
        if (navigator.share) {
          await navigator.share({
            title: article.title,
            text: shareDescription,
            url: shareUrl
          });
        } else {
          await navigator.clipboard.writeText(shareUrl);
          event.currentTarget.textContent = "link copiado";
        }
      } catch (error) {
        if (error?.name !== "AbortError") console.error(error);
      }
    });
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
            <button class="result-item" type="button" data-id="${escapeHtml(article.id)}">
              <strong>${escapeHtml(article.title)}</strong>
              <time>${formatDate(article.publishedAt)}</time>
            </button>
          `).join("")
        : query
          ? "<p>NO HAY RESULTADOS.</p>"
          : "<p>ESCRIBE PARA BUSCAR.</p>";

      results.querySelectorAll("[data-id]").forEach(button => {
        button.addEventListener("click", () => {
          const article = state.all.find(item => item.id === button.dataset.id);
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

      const slug = new URL(window.location.href).searchParams.get("article");
      if (slug) {
        const article = state.all.find(
          item => item.slug === slug || item.id === slug
        );
        if (article) openArticle(article, false);
      }
    } catch (error) {
      console.error(error);
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
    const slug = new URL(window.location.href).searchParams.get("article");

    if (!slug) {
      closeModal({ clearUrl: false });
      return;
    }

    const article = state.all.find(
      item => item.slug === slug || item.id === slug
    );
    if (article) openArticle(article, false);
  });

  grid.addEventListener("scroll", syncHorizontalThumb, { passive: true });

  window.addEventListener("resize", () => {
    grid.querySelectorAll(".card-title").forEach(fitTitle);
    grid.querySelectorAll(".card-summary").forEach(fitPreview);
    syncHorizontalThumb();
  });

  enableHorizontalControls();
  load();
})();
