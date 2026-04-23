const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("show");
      }
    });
  },
  {
    threshold: 0.14,
  }
);

document
  .querySelectorAll(".panel, .project-card, .experience-card, .timeline-card, .skill-block")
  .forEach((el) => {
    el.classList.add("reveal");
    observer.observe(el);
  });
