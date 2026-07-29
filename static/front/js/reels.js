'use strict';

let page = 1;
let loading = false;
let hasNext = true;
let activePlatform = "all";

const feed = document.getElementById("reelsFeed");
const loader = document.getElementById("reelsLoader");

if (feed) {

    initFilters();
    loadReels();

    window.addEventListener(
        "scroll",
        handleInfiniteScroll
    );
}

/* =====================================
   FILTERS
===================================== */

function initFilters() {

    const filterButtons =
    document.querySelectorAll(
        ".ne-filters button"
    );

    if (!filterButtons.length) return;

    filterButtons.forEach(btn => {

        btn.addEventListener(
            "click",
            () => {

                if (
                    btn.dataset.platform === activePlatform
                ) {
                    return;
                }

                filterButtons.forEach(button => {
                    button.classList.remove("active");
                });

                btn.classList.add("active");

                activePlatform =
                btn.dataset.platform;

                page = 1;
                hasNext = true;

                feed.innerHTML = "";

                loadReels();
            }
        );
    });
}

/* =====================================
   LOAD REELS
===================================== */

async function loadReels() {

    if (loading || !hasNext) return;

    loading = true;

    if (loader) {
        loader.style.display = "block";
    }

    try {

        const response =
        await fetch(
            `/api/news-reels?page=${page}&platform=${activePlatform}`
        );

        const data =
        await response.json();

        if (
            page === 1 &&
            data.results.length === 0
        ) {

            feed.innerHTML = `
                <div class="ne-empty-state">
                    <i class="fa-regular fa-images"></i>
                    <h3>No updates found</h3>
                    <p>
                        No content available for this category yet.
                    </p>
                </div>
            `;

            hasNext = false;

            return;
        }

        data.results.forEach(
            item => renderReel(item)
        );

        hasNext = data.has_next;

        if (hasNext) {
            page++;
        }

    } catch(error) {

        console.error(
            "Failed to load reels:",
            error
        );

    } finally {

        loading = false;

        if (loader) {
            loader.style.display = "none";
        }
    }
}

/* =====================================
   RENDER CARD
===================================== */

function renderReel(item){

    const card =
    document.createElement("article");

    card.className = "ne-reel-card";

    card.dataset.id = item.id;

    card.innerHTML = `

        <div class="ne-reel-media">

            ${
                item.media_type === "video"

                ?

                `
                <video
                    class="reel-video"
                    muted
                    loop
                    playsinline
                    preload="metadata"
                >
                    <source src="${item.media_url}">
                </video>

                <div class="ne-video-icon">
                    <i class="fa-solid fa-play"></i>
                </div>
                `

                :

                `
                <img
                    src="${item.media_url}"
                    alt="${item.title}"
                    loading="lazy"
                >
                `
            }

            <span class="ne-platform-badge">
                ${item.platform}
            </span>

        </div>

        <div class="ne-reel-content">

            <h3>${item.title}</h3>

            ${
                item.description
                ?
                `<p>${item.description}</p>`
                :
                ''
            }

            <div class="ne-tag-row">

                ${
                    item.product_url
                    ?
                    `
                    <a
                    href="/product/${item.product_url}"
                    class="ne-product-tag">
                        View Product
                    </a>
                    `
                    :
                    ''
                }

                ${
                    item.bundle_url
                    ?
                    `
                    <a
                    href="/bundle/${item.bundle_url}"
                    class="ne-bundle-tag">
                        View Bundle
                    </a>
                    `
                    :
                    ''
                }

            </div>

            ${
                item.external_url
                ?
                `
                <a
                    href="${item.external_url}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="ne-view-btn">

                    View Original Post

                </a>
                `
                :
                ''
            }

        </div>
    `;

    feed.appendChild(card);

    observeReel(card);
}

/* =====================================
   VIDEO OBSERVER
===================================== */

const observer =
new IntersectionObserver(

    entries => {

        entries.forEach(entry => {

            const card =
            entry.target;

            const video =
            card.querySelector(
                ".reel-video"
            );

            if (
                entry.isIntersecting
            ) {

                if (video) {

                    video.play()
                    .catch(() => {});
                }

                if (
                    !card.dataset.tracked
                ) {

                    card.dataset.tracked =
                    "true";

                    trackView(
                        card.dataset.id
                    );
                }

            } else {

                if (video) {
                    video.pause();
                }
            }

        });

    },

    {
        threshold: 0.6
    }
);

function observeReel(card) {
    observer.observe(card);
}

/* =====================================
   TRACK VIEW
===================================== */

async function trackView(id){

    if (!id) return;

    try {

        await fetch(
            `/api/reel-view/${id}/`,
            {
                method: "POST",
                headers: {
                    "X-CSRFToken":
                    getCSRFToken()
                }
            }
        );

    } catch(error) {

        console.error(
            "Tracking failed:",
            error
        );
    }
}

/* =====================================
   INFINITE SCROLL
===================================== */

function handleInfiniteScroll(){

    if (
        loading ||
        !hasNext
    ) {
        return;
    }

    const triggerOffset = 600;

    if (

        window.innerHeight +
        window.scrollY

        >=

        document.body.offsetHeight -
        triggerOffset

    ) {

        loadReels();
    }
}