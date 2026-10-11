(function () {
  var commands = [
    { name: "Go Dashboard", run: function () { nav("dashboard"); } },
    { name: "Go Bots", run: function () { nav("bots"); } },
    { name: "Go Attacks", run: function () { nav("attacks"); } },
    { name: "Go Proxies", run: function () { nav("proxies"); } },
    { name: "Go Methods", run: function () { nav("methods"); } },
    { name: "Go AI", run: function () { nav("ai"); } },
    { name: "Refresh data", run: function () { window.ryzenRefresh && window.ryzenRefresh(); } },
    { name: "Scrape proxies", run: function () { document.getElementById("btnScrape") && document.getElementById("btnScrape").click(); } },
    { name: "Simulate bots", run: function () { document.getElementById("btnSimBots") && document.getElementById("btnSimBots").click(); } },
    { name: "Toggle theme", run: function () { document.getElementById("btnTheme") && document.getElementById("btnTheme").click(); } }
  ];
  function nav(page) {
    var el = document.querySelector('.nav-item[data-page="' + page + '"]');
    if (el) el.click();
  }
  var palette = document.getElementById("palette");
  var input = document.getElementById("paletteInput");
  var list = document.getElementById("paletteList");
  var active = 0;
  function render(filter) {
    filter = (filter || "").toLowerCase();
    list.innerHTML = "";
    var items = commands.filter(function (c) { return c.name.toLowerCase().indexOf(filter) >= 0; });
    items.forEach(function (c, i) {
      var li = document.createElement("li");
      li.textContent = c.name;
      if (i === active) li.className = "active";
      li.onclick = function () { c.run(); close(); };
      list.appendChild(li);
    });
  }
  function open() {
    palette.classList.remove("hidden");
    input.value = "";
    active = 0;
    render("");
    input.focus();
  }
  function close() { palette.classList.add("hidden"); }
  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (palette.classList.contains("hidden")) open(); else close();
    }
    if (e.key === "Escape") close();
    if (e.key.toLowerCase() === "r" && !e.ctrlKey && document.activeElement.tagName !== "INPUT") {
      window.ryzenRefresh && window.ryzenRefresh();
    }
  });
  input && input.addEventListener("input", function () { active = 0; render(input.value); });
  input && input.addEventListener("keydown", function (e) {
    var items = list.querySelectorAll("li");
    if (e.key === "ArrowDown") { active = Math.min(active + 1, items.length - 1); render(input.value); e.preventDefault(); }
    if (e.key === "ArrowUp") { active = Math.max(active - 1, 0); render(input.value); e.preventDefault(); }
    if (e.key === "Enter" && items[active]) { items[active].click(); }
  });
})();
