window.I18N = {
  lang: localStorage.getItem("ryzen_lang") || "vi",
  dict: {
    vi: {
      dashboard: "Dashboard", bots: "Bots", attacks: "Tấn công", proxies: "Proxy",
      methods: "Methods", ai: "AI", logs: "Logs", settings: "Cài đặt",
      refresh: "Làm mới", launch: "Triển khai", scrape: "Scrape", online: "trực tuyến",
      offline: "ngoại tuyến", search_bots: "Lọc bot…", search_atk: "Lọc attack…",
      search_proxy: "Lọc proxy…", theme: "Giao diện", palette: "Gõ lệnh…"
    },
    en: {
      dashboard: "Dashboard", bots: "Bots", attacks: "Attacks", proxies: "Proxies",
      methods: "Methods", ai: "AI", logs: "Logs", settings: "Settings",
      refresh: "Refresh", launch: "Launch", scrape: "Scrape", online: "online",
      offline: "offline", search_bots: "Filter bots…", search_atk: "Filter attacks…",
      search_proxy: "Filter proxies…", theme: "Theme", palette: "Type a command…"
    }
  },
  t: function (k) {
    var d = this.dict[this.lang] || this.dict.vi;
    return d[k] || k;
  },
  set: function (lang) {
    this.lang = lang;
    localStorage.setItem("ryzen_lang", lang);
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      el.textContent = window.I18N.t(key);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      el.placeholder = window.I18N.t(el.getAttribute("data-i18n-placeholder"));
    });
  }
};
