'use strict';

document.addEventListener("DOMContentLoaded", () => {
  function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute("content") : "";
  }

  function showCartToast(message = "Product added to cart") {
    const toast = document.getElementById("cartToast");
    if (!toast) return;

    toast.querySelector("span").textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
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

            showCartToast("Product added to cart");

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

  const scrollBtn = document.getElementById("scrollTopBtn");

  window.addEventListener("scroll", () => {
    if (window.scrollY > 300) {
      scrollBtn.classList.add("show");
    } else {
      scrollBtn.classList.remove("show");
    }
  });

  scrollBtn.addEventListener("click", () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });
  });

  document.querySelectorAll(".bundle-carousel").forEach(carousel => {
    const track = carousel.querySelector(".bundle-track");
    const slides = carousel.querySelectorAll("img");

    const prev = carousel.querySelector(".bundle-prev");
    const next = carousel.querySelector(".bundle-next");
    const dotsContainer = carousel.querySelector(".bundle-dots");

    let index = 0;

    slides.forEach((_, i) => {
      const dot = document.createElement("button");
      if (i === 0) dot.classList.add("active");

      dot.addEventListener("click", () => {
        index = i;
        update();
      });

      dotsContainer.appendChild(dot);
    });

    const dots = dotsContainer.querySelectorAll("button");

    function update() {
      track.style.transform = `translateX(-${index * 100}%)`;

      dots.forEach(d => d.classList.remove("active"));
      dots[index].classList.add("active");
    }

    next.addEventListener("click", () => {
      index = (index + 1) % slides.length;
      update();
    });

    prev.addEventListener("click", () => {
      index = (index - 1 + slides.length) % slides.length;
      update();
    });
  });

  const addBundleButtons = document.querySelectorAll(".add-bundle-to-cart-btn");

  if (addBundleButtons.length) {
    addBundleButtons.forEach(button => {
      button.addEventListener("click", async () => {
        const slug = button.dataset.slug;
        if (!slug) return;

        const oldText = button.innerText;
        button.innerText = "Adding...";

        try {
          const response = await fetch(`/add-bundle-to-cart/${slug}`, {
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

            showCartToast(`Bundle added (${data.added_items} items)`);

            button.innerText = "Added";

            setTimeout(() => {
              button.innerText = oldText || "Buy Bundle";
            }, 1500);
          }

        } catch (error) {
          console.log(error);
          button.innerText = oldText || "Buy Bundle";
        }
      });
    });
  }

  document.querySelectorAll(".faq-question").forEach(q => {
    q.addEventListener("click", () => {
      const item = q.parentElement;
      const answer = item.querySelector(".faq-answer");

      const isOpen = item.classList.contains("active");

      if (isOpen) {
        // CLOSE (smooth collapse)
        answer.style.height = answer.scrollHeight + "px";

        requestAnimationFrame(() => {
          answer.style.height = "0px";
          item.classList.remove("active");
        });

      } else {
        // OPEN (smooth expand)
        answer.style.height = answer.scrollHeight + "px";

        item.classList.add("active");

        answer.addEventListener("transitionend", function handler() {
          if (item.classList.contains("active")) {
            answer.style.height = "auto";
          }
          answer.removeEventListener("transitionend", handler);
        });
      }
    });
  });

  const tabs = document.querySelectorAll(".faq-tabs .tab");
  const faqItems = document.querySelectorAll(".faq-item");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {

      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const category = tab.dataset.category;

      faqItems.forEach(item => {
        const itemCategory = item.dataset.category;

        if (category === "all" || itemCategory === category) {
          item.style.display = "block";
        } else {
          item.style.display = "none";
        }
      });

    });
  });

  const searchInput = document.getElementById("faqSearch");

  if(searchInput){
    searchInput.addEventListener("input", function () {
      const value = this.value.toLowerCase();

      faqItems.forEach(item => {
        const text = item.innerText.toLowerCase();

        if (text.includes(value)) {
          item.style.display = "block";
        } else {
          item.style.display = "none";
        }
      });
    });
  }

  const zoomables = document.querySelectorAll(".zoomable");

  if(zoomables){
    zoomables.forEach(img => {
      img.addEventListener("click", () => {
        const src = img.dataset.full;

        const modal = document.createElement("div");
        modal.classList.add("img-modal");

        modal.innerHTML = `
          <div class="img-modal-content">
            <img src="${src}">
            <span class="close">&times;</span>
          </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector(".close").onclick = () => modal.remove();
        modal.onclick = (e) => {
          if (e.target === modal) modal.remove();
        };
      });
    });
  }

  document.querySelectorAll(".vb-faq-question").forEach((button)=>{
    button.addEventListener("click",()=>{
        const item=button.parentElement;

        document.querySelectorAll(".vb-faq-item").forEach((faq)=>{
            if(faq!==item){
                faq.classList.remove("active");
            }
        });

        item.classList.toggle("active");
    });
  });

  
})