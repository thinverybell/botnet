window.RyzenTerm = {
  lines: [],
  mount: function (el) {
    this.el = el;
    this.println("RyzenC2 web terminal (lab)");
    this.println("Commands: help | stats | bots | proxies | clear");
  },
  println: function (s) {
    this.lines.push(s);
    if (this.lines.length > 200) this.lines.shift();
    if (this.el) this.el.textContent = this.lines.join("\n");
  },
  exec: async function (cmd, apiFn) {
    cmd = (cmd || "").trim();
    this.println("> " + cmd);
    if (cmd === "clear") { this.lines = []; this.println(""); return; }
    if (cmd === "help") {
      this.println("help, stats, bots, proxies, clear");
      return;
    }
    try {
      if (cmd === "stats") {
        var s = await apiFn("/api/v1/stats");
        this.println(JSON.stringify(s, null, 2));
      } else if (cmd === "bots") {
        var b = await apiFn("/api/v1/bots/stats");
        this.println(JSON.stringify(b, null, 2));
      } else if (cmd === "proxies") {
        var p = await apiFn("/api/v1/proxies/stats");
        this.println(JSON.stringify(p, null, 2));
      } else {
        this.println("unknown command");
      }
    } catch (e) {
      this.println("error: " + e);
    }
  }
};
