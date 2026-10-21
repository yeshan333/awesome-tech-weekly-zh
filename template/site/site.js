(() => {
  document.querySelectorAll(".featured-image[data-fallback]").forEach((image) => {
    const useFallback = () => {
      const fallback = image.dataset.fallback;
      if (!fallback) return;
      delete image.dataset.fallback;
      image.src = fallback;
    };
    image.addEventListener("error", useFallback, { once: true });
    if (image.complete && image.naturalWidth === 0) useFallback();
  });
  const root = document.documentElement;
  const motion = () =>
    matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "instant"
      : "smooth";
  const themeToggle = document.getElementById("themeToggle");
  function reflectTheme() {
    const dark = root.dataset.theme === "dark";
    themeToggle.setAttribute("aria-pressed", String(dark));
    themeToggle.setAttribute(
      "aria-label",
      dark ? "切换到浅色主题" : "切换到深色主题",
    );
  }
  themeToggle.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    try {
      localStorage.setItem("weekly-theme", root.dataset.theme);
    } catch {
      /* Session-only preference. */
    }
    reflectTheme();
  });
  reflectTheme();

  const search = document.getElementById("searchInput");
  const recent = document.getElementById("recentFilter");
  const clear = document.getElementById("clearFilters");
  const rows = [...document.querySelectorAll(".feed-row")];
  const sections = [...document.querySelectorAll(".category")];
  const nav = [...document.querySelectorAll(".nav-item")];
  const categorySelect = document.getElementById("categorySelect");
  categorySelect.replaceChildren(
    ...nav.map((item) => new Option(item.textContent, item.dataset.category)),
  );
  let category = "all";
  let recentOnly = false;

  function refreshRecency() {
    const now = Date.now();
    for (const row of rows) {
      const age = now - Date.parse(row.dataset.published);
      const isRecent = age >= 0 && age <= 7 * 86400000;
      row.dataset.recent = String(isRecent);
      const mark = row.querySelector(".recent-mark");
      if (mark) mark.hidden = !isRecent;
    }
    document.getElementById("recentTotal").textContent = rows.filter(
      (row) => row.dataset.recent === "true",
    ).length;
  }

  function applyFilters() {
    const query = search.value.trim().toLocaleLowerCase();
    let count = 0;
    for (const row of rows) {
      row.hidden = !(
        (category === "all" || row.dataset.category === category) &&
        (!recentOnly || row.dataset.recent === "true") &&
        row.dataset.search.includes(query)
      );
      if (!row.hidden) count++;
    }
    for (const section of sections) {
      const visible = [...section.querySelectorAll(".feed-row")].filter(
        (row) => !row.hidden,
      ).length;
      section.hidden = visible === 0;
      section.querySelector(".category-count").textContent =
        `${visible} 份周刊`;
    }
    for (const item of nav) {
      const selected = item.dataset.category === category;
      item.dataset.active = String(selected);
      if (selected) item.setAttribute("aria-current", "true");
      else item.removeAttribute("aria-current");
    }
    recent.setAttribute("aria-pressed", String(recentOnly));
    categorySelect.value = category;
    clear.hidden = !query && !recentOnly && category === "all";
    document.getElementById("noResults").hidden = count !== 0;
    const label = nav.find(
      (item) => item.dataset.category === category,
    )?.textContent;
    document.getElementById("resultCount").textContent =
      category === "all"
        ? `显示 ${count} / ${rows.length} 份周刊`
        : `${label} · ${count} 份周刊`;
  }

  nav.forEach((item) =>
    item.addEventListener("click", (event) => {
      event.preventDefault();
      category = item.dataset.category;
      applyFilters();
    }),
  );
  categorySelect.addEventListener("change", () => {
    category = categorySelect.value;
    applyFilters();
  });
  search.addEventListener("input", applyFilters);
  recent.addEventListener("click", () => {
    recentOnly = !recentOnly;
    refreshRecency();
    applyFilters();
  });
  function reset() {
    category = "all";
    recentOnly = false;
    search.value = "";
    applyFilters();
    search.focus({ preventScroll: true });
  }
  clear.addEventListener("click", reset);
  document.getElementById("resetFilters").addEventListener("click", reset);
  document.addEventListener("keydown", (event) => {
    if (
      event.key === "/" &&
      !event.ctrlKey &&
      !event.metaKey &&
      !event.altKey &&
      !event.target.closest("input, textarea, select, [contenteditable]")
    ) {
      event.preventDefault();
      search.focus();
    }
    if (event.key === "Escape" && document.activeElement === search) {
      search.value = "";
      applyFilters();
    }
  });
  refreshRecency();
  applyFilters();
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      refreshRecency();
      applyFilters();
    }
  });

  const back = document.getElementById("backToTop");
  function reflectScroll() {
    back.hidden = window.scrollY < 400;
  }
  window.addEventListener("scroll", reflectScroll, { passive: true });
  back.addEventListener("click", () =>
    window.scrollTo({ top: 0, behavior: motion() }),
  );
  reflectScroll();

  const track = document.getElementById("featuredTrack");
  if (track) {
    const cards = [...track.children];
    const previous = document.getElementById("previousArticle");
    const next = document.getElementById("nextArticle");
    const dots = document.getElementById("articleDots");
    let active = 0;
    let positions = [];
    const start = () => cards[0].offsetLeft;
    function measure() {
      const maximum = track.scrollWidth - track.clientWidth;
      positions = [
        ...new Set(
          cards.map((card) => Math.min(card.offsetLeft - start(), maximum)),
        ),
      ];
      dots.replaceChildren(
        ...positions.map((position, index) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "carousel-dot";
          button.dataset.test = "carousel-dot";
          button.setAttribute("aria-label", `查看第 ${index + 1} 篇起的文章`);
          button.addEventListener("click", () =>
            track.scrollTo({ left: position, behavior: motion() }),
          );
          return button;
        }),
      );
      reflectCarousel();
    }
    function reflectCarousel() {
      active = positions.reduce(
        (nearest, value, index) =>
          Math.abs(value - track.scrollLeft) <
          Math.abs(positions[nearest] - track.scrollLeft)
            ? index
            : nearest,
        0,
      );
      cards.forEach((card, index) => {
        card.dataset.active = String(index === active);
      });
      [...dots.children].forEach((dot, index) => {
        if (index === active) dot.setAttribute("aria-current", "true");
        else dot.removeAttribute("aria-current");
      });
      previous.disabled = active === 0;
      next.disabled = active === positions.length - 1;
      const shown = Math.max(
        1,
        Math.round((track.clientWidth + 16) / (cards[0].offsetWidth + 16)),
      );
      document.getElementById("articlePosition").textContent =
        `${active + 1}${shown > 1 ? `–${Math.min(cards.length, active + shown)}` : ""} / ${cards.length}`;
    }
    function move(delta) {
      const target = Math.max(
        0,
        Math.min(positions.length - 1, active + delta),
      );
      track.scrollTo({ left: positions[target], behavior: motion() });
    }
    previous.addEventListener("click", () => move(-1));
    next.addEventListener("click", () => move(1));
    track.addEventListener("keydown", (event) => {
      if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
        event.preventDefault();
        move(event.key === "ArrowRight" ? 1 : -1);
      }
    });
    track.addEventListener("scroll", reflectCarousel, { passive: true });
    new ResizeObserver(measure).observe(track);
    let drag = null;
    let suppressClick = false;
    track.addEventListener("pointerdown", (event) => {
      if (event.pointerType !== "mouse" || event.button !== 0) return;
      drag = {
        x: event.clientX,
        left: track.scrollLeft,
        index: active,
        moved: false,
      };
    });
    track.addEventListener("pointermove", (event) => {
      if (!drag) return;
      const delta = event.clientX - drag.x;
      if (Math.abs(delta) > 5) {
        if (!drag.moved) track.setPointerCapture(event.pointerId);
        drag.moved = true;
        track.style.scrollSnapType = "none";
        track.style.userSelect = "none";
        track.scrollLeft = drag.left - delta;
      }
    });
    function endDrag(event) {
      if (!drag) return;
      const moved = drag.moved;
      const delta = event.clientX - drag.x;
      const target = Math.max(
        0,
        Math.min(
          positions.length - 1,
          Math.abs(delta) > 40 ? drag.index + (delta < 0 ? 1 : -1) : active,
        ),
      );
      drag = null;
      if (track.hasPointerCapture(event.pointerId))
        track.releasePointerCapture(event.pointerId);
      track.style.scrollSnapType = "";
      track.style.userSelect = "";
      if (moved) {
        suppressClick = true;
        track.scrollTo({ left: positions[target], behavior: motion() });
        setTimeout(() => {
          suppressClick = false;
        }, 0);
      }
    }
    track.addEventListener("pointerup", endDrag);
    track.addEventListener("pointercancel", endDrag);
    track.addEventListener("pointerleave", (event) => {
      if (drag && !drag.moved) endDrag(event);
    });
    track.addEventListener(
      "click",
      (event) => {
        if (suppressClick) {
          event.preventDefault();
          event.stopPropagation();
        }
      },
      true,
    );
    track.addEventListener("dragstart", (event) => event.preventDefault());
    measure();
  }
  // Without JavaScript all newsletter links and category anchors remain usable.
  root.classList.add("js");
})();
