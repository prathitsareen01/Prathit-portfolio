(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const canObserve = "IntersectionObserver" in window;

  if (canObserve && !reducedMotion.matches) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("show");
        revealObserver.unobserve(entry.target);
      });
    }, { threshold: 0.14 });
    document.querySelectorAll(".panel, .project-card, .experience-card, .timeline-card, .skill-block")
      .forEach((element) => {
        element.classList.add("reveal");
        revealObserver.observe(element);
      });
  }

  // Static copies of the final numbers remain available to screen readers.
  const counters = [...document.querySelectorAll("[data-count]")];
  const runningCounters = new Map();
  const formatCount = (element, value) => `${element.dataset.prefix || ""}${value}${element.dataset.suffix || ""}`;
  const finishCount = (element) => {
    const frame = runningCounters.get(element);
    if (frame !== undefined) cancelAnimationFrame(frame);
    runningCounters.delete(element);
    element.textContent = formatCount(element, Number(element.dataset.count));
    element.dataset.counted = "true";
  };
  const animateCount = (element) => {
    if (element.dataset.counted === "true") return;
    element.dataset.counted = "true";
    const target = Number(element.dataset.count);
    const start = performance.now();
    const tick = (now) => {
      if (reducedMotion.matches) return finishCount(element);
      const progress = Math.min(1, (now - start) / 1150);
      const eased = 1 - Math.pow(1 - progress, 3);
      element.textContent = formatCount(element, Math.floor(target * eased));
      if (progress < 1) runningCounters.set(element, requestAnimationFrame(tick));
      else finishCount(element);
    };
    element.textContent = formatCount(element, 0);
    runningCounters.set(element, requestAnimationFrame(tick));
  };
  if (canObserve && !reducedMotion.matches) {
    const countObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        animateCount(entry.target);
        countObserver.unobserve(entry.target);
      });
    }, { threshold: 0.6 });
    counters.forEach((element) => countObserver.observe(element));
  } else counters.forEach(finishCount);
  reducedMotion.addEventListener("change", () => {
    if (!reducedMotion.matches) return;
    counters.forEach(finishCount);
    document.querySelectorAll(".reveal").forEach((element) => element.classList.add("show"));
  });

  const progressFill = document.querySelector(".reading-progress-fill");
  let progressFrame = null;
  const updateProgress = () => {
    progressFrame = null;
    if (!progressFill) return;
    const page = document.scrollingElement || document.documentElement;
    const available = page.scrollHeight - page.clientHeight;
    const fraction = available > 0 ? Math.min(1, Math.max(0, page.scrollTop / available)) : 0;
    progressFill.style.transform = `scaleX(${fraction})`;
  };
  const scheduleProgress = () => {
    if (progressFrame === null) progressFrame = requestAnimationFrame(updateProgress);
  };
  window.addEventListener("scroll", scheduleProgress, { passive: true });
  window.addEventListener("resize", scheduleProgress);
  window.addEventListener("load", scheduleProgress);
  window.addEventListener("pageshow", scheduleProgress);
  if ("ResizeObserver" in window) new ResizeObserver(scheduleProgress).observe(document.body);
  updateProgress();

  // Hover reveals are also available through explicit touch and keyboard controls.
  const hoverPointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  document.querySelectorAll("[data-preview-card]").forEach((card) => {
    const controls = card.querySelector(".project-preview-controls");
    const toggle = card.querySelector(".preview-toggle");
    const panel = card.querySelector(".project-preview-panel");
    const previewLabel = card.dataset.previewLabel || "project";
    if (!controls || !toggle || !panel) return;
    controls.hidden = false;
    let pinned = false;
    let hovered = false;
    const setExpanded = (expanded) => {
      card.dataset.previewExpanded = String(expanded);
      toggle.setAttribute("aria-expanded", String(expanded));
      toggle.innerHTML = pinned
        ? 'Hide preview <span aria-hidden="true">−</span>'
        : expanded
          ? 'Keep preview open <span aria-hidden="true">+</span>'
          : `Preview ${previewLabel} <span aria-hidden="true">+</span>`;
      panel.setAttribute("aria-hidden", String(!expanded));
      panel.inert = !expanded;
      panel.toggleAttribute("inert", !expanded);
      scheduleProgress();
    };
    toggle.addEventListener("click", () => {
      pinned = !pinned;
      setExpanded(pinned);
    });
    card.addEventListener("pointerenter", () => {
      if (!hoverPointer.matches) return;
      hovered = true;
      setExpanded(true);
    });
    card.addEventListener("pointerleave", () => {
      hovered = false;
      if (!pinned && !panel.contains(document.activeElement)) setExpanded(false);
    });
    card.addEventListener("focusout", (event) => {
      if (!pinned && !hovered && !card.contains(event.relatedTarget)) setExpanded(false);
    });
  });

  document.querySelectorAll("[data-experience-card]").forEach((card) => {
    const toggle = card.querySelector(".experience-toggle");
    const details = card.querySelector(".experience-details");
    if (!toggle || !details) return;
    const setExpanded = (expanded) => {
      if (!expanded && details.contains(document.activeElement)) toggle.focus({ preventScroll: true });
      card.dataset.experienceExpanded = String(expanded);
      toggle.setAttribute("aria-expanded", String(expanded));
      details.setAttribute("aria-hidden", String(!expanded));
      details.inert = !expanded;
      details.toggleAttribute("inert", !expanded);
      scheduleProgress();
    };
    setExpanded(false);
    toggle.disabled = false;
    toggle.addEventListener("click", () => {
      setExpanded(toggle.getAttribute("aria-expanded") !== "true");
    });
  });

  const dialogs = [...document.querySelectorAll(".project-preview-dialog")];
  const returnFocus = new Map();
  document.querySelectorAll("[data-preview-open]").forEach((button) => {
    button.addEventListener("click", () => {
      const dialog = document.getElementById(button.dataset.previewOpen);
      if (!dialog) return;
      if (typeof dialog.showModal !== "function") {
        window.open(dialog.querySelector("a").href, "_blank", "noopener");
        return;
      }
      returnFocus.set(dialog, button);
      dialog.showModal();
      dialog.scrollTop = 0;
      document.body.classList.add("preview-dialog-open");
    });
  });
  dialogs.forEach((dialog) => {
    dialog.querySelector("[data-preview-close]").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    });
    dialog.addEventListener("close", () => {
      if (!dialogs.some((item) => item.open)) document.body.classList.remove("preview-dialog-open");
      const trigger = returnFocus.get(dialog);
      const focusTarget = trigger?.closest(".project-preview-panel")?.inert
        ? trigger.closest("[data-preview-card]").querySelector(".preview-toggle")
        : trigger;
      focusTarget?.focus({ preventScroll: true });
      returnFocus.delete(dialog);
      scheduleProgress();
    });
  });
})();

