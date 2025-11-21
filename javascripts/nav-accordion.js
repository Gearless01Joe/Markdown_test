document.addEventListener("DOMContentLoaded", () => {
  const primaryNav = document.querySelector(".md-nav--primary");
  if (!primaryNav) return;

  const toggles = primaryNav.querySelectorAll("input.md-nav__toggle");

  toggles.forEach((toggle) => {
    toggle.addEventListener("change", () => {
      if (!toggle.checked) return;

      const list = toggle.closest(".md-nav__item")?.parentElement;
      if (!list) return;

      Array.from(list.children)
        .map((item) => item.querySelector("input.md-nav__toggle"))
        .filter((input) => input && input !== toggle)
        .forEach((input) => {
          input.checked = false;
        });
    });
  });

  const nestedLinks = primaryNav.querySelectorAll(
    ".md-nav__item--nested > .md-nav__link"
  );

  nestedLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      const toggle = link.previousElementSibling;
      const isToggle =
        toggle && toggle.classList && toggle.classList.contains("md-nav__toggle");
      if (!isToggle) {
        return;
      }

      // Toggle open/close on click and prevent page jump
      toggle.checked = !toggle.checked;
      toggle.dispatchEvent(new Event("change", { bubbles: true }));
      event.preventDefault();
      event.stopPropagation();
    });
  });
});

