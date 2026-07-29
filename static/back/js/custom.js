'use strict';

document.addEventListener("DOMContentLoaded", () => {
    /* HELPERS */
    function makeSlug(text) {
        return text
            .toString()
            .toLowerCase()
            .trim()
            .replace(/&/g, "and")
            .replace(/['"]/g, "")
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "");
    }

    function getCSRFToken() {
        const token = document.querySelector(
            'meta[name="csrf-token"]'
        );

        return token ? token.getAttribute("content") : "";
    }

    /* AUTO HIDE ALERTS */
    setTimeout(() => {
        document.querySelectorAll(".alert").forEach(el => {
            el.style.opacity = "0";

            setTimeout(() => {
                el.remove();
            }, 300);
        });
    }, 3000);

    /* SLUGS */
    function setupSlug(nameId, slugId) {
        const nameInput = document.getElementById(nameId);
        const slugInput = document.getElementById(slugId);

        if (!nameInput || !slugInput) return;

        const originalSlug = slugInput.value.trim();

        let slugEdited = false;

        slugInput.addEventListener("input", () => {
            slugEdited = true;
            slugInput.value = makeSlug(slugInput.value);
        });

        nameInput.addEventListener("input", () => {

            const generatedFromCurrentName = makeSlug(nameInput.value);

            /*
                Allow auto-update when:
                1. slug is empty
                2. slug still equals original slug
                3. user never manually edited slug
            */

            if (
                !slugEdited ||
                slugInput.value.trim() === "" ||
                slugInput.value.trim() === originalSlug
            ) {
                slugInput.value = generatedFromCurrentName;
            }
        });
    }
    setupSlug("categoryName", "categorySlug");
    setupSlug("subcategoryName", "subcategorySlug");
    setupSlug("collectionName", "collectionSlug");
    setupSlug("productName", "productSlug");
    setupSlug("blogTitle", "blogSlug");

    /* REUSABLE IMAGE UPLOAD */
    function setupImageUpload({
        inputId,
        boxId,
        previewId,
        previewImgId,
        removeId
    }) {
        const input = document.getElementById(inputId);
        const box = document.getElementById(boxId);
        const preview = document.getElementById(previewId);
        const previewImg = document.getElementById(previewImgId);
        const removeBtn = document.getElementById(removeId);

        if (!input || !box || !preview || !previewImg) return;

        box.addEventListener("click", () => {
            input.click();
        });

        input.addEventListener("change", () => {
            const file = input.files[0];

            if (!file) return;

            const reader = new FileReader();

            reader.onload = (e) => {
                previewImg.src = e.target.result;
                preview.style.display = "block";
                box.style.display = "none";
            };

            reader.readAsDataURL(file);
        });

        if (removeBtn) {
            removeBtn.addEventListener("click", () => {
                input.value = "";
                previewImg.src = "";
                preview.style.display = "none";
                box.style.display = "block";
            });
        }
    }

    /* CATEGORY IMAGE */
    setupImageUpload({
        inputId: "categoryImageInput",
        boxId: "categoryImageBox",
        previewId: "categoryImagePreview",
        previewImgId: "categoryPreviewImg",
        removeId: "categoryImageRemove"
    });

    /* SUBCATEGORY IMAGE */
    setupImageUpload({
        inputId: "subcategoryImageInput",
        boxId: "subcategoryImageBox",
        previewId: "subcategoryImagePreview",
        previewImgId: "subcategoryPreviewImg",
        removeId: "subcategoryImageRemove"
    });

    /* COLLECTION IMAGE */
    setupImageUpload({
        inputId: "collectionImageInput",
        boxId: "collectionImageBox",
        previewId: "collectionImagePreview",
        previewImgId: "collectionPreviewImg",
        removeId: "collectionImageRemove"
    });

    /* PRODUCT MULTI IMAGE UPLOAD */
    const productInput = document.getElementById("productImages");
    const productBox = document.getElementById("productUploadBox");
    const productPreview = document.getElementById("multiImagePreview");

    if (productInput && productBox && productPreview) {
        productBox.addEventListener("click", () => {
            productInput.click();
        });

        productInput.addEventListener("change", () => {
            productPreview.innerHTML = "";

            Array.from(productInput.files).forEach((file, index) => {
                if (!file.type.startsWith("image/")) return;

                const reader = new FileReader();

                reader.onload = (e) => {
                    const item = document.createElement("div");

                    item.className = "product-preview-item";

                    item.innerHTML = `
                        <img src="${e.target.result}" alt="Preview">

                        <input type="text"
                               name="alt_text[]"
                               placeholder="Alt text">

                        <label>
                            <input type="radio"
                                   name="primary_image"
                                   value="${index}"
                                   ${index === 0 ? "checked" : ""}>
                            Primary
                        </label>
                    `;

                    productPreview.appendChild(item);
                };

                reader.readAsDataURL(file);
            });
        });
    }

    /* PRODUCT ATTRIBUTES */
    const addAttributeBtn = document.getElementById("addAttributeBtn");
    const attributeWrapper = document.getElementById("attributeWrapper");

    if (addAttributeBtn && attributeWrapper) {
        addAttributeBtn.addEventListener("click", () => {
            const row = document.createElement("div");
            row.className = "attribute-row";

            row.innerHTML = `
                <input type="hidden"
                       name="attribute_id[]"
                       value="">

                <input type="text"
                       name="attribute_name[]"
                       placeholder="Attribute name">

                <input type="text"
                       name="attribute_value[]"
                       placeholder="Value">
            `;

            attributeWrapper.appendChild(row);
        });
    }

    /* DELETE MODAL */
    const deleteModal = document.getElementById("deleteModal");
    const cancelDeleteBtn = document.getElementById("cancelDelete");
    const deleteIdInput = document.getElementById("deleteCategoryId");
    const deleteText = document.getElementById("deleteText");

    if (deleteModal && deleteIdInput) {
        document.querySelectorAll(".btn-delete").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();

                const id = btn.dataset.id;
                const name = btn.dataset.name || "this item";
                deleteIdInput.value = id;

                if (deleteText) {
                    deleteText.innerText =
                        `Delete "${name}"? This action cannot be undone.`;
                }

                deleteModal.style.display = "flex";
            });
        });

        if (cancelDeleteBtn) {
            cancelDeleteBtn.addEventListener("click", () => {
                deleteModal.style.display = "none";
            });
        }
    }

    /* SEARCH FILTERS */
    function setupSearch(inputId, rowSelector) {
        const input = document.getElementById(inputId);

        if (!input) return;

        const rows = document.querySelectorAll(rowSelector);

        input.addEventListener("input", () => {
            const value = input.value.toLowerCase().trim();

            rows.forEach(row => {
                const matched = row.textContent
                    .toLowerCase()
                    .includes(value);

                row.style.display = matched ? "" : "none";
            });
        });
    }

    setupSearch("categorySearch", ".category-row");
    setupSearch("subcategorySearch", ".subcategory-row");
    setupSearch("collectionSearch", ".collection-row");
    setupSearch("productSearch", ".product-row");
    setupSearch("orderSearch", ".order-row");
    setupSearch("customerSearch", ".customer-row");
    setupSearch("reviewSearch", ".review-row");
    setupSearch("inquirySearch", ".inquiry-row");
    setupSearch("subscriberSearch", ".subscriber-row");
    setupSearch("blogCategorySearch", ".blog-category-row");
    setupSearch("blogSearch", ".blog-row");
    setupSearch("keywordSearch", ".keywords-row");
    setupSearch("faqSearch", ".faq-row");
    setupSearch("bundleSearch", ".bundle-row");
    setupSearch("mediaSearch", ".media-row");
    setupSearch("ticketSearch", ".ticket-row");

    const categorySelect = document.getElementById("category");

    if (categorySelect) {
        categorySelect.addEventListener("change", function () {
            let categoryId = this.value;
            const csrfToken = getCSRFToken();

            fetch("/master/fetch-subcategories", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ category_id: categoryId })
            })
            .then(response => response.json())
            .then(data => {
                let subcategory = document.getElementById("subcategory");
                if (!subcategory) return;

                subcategory.innerHTML = '<option value="" hidden>Select Subcategory</option>';

                data.subcategories.forEach(function(item) {
                    subcategory.innerHTML += `<option value="${item.id}">${item.name}</option>`;
                });
            });
        });
    }

    const subcategorySelect = document.getElementById("subcategory");

    if (subcategorySelect) {
        subcategorySelect.addEventListener("change", function () {
            const subcategoryId = this.value;
            const csrfToken = getCSRFToken();

            fetch("/master/fetch-collections", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ subcategory_id: subcategoryId })
            })
            .then(response => response.json())
            .then(data => {
                const collection = document.getElementById("collection");
                if (!collection) return;

                collection.innerHTML = '<option value="" hidden>Select Collection</option>';

                data.collections.forEach(item => {
                    collection.innerHTML += `<option value="${item.id}">${item.name}</option>`;
                });
            });
        });
    }

    const productSearch = document.getElementById("productSearch");

    if (productSearch) {
        productSearch.addEventListener("input", function () {
            const value = this.value.toLowerCase().trim();

            document.querySelectorAll(".product-row").forEach(function (row) {
                const text = row.textContent.toLowerCase();

                row.style.display = text.includes(value)
                    ? "grid"
                    : "none";
            });
        });
    }

    const notificationPage = document.querySelector(".notification-page");

    if (notificationPage) {

        const searchInput = document.getElementById("notificationSearch");
        const channelFilter = document.getElementById("channelFilter");
        const statusFilter = document.getElementById("statusFilter");
        const eventFilter = document.getElementById("eventFilter");
        const resetBtn = document.getElementById("resetNotificationFilters");
        const rows = document.querySelectorAll(".notification-row");
        const visibleCount = document.getElementById("visibleCount");

        function filterNotifications() {
            const searchValue = searchInput?.value.toLowerCase().trim() || "";
            const channelValue = channelFilter?.value || "";
            const statusValue = statusFilter?.value || "";
            const eventValue = eventFilter?.value || "";

            let count = 0;

            rows.forEach(function (row) {
                const searchData = row.dataset.search.toLowerCase();
                const channelData = row.dataset.channel;
                const statusData = row.dataset.status;
                const eventData = row.dataset.event;

                const searchMatch = !searchValue || searchData.includes(searchValue);
                const channelMatch = !channelValue || channelData === channelValue;
                const statusMatch = !statusValue || statusData === statusValue;
                const eventMatch = !eventValue || eventData === eventValue;

                if (
                    searchMatch &&
                    channelMatch &&
                    statusMatch &&
                    eventMatch
                ) {
                    row.style.display = "grid";
                    count++;
                } else {
                    row.style.display = "none";
                }
            });

            if (visibleCount) {
                visibleCount.textContent = count;
            }
        }

        [searchInput, channelFilter, statusFilter, eventFilter].forEach(function (el) {
            if (!el) return;

            el.addEventListener("input", filterNotifications);
            el.addEventListener("change", filterNotifications);
        });

        if (resetBtn) {
            resetBtn.addEventListener("click", function () {
                searchInput.value = "";
                channelFilter.value = "";
                statusFilter.value = "";
                eventFilter.value = "";
                filterNotifications();
            });
        }

        const modal = document.getElementById("notificationResponseModal");
        const modalText = document.getElementById("notificationResponseText");
        const closeModal = document.querySelector(".notification-modal-close");

        document.querySelectorAll(".response-toggle").forEach(function (btn) {
            btn.addEventListener("click", function () {
                modalText.textContent = this.dataset.response;
                modal.classList.add("show");
            });
        });

        if (closeModal) {
            closeModal.addEventListener("click", function () {
                modal.classList.remove("show");
            });
        }

        if (modal) {
            modal.addEventListener("click", function (e) {
                if (e.target === modal) {
                    modal.classList.remove("show");
                }
            });
        }
    }

    const exportTables = document.querySelectorAll(".report-export-table");

    if (exportTables.length) {
        function getTableData(table) {
            const rows = [];
            const head = table.querySelector(".table-head");
            const bodyRows = table.querySelectorAll(".table-row");

            if (head) {
                rows.push(
                    Array.from(head.children).map(cell => cell.innerText.trim())
                );
            }

            bodyRows.forEach(row => {
                if (row.style.display === "none") return;

                rows.push(
                    Array.from(row.children).map(cell =>
                        cell.innerText.replace(/\s+/g, " ").trim()
                    )
                );
            });

            return rows;
        }

        function downloadFile(content, filename, type) {
            const blob = new Blob([content], { type });
            const link = document.createElement("a");

            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();

            URL.revokeObjectURL(link.href);
        }

        function exportCSV(table) {
            const rows = getTableData(table);

            const csv = rows.map(row =>
                row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(",")
            ).join("\n");

            downloadFile(csv, "vedabrass-report.csv", "text/csv;charset=utf-8;");
        }

        function exportExcel(table) {
            const rows = getTableData(table);

            const html = `
                <table>
                    ${rows.map(row =>
                        `<tr>${row.map(cell => `<td>${cell}</td>`).join("")}</tr>`
                    ).join("")}
                </table>
            `;

            downloadFile(
                html,
                "vedabrass-report.xls",
                "application/vnd.ms-excel"
            );
        }

        function copyTable(table) {
            const rows = getTableData(table);
            const text = rows.map(row => row.join("\t")).join("\n");

            navigator.clipboard.writeText(text).then(() => {
                alert("Report copied successfully.");
            });
        }

        function printTable(table) {
            const rows = getTableData(table);

            const html = `
                <html>
                <head>
                    <title>Vedabrass Report</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 30px; }
                        table { width: 100%; border-collapse: collapse; }
                        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
                        th { background: #442d1c; color: #fff; }
                    </style>
                </head>
                <body>
                    <h2>Vedabrass Report</h2>
                    <table>
                        ${rows.map((row, index) =>
                            `<tr>${row.map(cell =>
                                index === 0 ? `<th>${cell}</th>` : `<td>${cell}</td>`
                            ).join("")}</tr>`
                        ).join("")}
                    </table>
                </body>
                </html>
            `;

            const printWindow = window.open("", "_blank");
            printWindow.document.write(html);
            printWindow.document.close();
            printWindow.print();
        }

        document.querySelectorAll(".export-btn").forEach(button => {
            button.addEventListener("click", function () {
                const card = this.closest(".dashboard-card");
                if (!card) return;

                const table = card.querySelector(".report-export-table");
                if (!table) return;

                const type = this.dataset.export;

                if (type === "csv") exportCSV(table);
                if (type === "excel") exportExcel(table);
                if (type === "copy") copyTable(table);
                if (type === "print") printTable(table);
            });
        });
    }

    const collectionProductsPage = document.querySelector(".collection-products-page");

    if (collectionProductsPage) {
        const adminProductSearch = collectionProductsPage.querySelector("#adminProductSearch");
        const adminProductItems = collectionProductsPage.querySelectorAll(".product-item");

        if (adminProductSearch && adminProductItems.length) {
            adminProductSearch.addEventListener("input", function () {
                const searchValue = this.value.toLowerCase().trim();

                adminProductItems.forEach(function (item) {
                    const searchableText = item.textContent.toLowerCase();

                    item.style.display = searchableText.includes(searchValue)
                        ? "flex"
                        : "none";
                });
            });
        }
    }

    const product = document.querySelector('[name="product"]');
    const bundle = document.querySelector('[name="bundle"]');

    if(product){
        product.addEventListener("change", () => {
            if (product.value) {
                bundle.value = "";
            }
        });
    }
    
    if(bundle){
        bundle.addEventListener("change", () => {
            if (bundle.value) {
                product.value = "";
            }
        });
    }

    const customer = document.getElementById("customerSelect");
    const order = document.getElementById("orderSelect");

    if(customer){
        function filterOrders() {
            const customerId = customer.value;

            Array.from(order.options).forEach(option => {
                if (!option.value) return;

                option.hidden =
                    option.dataset.customer &&
                    option.dataset.customer !== customerId;
            });
        }

        filterOrders();
        
        customer.addEventListener("change", () => {
            filterOrders();
            order.value = "";
        });
    }

    const search = document.getElementById("adminProductSearch");
    const count = document.getElementById("selectedProductsCount");
    const clear = document.getElementById("clearSelectedProducts");

    const items = document.querySelectorAll(".product-picker-item");

    function updateCount() {
        const checked = document.querySelectorAll(
            '.product-picker-item input[type="checkbox"]:checked'
        ).length;

        count.textContent = checked;

        if (clear) {
            clear.disabled = checked === 0;
        }
    }

    if (search) {
        search.addEventListener("keyup", function () {
            const value = this.value.trim().toLowerCase();

            items.forEach(item => {
                const text = item.textContent.toLowerCase();

                item.style.display =
                    text.includes(value)
                        ? "grid"
                        : "none";
            });
        });
    }

    items.forEach(item => {
        const checkbox = item.querySelector(
            'input[type="checkbox"]'
        );

        checkbox.addEventListener(
            "change",
            updateCount
        );
    });

    if (clear) {
        clear.addEventListener("click", function () {
            items.forEach(item => {
                item.querySelector(
                    'input[type="checkbox"]'
                ).checked = false;
            });

            updateCount();
        });
    }

    updateCount();

    function initBundlePicker(){
        const search = document.getElementById("adminBundleSearch");

        const items = document.querySelectorAll(".bundle-picker-item");
        const radios = document.querySelectorAll(
            '.bundle-picker-item input[type="radio"]'
        );

        if(search){
            search.addEventListener("input",function(){
                const value=this.value.toLowerCase();

                items.forEach(item=>{
                    item.style.display =
                        item.innerText.toLowerCase().includes(value)
                        ? "grid"
                        : "none";
                });
            });
        }

        update();
    }

    initBundlePicker();

    
});

/* SELECT2 */
$(document).ready(function () {
    if ($('.select2').length) {
        $('.select2').select2({
            placeholder: 'Select From Options',
            allowClear: true,
            width: '100%'
        });
    }
});

