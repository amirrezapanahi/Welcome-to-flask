document.addEventListener("DOMContentLoaded", () => {
  const highlightButton = document.querySelector("[data-js='highlight']");
  const timestampButton = document.querySelector("[data-js='timestamp']");
  const container = document.querySelector("main");
  const timestampTarget = document.querySelector("[data-js='timestamp-value']");

  if (highlightButton) {
    highlightButton.addEventListener("click", () => {
      container.classList.toggle("highlighted");
    });
  }

  if (timestampButton) {
    timestampButton.addEventListener("click", () => {
      const now = new Date().toISOString().replace("T", " ").slice(0, 19) + "Z";
      timestampTarget.textContent = now;
    });
  }
});
