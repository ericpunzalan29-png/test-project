(function () {
  "use strict";

  document.getElementById("year").textContent = new Date().getFullYear();

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Sticky header state + scroll progress bar */
  var header = document.getElementById("siteHeader");
  var progressBar = document.getElementById("progressBar");

  function updateProgress() {
    var doc = document.documentElement;
    var scrollTop = doc.scrollTop || document.body.scrollTop;
    var height = doc.scrollHeight - doc.clientHeight;
    var pct = height > 0 ? (scrollTop / height) * 100 : 0;
    progressBar.style.width = pct + "%";
  }

  var onScroll = function () {
    header.classList.toggle("is-scrolled", window.scrollY > 12);
    updateProgress();
  };
  document.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* Mobile nav toggle */
  var navToggle = document.getElementById("navToggle");
  var mainNav = document.getElementById("mainNav");
  navToggle.addEventListener("click", function () {
    var isOpen = mainNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });
  mainNav.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      mainNav.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
    });
  });

  /* Hero: mouse + scroll parallax on the aurora field, cursor spotlight */
  var heroSection = document.querySelector(".hero");
  var heroField = document.getElementById("heroField");
  var heroSpotlight = document.getElementById("heroSpotlight");
  var heroMx = 0, heroMy = 0;

  function applyHeroTransform() {
    var scrollShift = reducedMotion ? 0 : window.scrollY * 0.12;
    heroField.style.transform =
      "translate(" + heroMx + "px, " + (heroMy - scrollShift) + "px)";
  }

  if (heroSection && !reducedMotion) {
    heroSection.addEventListener("mousemove", function (e) {
      var rect = heroSection.getBoundingClientRect();
      var relX = (e.clientX - rect.left) / rect.width - 0.5;
      var relY = (e.clientY - rect.top) / rect.height - 0.5;
      heroMx = relX * 26;
      heroMy = relY * 20;
      applyHeroTransform();
      heroSpotlight.style.setProperty("--sx", (relX + 0.5) * 100 + "%");
      heroSpotlight.style.setProperty("--sy", (relY + 0.5) * 100 + "%");
    });
    heroSection.addEventListener("mouseleave", function () {
      heroMx = 0; heroMy = 0;
      applyHeroTransform();
    });
    document.addEventListener("scroll", applyHeroTransform, { passive: true });
  }

  /* About visual: gentle scroll-linked drift on the floating cards */
  var visualCards = document.querySelectorAll(".about-visual .visual-card");
  var aboutVisual = document.querySelector(".about-visual");
  if (aboutVisual && visualCards.length && !reducedMotion) {
    var updateVisualParallax = function () {
      var rect = aboutVisual.getBoundingClientRect();
      var progress = (window.innerHeight - rect.top) / (window.innerHeight + rect.height);
      var shift = (progress - 0.5) * 30;
      visualCards.forEach(function (card, i) {
        var factor = i === 0 ? 1 : -1;
        card.style.transform = "translateY(" + (shift * factor) + "px)";
      });
    };
    document.addEventListener("scroll", updateVisualParallax, { passive: true });
    updateVisualParallax();
  }

  /* Card tilt: service + testimonial cards tilt toward the cursor */
  if (!reducedMotion) {
    var tiltCards = document.querySelectorAll(".service-card");
    tiltCards.forEach(function (card) {
      card.addEventListener("mousemove", function (e) {
        var rect = card.getBoundingClientRect();
        var relX = (e.clientX - rect.left) / rect.width - 0.5;
        var relY = (e.clientY - rect.top) / rect.height - 0.5;
        card.style.transform =
          "perspective(900px) rotateX(" + (relY * -7) + "deg) rotateY(" + (relX * 9) + "deg) translateY(-4px)";
      });
      card.addEventListener("mouseleave", function () {
        card.style.transform = "perspective(900px)";
      });
    });
  }

  /* Scroll reveal */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach(function (el) { observer.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  }

  /* Animated stat counters, triggered once stats bar is visible */
  var statEls = document.querySelectorAll(".stat-num");
  function animateCount(el) {
    var target = parseInt(el.getAttribute("data-count"), 10) || 0;
    var duration = 1400;
    var start = null;

    function step(timestamp) {
      if (start === null) start = timestamp;
      var progress = Math.min((timestamp - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.floor(eased * target).toLocaleString();
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target.toLocaleString();
      }
    }
    requestAnimationFrame(step);
  }

  var statsBar = document.querySelector(".stats-bar");
  if (statsBar && "IntersectionObserver" in window) {
    var statsObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            statEls.forEach(animateCount);
            statsObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );
    statsObserver.observe(statsBar);
  } else {
    statEls.forEach(animateCount);
  }

  /* Contact form (front-end only — no backend wired up yet) */
  var form = document.getElementById("contactForm");
  var success = document.getElementById("formSuccess");
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    success.hidden = false;
    form.reset();
    success.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
})();
