'use strict';

document.addEventListener("DOMContentLoaded", () => {
  function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute("content") : "";
  }
  
  /* NAVIGATION */
  window.toggleMenu = function () {
    document.getElementById("nav")?.classList.toggle("active");
  };

  /* SEARCH */
  const searchTrigger = document.getElementById("searchTrigger");
  const searchOverlay = document.getElementById("searchOverlay");

  searchTrigger?.addEventListener("click", () => {
      searchOverlay?.classList.add("active");
  });

  window.closeSearch = function () {
      searchOverlay?.classList.remove("active");
  };

  document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
          closeSearch();
      }
  });

  /* SUBNAV SCROLL */
  window.scrollSubnav = function (amount) {
    document.getElementById("subnav")?.scrollBy({
      left: amount,
      behavior: "smooth"
    });
  };

  /* MOBILE NAVIGATION */
  document.querySelectorAll('.nav-item > .nav-link').forEach(item => {
    item.addEventListener('click', function () {
      if (window.innerWidth > 1024) return;

      const parent = this.parentElement;

      document.querySelectorAll('.nav-item').forEach(el => {
        if (el !== parent) el.classList.remove('active');
      });

      parent.classList.toggle('active');
    });
  });

  document.querySelectorAll('.dropdown-item > .nav-link').forEach(item => {
    item.addEventListener('click', function (e) {
      if (window.innerWidth > 1024) return;

      e.preventDefault();

      const parent = this.parentElement;

      parent.parentElement.querySelectorAll('.dropdown-item').forEach(el => {
        if (el !== parent) el.classList.remove('active');
      });

      parent.classList.toggle('active');
      e.stopPropagation();
    });
  });

  /* CLICK OUTSIDE CLOSE */
  document.addEventListener("click", function (e) {
    if (window.innerWidth > 1024) return;

    const nav = document.getElementById("nav");
    const menuBtn = document.querySelector(".menu-btn");

    if (
      nav &&
      !nav.contains(e.target) &&
      !menuBtn?.contains(e.target)
    ) {
      nav.classList.remove("active");

      document.querySelectorAll(".nav-item, .dropdown-item")
        .forEach(el => el.classList.remove("active"));
    }
  });

  /* HERO SLIDER */
  let heroIndex = 0;

  const heroSlider = document.getElementById("heroSlider");
  const heroSlides = document.querySelectorAll(".hero .slide");
  const heroDotsContainer = document.getElementById("heroDots");

  if (heroSlider && heroSlides.length && heroDotsContainer) {
      
      heroSlides.forEach((_, i) => {
          const dot = document.createElement("span");

          dot.addEventListener("click", () => {
              goToHeroSlide(i);
          });

          heroDotsContainer.appendChild(dot);
      });

      const heroDots = heroDotsContainer.querySelectorAll("span");

      function updateHeroSlider() {
          heroSlider.style.transform = `translateX(-${heroIndex * 100}%)`;

          heroDots.forEach(dot => dot.classList.remove("active"));
          heroDots[heroIndex].classList.add("active");
      }

      window.moveSlide = function (step) {
          heroIndex = (heroIndex + step + heroSlides.length) % heroSlides.length;
          updateHeroSlider();
      };

      window.goToHeroSlide = function (i) {
          heroIndex = i;
          updateHeroSlider();
      };

      setInterval(() => {
          window.moveSlide(1);
      }, 5000);

      let startX = 0;

      heroSlider.addEventListener("touchstart", e => {
          startX = e.touches[0].clientX;
      });

      heroSlider.addEventListener("touchend", e => {
          const endX = e.changedTouches[0].clientX;

          if (startX - endX > 50) {
              window.moveSlide(1);
          }

          if (endX - startX > 50) {
              window.moveSlide(-1);
          }
      });

      updateHeroSlider();
  }

  /* CATEGORY SCROLL */
  function scrollCategory(amount) {
    document.getElementById('categoryScroll')?.scrollBy({
      left: amount,
      behavior: 'smooth'
    });
  }

  /* COUNTER ANIMATION */
  const counters = document.querySelectorAll('.stat h3');

  if (counters.length) {
    const counterObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;

        const counter = entry.target;
        const target = +counter.innerText.replace(/\D/g, '');
        let current = 0;
        const step = target / 80;

        const interval = setInterval(() => {
          current += step;

          if (current >= target) {
            counter.innerText = target.toLocaleString() + '+';
            clearInterval(interval);
          } else {
            counter.innerText = Math.floor(current).toLocaleString() + '+';
          }
        }, 20);

        counterObserver.unobserve(counter);
      });
    }, { threshold: 0.6 });

    counters.forEach(counter => counterObserver.observe(counter));
  }

  /* IMAGE PARALLAX */
  const imageWrapper = document.querySelector(".image-wrapper");

  function updateParallax() {
    if (!imageWrapper) return;

    const img = imageWrapper.querySelector("img");

    if (!img) return;

    const rect = imageWrapper.getBoundingClientRect();

    img.style.transform = `translateY(${rect.top * 0.15}px) scale(1.05)`;
  }


  /* PREMIUM TIMELINE */
  const specialSection = document.querySelector(".special-section");
  const timeline = document.querySelector(".timeline");
  const timelineItems = document.querySelectorAll(".timeline-item");
  const timelineCards = document.querySelectorAll(".timeline-card");

  /* PARTICLES */
  if (specialSection) {
    const particlesContainer = document.createElement("div");
    particlesContainer.classList.add("particles");
    specialSection.appendChild(particlesContainer);

    for (let i = 0; i < 50; i++) {
      const particle = document.createElement("span");
      const size = Math.random() * 6 + 2;

      particle.style.setProperty("--size", `${size}px`);
      particle.style.left = Math.random() * 100 + "%";
      particle.style.animationDuration = (10 + Math.random() * 12) + "s";
      particle.style.animationDelay = Math.random() * 5 + "s";
      particle.style.opacity = Math.random() * 0.4 + 0.2;

      const colors = [
        "rgba(80,60,30,0.8)",
        "rgba(40,30,15,0.6)",
        "rgba(212,175,55,0.6)"
      ];

      particle.style.background = `radial-gradient(circle, ${
        colors[Math.floor(Math.random() * colors.length)]
      }, transparent)`;

      particlesContainer.appendChild(particle);
    }
  }

  /* SCROLL REVEAL */
  if (timelineItems.length) {
    const revealObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("show");
        }
      });
    }, {
      threshold: 0.2
    });

    timelineItems.forEach(item => {
      revealObserver.observe(item);
    });
  }

  /* TIMELINE LINE */
  function updateTimelineLine() {
    if (!timeline) return;

    const rect = timeline.getBoundingClientRect();
    const windowHeight = window.innerHeight;

    let progress = (windowHeight - rect.top) / (rect.height + windowHeight);
    progress = Math.max(0, Math.min(1, progress));

    timeline.style.setProperty("--line-height", `${progress * 100}%`);
  }

  /* CARD INTERACTION */
  if (timelineCards.length) {
    timelineCards.forEach(card => {
      card.addEventListener("mousemove", e => {
        const rect = card.getBoundingClientRect();

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        card.style.setProperty("--x", `${x}px`);
        card.style.setProperty("--y", `${y}px`);

        timelineItems.forEach((item, i) => {
          let offset = 0;

          if (window.innerWidth > 1024) {
            offset = i % 2 === 0 ? -40 : 40;

            if (i % 3 === 0) {
              offset *= 1.5;
            }
          }

          item.style.setProperty("--offsetX", `${offset}px`);
        });
      });

      card.addEventListener("mouseleave", () => {
        card.style.transform =
          "perspective(800px) rotateX(0) rotateY(0) scale(1)";
      });
    });
  }

  /* CTA REVEAL */
  const cta = document.querySelector('.cta-container');

  if (cta) {
    const ctaObserver = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        cta.style.opacity = 1;
        cta.style.transform = "translateY(0)";
      }
    });

    cta.style.opacity = 0;
    cta.style.transform = "translateY(40px)";
    cta.style.transition = "all 0.8s ease";

    ctaObserver.observe(cta);
  }

  /* HOVER CARDS (LIGHT PARALLAX) */
  function attachHoverEffect(selector, intensity = 0.03) {
    const cards = document.querySelectorAll(selector);

    if (!cards.length) return;

    cards.forEach(card => {
      card.addEventListener("mousemove", e => {
        const rect = card.getBoundingClientRect();

        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;

        card.style.transform =
          `translate(${x * intensity}px, ${y * intensity}px) scale(1.02)`;
      });

      card.addEventListener("mouseleave", () => {
        card.style.transform = "";
      });
    });
  }

  attachHoverEffect('.insta-card', 0.05);
  attachHoverEffect('.testimonial-card', 0.03);

  /* GLOBAL SCROLL HANDLER */
  window.addEventListener('scroll', () => {
    /* NAVBAR */
    document.getElementById('navbar')
      ?.classList.toggle('shrink', window.scrollY > 50);

    updateTimelineLine();
    updateParallax();
  });

  const testimonialSlider = document.getElementById("testimonialSlider");
  const testimonialPrev = document.getElementById("testimonialPrev");
  const testimonialNext = document.getElementById("testimonialNext");

  if (testimonialSlider && testimonialPrev && testimonialNext) {
    const scrollAmount = 360;

    testimonialNext.addEventListener("click", () => {
      testimonialSlider.scrollBy({
        left: scrollAmount,
        behavior: "smooth"
      });
    });

    testimonialPrev.addEventListener("click", () => {
      testimonialSlider.scrollBy({
        left: -scrollAmount,
        behavior: "smooth"
      });
    });
  }

  const mainImage = document.querySelector(".main-product-img");
  const thumbnails = document.querySelectorAll(".thumb-gallery img");

  if (mainImage && thumbnails.length) {
    thumbnails.forEach(thumb => {
      thumb.addEventListener("click", () => {
        mainImage.src = thumb.src;

        thumbnails.forEach(img => {
          img.classList.remove("active");
        });

        thumb.classList.add("active");
      });
    });
  }

  const addToCartButtons = document.querySelectorAll(".add-to-cart-btn");

  if (addToCartButtons.length) {
    addToCartButtons.forEach(button => {
      button.addEventListener("click", async () => {
        const slug = button.dataset.slug;

        if (!slug) return;

        try {
          const response = await fetch(`/add-to-cart/${slug}`, {
            method: "POST",
            headers: {
              "X-CSRFToken": getCSRFToken(),
              "X-Requested-With": "XMLHttpRequest"
            }
          });

          const data = await response.json();

          if (data.success) {
            const cartCount = document.getElementById("cartCount");

            if (cartCount) {
              cartCount.innerText = data.cart_count;
            }

            const oldText = button.innerText;

            button.innerText = "Added";

            setTimeout(() => {
              button.innerText = oldText || "Add to Cart";
            }, 1500);
          }
        } catch (error) {
          console.log(error);
        }
      });
    });
  }

  function updateSummary(data) {
    const cartSubtotal = document.getElementById("cartSubtotal");
    const cartTotal = document.getElementById("cartTotal");
    const cartCount = document.getElementById("cartCount");

    if (cartSubtotal) {
      cartSubtotal.innerText = `₹${data.subtotal}`;
    }

    if (cartTotal) {
      cartTotal.innerText = `₹${data.total}`;
    }

    if (cartCount) {
      cartCount.innerText = data.cart_count;
    }
  }

  const cartButtons = document.querySelectorAll(".cart-plus, .cart-minus");

  if (cartButtons.length) {
    cartButtons.forEach(button => {
      button.addEventListener("click", async function () {
        const itemId = this.dataset.id;

        if (!itemId) return;

        const action = this.classList.contains("cart-plus")
          ? "plus"
          : "minus";

        const formData = new FormData();
        formData.append("action", action);

        try {
          const response = await fetch(`/update-cart/${itemId}`, {
            method: "POST",
            headers: {
              "X-CSRFToken": getCSRFToken()
            },
            body: formData
          });

          const data = await response.json();

          if (data.success) {
            const qtyInput = document.getElementById(`qty-${itemId}`);

            if (data.quantity <= 0) {
              this.closest(".cart-item")?.remove();
            } else if (qtyInput) {
              qtyInput.value = data.quantity;
            }

            updateSummary(data);
          }
        } catch (error) {
          console.log(error);
        }
      });
    });
  }

  const removeButtons = document.querySelectorAll(".cart-remove");

  if (removeButtons.length) {
    removeButtons.forEach(button => {
      button.addEventListener("click", async function () {
        const itemId = this.dataset.id;

        if (!itemId) return;

        try {
          const response = await fetch(`/remove-from-cart/${itemId}`, {
            method: "POST",
            headers: {
              "X-CSRFToken": getCSRFToken()
            }
          });

          const data = await response.json();

          if (data.success) {
            this.closest(".cart-item")?.remove();
            updateSummary(data);
          }
        } catch (error) {
          console.log(error);
        }
      });
    });
  }

  const sameAsBilling = document.getElementById("sameAsBilling");
  const shippingBox = document.getElementById("shippingAddressBox");

  if (sameAsBilling && shippingBox) {
    shippingBox.style.display = sameAsBilling.checked ? "none" : "block";

    sameAsBilling.addEventListener("change", function () {
      shippingBox.style.display = this.checked ? "none" : "block";
    });
  }

  
})