// Mobile nav toggle
const navToggle = document.getElementById("navToggle");
const nav = document.getElementById("nav");

navToggle.addEventListener("click", () => {
  const isOpen = nav.classList.toggle("is-open");
  navToggle.setAttribute("aria-expanded", String(isOpen));
});

nav.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    nav.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
  });
});

// Scroll reveal
const revealEls = document.querySelectorAll(".reveal");
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  },
  // Positive bottom margin so elements near the very end of the page
  // (which the viewport can never scroll fully past) still register.
  { threshold: 0, rootMargin: "0px 0px 200px 0px" }
);
revealEls.forEach((el) => observer.observe(el));

// Contact form (front-end only placeholder)
const form = document.getElementById("contactForm");
const status = document.getElementById("formStatus");

form.addEventListener("submit", (e) => {
  e.preventDefault();
  status.textContent = "Thanks! This form isn't connected to a backend yet — wire it up to your email or CRM to receive messages.";
  form.reset();
});

// Footer year
document.getElementById("year").textContent = new Date().getFullYear();
