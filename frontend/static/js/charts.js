window.RyzenCharts = (function () {
  var chart = null;
  var labels = [];
  var bots = [];
  var proxies = [];
  function ensure() {
    var canvas = document.getElementById("chartActivity");
    if (!canvas || typeof Chart === "undefined") return null;
    if (chart) return chart;
    chart = new Chart(canvas.getContext("2d"), {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          { label: "Bots online", data: bots, borderColor: "#00e5ff", tension: 0.3, fill: false },
          { label: "Proxies alive", data: proxies, borderColor: "#00e676", tension: 0.3, fill: false }
        ]
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: "#8b9bb4" } } },
        scales: {
          x: { ticks: { color: "#8b9bb4" }, grid: { color: "#243049" } },
          y: { ticks: { color: "#8b9bb4" }, grid: { color: "#243049" } }
        }
      }
    });
    return chart;
  }
  function push(bOnline, pAlive) {
    var c = ensure();
    if (!c) return;
    var t = new Date().toLocaleTimeString();
    labels.push(t);
    bots.push(bOnline);
    proxies.push(pAlive);
    if (labels.length > 20) { labels.shift(); bots.shift(); proxies.shift(); }
    c.update();
  }
  return { push: push, ensure: ensure };
})();
