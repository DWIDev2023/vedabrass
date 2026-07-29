'use strict';

document.addEventListener("DOMContentLoaded", function () {
    const chatbotToggle = document.getElementById("chatbotToggle");
    const chatbotBox = document.getElementById("chatbotBox");
    const chatbotClose = document.getElementById("chatbotClose");
    const chatbotSend = document.getElementById("chatbotSend");
    const chatbotInput = document.getElementById("chatbotInput");
    const chatbotMessages = document.getElementById("chatbotMessages");
    const typingIndicator = document.getElementById("typingIndicator");

    if (!chatbotToggle || !chatbotBox || !chatbotSend || !chatbotInput || !chatbotMessages) {
        return;
    }

    const CHATBOT_OPEN_KEY = "vedabrass_chatbot_opened_once";

    setTimeout(function () {
        if (!localStorage.getItem(CHATBOT_OPEN_KEY)) {
            chatbotBox.classList.add("active");
            localStorage.setItem(CHATBOT_OPEN_KEY, "yes");
        }
    }, 1500);

    chatbotToggle.addEventListener("click", function () {
        chatbotBox.classList.toggle("active");
    });

    if (chatbotClose) {
        chatbotClose.addEventListener("click", function () {
            chatbotBox.classList.remove("active");
        });
    }

    function escapeHTML(text) {
        const div = document.createElement("div");
        div.textContent = text || "";
        return div.innerHTML;
    }

    function scrollChat() {
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    function removeOldQuickReplies() {
        chatbotMessages
            .querySelectorAll(".chatbot-dynamic-replies")
            .forEach(function (el) {
                el.remove();
            });
    }

    function appendUserMessage(message) {
        chatbotMessages.insertAdjacentHTML(
            "beforeend",
            `<div class="user-message">${escapeHTML(message)}</div>`
        );

        scrollChat();
    }

    function appendBotMessage(message) {
        chatbotMessages.insertAdjacentHTML(
            "beforeend",
            `<div class="bot-message">${escapeHTML(message)}</div>`
        );

        scrollChat();
    }

    function appendLinks(links) {
        if (!links || !links.length) return;

        let html = `<div class="chatbot-action-links">`;

        links.forEach(function (link) {
            html += `
                <a href="${escapeHTML(link.url)}" target="_blank" rel="noopener noreferrer">
                    ${escapeHTML(link.label)}
                </a>
            `;
        });

        html += `</div>`;

        chatbotMessages.insertAdjacentHTML("beforeend", html);
        scrollChat();
    }

    function appendQuickReplies(replies) {
        if (!replies || !replies.length) return;

        let html = `<div class="chatbot-quick-replies chatbot-dynamic-replies">`;

        replies.forEach(function (reply) {
            html += `
                <button
                    type="button"
                    class="quick-reply-btn"
                    data-message="${escapeHTML(reply.message)}">
                    ${escapeHTML(reply.label)}
                </button>
            `;
        });

        html += `</div>`;

        chatbotMessages.insertAdjacentHTML("beforeend", html);
        scrollChat();
    }

    function appendProducts(products) {
        if (!products || !products.length) return;

        let html = `<div class="chatbot-products">`;

        products.forEach(function (product) {
            html += `
                <a href="${escapeHTML(product.url)}" class="chatbot-product-card" target="_blank" rel="noopener noreferrer">
                    ${
                        product.image
                            ? `<img src="${escapeHTML(product.image)}" alt="${escapeHTML(product.name)}">`
                            : ""
                    }
                    <div>
                        <strong>${escapeHTML(product.name)}</strong>
                        <span>₹${escapeHTML(product.price)}</span>
                    </div>
                </a>
            `;
        });

        html += `</div>`;

        chatbotMessages.insertAdjacentHTML("beforeend", html);
        scrollChat();
    }

    function showTyping() {
        if (typingIndicator) {
            typingIndicator.classList.add("show");
        }
    }

    function hideTyping() {
        if (typingIndicator) {
            typingIndicator.classList.remove("show");
        }
    }

    function sendMessage(customMessage = null) {
        const message = customMessage || chatbotInput.value.trim();

        if (!message) return;

        removeOldQuickReplies();
        appendUserMessage(message);

        chatbotInput.value = "";
        showTyping();

        fetch("/chatbot/reply/", {
            method: "POST",
            headers: {
                "X-CSRFToken":
                    document.querySelector("[name=csrfmiddlewaretoken]")?.value || ""
            },
            body: new URLSearchParams({
                message: message
            })
        })
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            hideTyping();

            appendBotMessage(data.reply);
            appendProducts(data.products);
            appendLinks(data.links);
            appendQuickReplies(data.quick_replies);
        })
        .catch(function () {
            hideTyping();

            appendBotMessage("Something went wrong. Please try again.");
            appendQuickReplies([
                { label: "Main Menu", message: "Main Menu" },
                { label: "Talk to Support", message: "Talk to Support" }
            ]);
        });
    }

    chatbotSend.addEventListener("click", function () {
        sendMessage();
    });

    chatbotInput.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });

    chatbotMessages.addEventListener("click", function (e) {
        const button = e.target.closest(".quick-reply-btn");

        if (!button) return;

        sendMessage(button.dataset.message);
    });

    
});