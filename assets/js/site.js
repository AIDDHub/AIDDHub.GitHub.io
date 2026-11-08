/* Small progressive enhancements: mobile nav, TOC scrollspy, copy buttons. */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var toggle = document.getElementById("navToggle");
    var links = document.getElementById("navLinks");
    if (toggle && links) {
      toggle.addEventListener("click", function () {
        var open = links.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      links.addEventListener("click", function (event) {
        if (event.target.closest("a")) links.classList.remove("open");
      });
    }

    var year = document.getElementById("year");
    if (year) year.textContent = String(new Date().getFullYear());

    /* Card filter: hides cards instead of paginating them. */
    var filters = document.getElementById("filters");
    var cards = document.querySelectorAll("#cards .card");
    if (filters && cards.length) {
      filters.addEventListener("click", function (event) {
        var button = event.target.closest("button[data-filter]");
        if (!button) return;
        var value = button.getAttribute("data-filter");
        var buttons = filters.querySelectorAll("button[data-filter]");
        for (var k = 0; k < buttons.length; k++) {
          buttons[k].setAttribute("aria-pressed", buttons[k] === button ? "true" : "false");
        }
        for (var c = 0; c < cards.length; c++) {
          var match = value === "all" || cards[c].getAttribute("data-product") === value;
          cards[c].style.display = match ? "" : "none";
        }
      });
    }

    /* Copy buttons on code blocks */
    var blocks = document.querySelectorAll(".article-body pre");
    for (var i = 0; i < blocks.length; i++) {
      (function (pre) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "copy-btn";
        button.textContent = "Copy";
        button.setAttribute("aria-label", "Copy code");
        button.addEventListener("click", function () {
          var text = pre.querySelector("code");
          var value = text ? text.innerText : pre.innerText;
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(value).then(function () {
              button.textContent = "Copied";
              setTimeout(function () { button.textContent = "Copy"; }, 1600);
            });
          }
        });
        pre.appendChild(button);
      })(blocks[i]);
    }

    /* TOC scrollspy */
    var toc = document.querySelector(".toc");
    if (!toc || !("IntersectionObserver" in window)) return;
    var anchors = toc.querySelectorAll('a[href^="#"]');
    var map = {};
    for (var j = 0; j < anchors.length; j++) {
      var id = anchors[j].getAttribute("href").slice(1);
      var heading = document.getElementById(id);
      if (heading) map[id] = anchors[j];
    }
    var current = null;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var link = map[entry.target.id];
        if (!link) return;
        if (current) current.classList.remove("active");
        link.classList.add("active");
        current = link;
      });
    }, { rootMargin: "-88px 0px -70% 0px", threshold: 0 });
    Object.keys(map).forEach(function (id) {
      observer.observe(document.getElementById(id));
    });
  });
})();
