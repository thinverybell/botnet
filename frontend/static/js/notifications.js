window.toast = function (msg, ms) {
  ms = ms || 2800;
  var el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.classList.remove("hidden");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(function () { el.classList.add("hidden"); }, ms);
};
