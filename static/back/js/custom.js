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

        input.addEventListener("input", () => {
            const value = input.value.toLowerCase();

            document.querySelectorAll(rowSelector).forEach(row => {

                row.style.display = row.innerText
                    .toLowerCase()
                    .includes(value)
                        ? "grid"
                        : "none";
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

    document.getElementById("category").addEventListener("change", function () {
        let categoryId = this.value;
        const csrfToken = getCSRFToken();

        fetch("/master/fetch-subcategories", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                category_id: categoryId
            })
        })
        .then(response => response.json())
        .then(data => {
            let subcategory = document.getElementById("subcategory");
            subcategory.innerHTML = '<option value="" hidden>Select Subcategory</option>';

            data.subcategories.forEach(function(item) {
                subcategory.innerHTML += `
                    <option value="${item.id}">
                        ${item.name}
                    </option>
                `;
            });
        });
    });

    document.getElementById("subcategory").addEventListener("change", function () {
        let subcategoryId = this.value;
        const csrfToken = getCSRFToken();

        fetch("/master/fetch-collections", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                subcategory_id: subcategoryId
            })
        })
        .then(response => response.json())
        .then(data => {
            let collection = document.getElementById("collection");
            collection.innerHTML = '<option value="" hidden>Select Collection</option>';

            data.collections.forEach(function(item) {
                collection.innerHTML += `
                    <option value="${item.id}">
                        ${item.name}
                    </option>
                `;
            });
        });
    });

    const searchInput=document.getElementById("productSearch");

    searchInput.addEventListener("keyup",()=>{
        const value=searchInput.value.toLowerCase();

        document
        .querySelectorAll(".product-item")
        .forEach(item=>{
            const text=item.innerText.toLowerCase();

            item.style.display=
            text.includes(value)
            ? "flex"
            : "none";
        });
    });
});

/* SELECT2 */
$(document).ready(function () {
    if ($('.select2').length) {
        $('.select2').select2({
            placeholder: 'Select Tags',
            allowClear: true,
            width: '100%'
        });
    }
});