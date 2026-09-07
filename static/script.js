/* ============================================================
   RETAIN IQ — DECORATIVE EFFECTS (additive only)
   This script never reads/writes application state, never calls
   fetch, and never touches the IDs or functions used by the
   existing page scripts. It only adds visual polish.
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {

    /* ---------- 1. animated background blobs ---------- */
    if (!document.querySelector(".riq-bg")) {
      var bg = document.createElement("div");
      bg.className = "riq-bg";
      bg.setAttribute("aria-hidden", "true");
      bg.innerHTML =
        '<div class="riq-blob riq-blob-1"></div>' +
        '<div class="riq-blob riq-blob-2"></div>' +
        '<div class="riq-blob riq-blob-3"></div>';
      document.body.insertBefore(bg, document.body.firstChild);
    }

    /* ---------- 2. scroll reveal for cards/panels ---------- */
    var revealSelectors = [
      ".card", ".summary-card", ".metric-card", ".info-box"
    ];
    var revealTargets = [];
    revealSelectors.forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        if (revealTargets.indexOf(el) === -1) revealTargets.push(el);
      });
    });

    if ("IntersectionObserver" in window && revealTargets.length) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("riq-in");
            io.unobserve(entry.target);
          }
        });
      }, { threshold: 0.08 });

      revealTargets.forEach(function (el, i) {
        el.classList.add("riq-reveal");
        el.style.animationDelay = (i % 6) * 0.06 + "s";
        io.observe(el);
      });
    }

    /* ---------- 3. button ripple (visual only) ---------- */
    document.addEventListener("click", function (e) {
      var btn = e.target.closest ? e.target.closest("button") : null;
      if (!btn || btn.disabled) return;

      var rect = btn.getBoundingClientRect();
      var size = Math.max(rect.width, rect.height);
      var ripple = document.createElement("span");
      ripple.className = "riq-ripple";
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = (e.clientX - rect.left - size / 2) + "px";
      ripple.style.top = (e.clientY - rect.top - size / 2) + "px";

      var computed = window.getComputedStyle(btn);
      if (computed.position === "static") {
        btn.style.position = "relative";
      }
      btn.style.overflow = "hidden";

      btn.appendChild(ripple);
      window.setTimeout(function () {
        if (ripple.parentNode) ripple.parentNode.removeChild(ripple);
      }, 650);
    }, true);

    /* ---------- 4. risk-label -> tint the nearest card (customer.html) ---------- */
    var riskLabel = document.getElementById("riskLabel");
    if (riskLabel) {
      var tintCard = function () {
        var card = riskLabel.closest(".card");
        if (!card) return;
        card.classList.remove("riq-tint-high", "riq-tint-medium", "riq-tint-low");
        if (riskLabel.classList.contains("high")) card.classList.add("riq-tint-high");
        else if (riskLabel.classList.contains("medium")) card.classList.add("riq-tint-medium");
        else if (riskLabel.classList.contains("low")) card.classList.add("riq-tint-low");
      };
      tintCard();
      new MutationObserver(tintCard).observe(riskLabel, { attributes: true, attributeFilter: ["class"] });
    }

    /* ---------- 5. password visibility toggle (login page only, additive) ---------- */
    var pwd = document.getElementById("password");
    if (pwd && pwd.parentNode && !document.getElementById("riqPwdToggle")) {
      var wrap = document.createElement("div");
      wrap.style.position = "relative";
      pwd.parentNode.insertBefore(wrap, pwd);
      wrap.appendChild(pwd);
      pwd.style.paddingRight = "42px";

      var toggle = document.createElement("button");
      toggle.type = "button";
      toggle.id = "riqPwdToggle";
      toggle.textContent = "Show";
      toggle.setAttribute("aria-label", "Toggle password visibility");
      toggle.style.cssText =
        "position:absolute;right:6px;top:50%;transform:translateY(-50%);" +
        "background:transparent;box-shadow:none;color:#6b7280;font-size:12px;" +
        "padding:6px 8px;border-radius:6px;";
      toggle.addEventListener("click", function () {
        var showing = pwd.type === "text";
        pwd.type = showing ? "password" : "text";
        toggle.textContent = showing ? "Show" : "Hide";
      });
      wrap.appendChild(toggle);
    }
  });
})();
