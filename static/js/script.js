/**
 * static/js/script.js
 * Single project script file. No inline <script> blocks or event handlers
 * live in the templates — every behavior is wired up here, scoped by
 * `data-*` attributes and element IDs so templates stay markup-only.
 */

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initMobileNav();
  initHeroTerminal();
  initMetricsChart();
});

/* --------------------------------------------------------------------------
 * Theme toggle (dark/light), persisted in localStorage
 * ------------------------------------------------------------------------ */
function initThemeToggle() {
  const STORAGE_KEY = "df-theme";
  const root = document.documentElement;
  const toggleButton = document.getElementById("theme-toggle");

  const savedTheme = localStorage.getItem(STORAGE_KEY) || "dark";
  root.setAttribute("data-theme", savedTheme);

  if (!toggleButton) return;

  toggleButton.addEventListener("click", () => {
    const nextTheme = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", nextTheme);
    localStorage.setItem(STORAGE_KEY, nextTheme);
  });
}

/* --------------------------------------------------------------------------
 * Mobile nav toggle
 * ------------------------------------------------------------------------ */
function initMobileNav() {
  const toggleButton = document.getElementById("mobile-nav-toggle");
  const nav = document.getElementById("mobile-nav");
  if (!toggleButton || !nav) return;

  toggleButton.addEventListener("click", () => {
    const isOpen = !nav.hidden;
    nav.hidden = isOpen;
    toggleButton.setAttribute("aria-expanded", String(!isOpen));
  });
}

/* --------------------------------------------------------------------------
 * Hero terminal typing animation (homepage signature element)
 * Respects prefers-reduced-motion: renders the final state instantly.
 * ------------------------------------------------------------------------ */
function initHeroTerminal() {
  const target = document.querySelector("[data-typing-target]");
  if (!target) return;

  const lines = [
    { html: '<span class="kw">$</span> scrapy_run --job=product-catalog --strategy=playwright' },
    { html: 'fetched <span class="str">1,204</span> pages in 8.4s' },
    { html: 'validating against schema&hellip; <span class="ok">1,198 valid</span> / 6 rejected' },
    { html: 'deduplicating&hellip; <span class="ok">1,061 unique records</span>' },
    { html: 'categorizing with AI&hellip; <span class="ok">done</span>' },
    { html: '<span class="kw">$</span> status: <span class="ok">ready for analysis</span>' },
  ];

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (prefersReducedMotion) {
    target.innerHTML = lines.map((line) => `<div>${line.html}</div>`).join("");
    return;
  }

  let lineIndex = 0;

  const renderNextLine = () => {
    if (lineIndex >= lines.length) {
      target.insertAdjacentHTML("beforeend", '<span class="df-caret"></span>');
      return;
    }

    const lineEl = document.createElement("div");
    lineEl.innerHTML = lines[lineIndex].html;
    target.appendChild(lineEl);
    lineIndex += 1;

    window.setTimeout(renderNextLine, 550);
  };

  renderNextLine();
}

/* --------------------------------------------------------------------------
 * Metrics chart (Chart.js), only initialized if the canvas exists on page
 * ------------------------------------------------------------------------ */
function initMetricsChart() {
  const canvas = document.getElementById("metrics-chart");
  if (!canvas || typeof Chart === "undefined") return;

  const styles = getComputedStyle(document.documentElement);
  const accentTeal = styles.getPropertyValue("--accent-teal").trim() || "#2dd4bf";
  const accentViolet = styles.getPropertyValue("--accent-violet").trim() || "#8b5cf6";
  const textMuted = styles.getPropertyValue("--text-muted").trim() || "#5d6b7a";

  const labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const recordsProcessed = [4200, 5100, 4800, 6300, 7100, 6800, 8200];

  new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Records processed",
          data: recordsProcessed,
          borderColor: accentTeal,
          backgroundColor: (context) => {
            const { ctx, chartArea } = context.chart;
            if (!chartArea) return "transparent";
            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            gradient.addColorStop(0, "rgba(45, 212, 191, 0.35)");
            gradient.addColorStop(1, "rgba(139, 92, 246, 0.02)");
            return gradient;
          },
          borderWidth: 2,
          tension: 0.35,
          fill: true,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: accentViolet,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: textMuted, font: { family: "Inter", size: 11 } },
        },
        y: {
          grid: { color: "rgba(255,255,255,0.06)" },
          ticks: { color: textMuted, font: { family: "Inter", size: 11 } },
        },
      },
    },
  });
}
