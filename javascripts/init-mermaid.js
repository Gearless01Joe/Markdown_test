document.addEventListener("DOMContentLoaded", () => {
  if (window.mermaid) {
    window.mermaid.initialize({
      startOnLoad: true,
      securityLevel: "loose",
      theme: "neutral"
    });
  }
});

