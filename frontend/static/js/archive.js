let currentDays = 1;

document.addEventListener("DOMContentLoaded", () => {
    setupRangeButtons();
    setupFilters();
    loadArticles();
});

function setupRangeButtons() {
    document.querySelectorAll(".range-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".range-btn").forEach(b => {
                b.classList.remove("active", "bg-green-700", "text-white");
                b.classList.add("bg-slate-100", "text-slate-700");
            });
            btn.classList.add("active", "bg-green-700", "text-white");
            btn.classList.remove("bg-slate-100", "text-slate-700");
            currentDays = parseInt(btn.dataset.days);
            loadArticles();
        });
    });
}

function setupFilters() {
    document.getElementById("category-filter").addEventListener("change", loadArticles);
    document.getElementById("importance-filter").addEventListener("change", loadArticles);
}

async function loadArticles() {
    const loading = document.getElementById("loading");
    const grid = document.getElementById("articles-grid");
    const noArticles = document.getElementById("no-articles");

    const category = document.getElementById("category-filter").value;
    const importance = document.getElementById("importance-filter").value;

    let url = `/api/news?days=${currentDays}`;
    if (category) url += `&category=${category}`;
    if (importance) url += `&importance=${importance}`;

    loading.classList.remove("hidden");
    grid.classList.add("hidden");
    noArticles.classList.add("hidden");

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to fetch");

        const data = await response.json();
        loading.classList.add("hidden");

        if (data.articles.length === 0) {
            noArticles.classList.remove("hidden");
            return;
        }

        grid.innerHTML = data.articles.map(createArticleCard).join("");
        grid.classList.remove("hidden");
    } catch (err) {
        loading.classList.add("hidden");
        noArticles.textContent = "Failed to load articles. Please try again.";
        noArticles.classList.remove("hidden");
    }
}

function createArticleCard(article) {
    const categoryBadge = getCategoryBadge(article.category);
    const importanceBadge = getImportanceBadge(article.importance);
    const imageHtml = article.image_url
        ? `<img src="${article.image_url}" alt="" class="w-full h-40 object-cover" onerror="this.style.display='none'">`
        : `<div class="w-full h-40 bg-slate-100 flex items-center justify-center text-slate-400"><svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg></div>`;

    return `
        <article class="article-card">
            ${imageHtml}
            <div class="p-4">
                <div class="flex gap-2 mb-3 flex-wrap">
                    ${categoryBadge}
                    ${importanceBadge}
                </div>
                <h3 class="font-bold text-slate-800 mb-2 line-clamp-2">${escapeHtml(article.title)}</h3>
                <p class="text-sm text-slate-600 line-clamp-3">${escapeHtml(article.summary)}</p>
                <ul class="key-points-list">
                    ${article.key_points.map(p => `<li>${escapeHtml(p)}</li>`).join("")}
                </ul>
                <div class="flex items-center justify-between mt-4 pt-3 border-t border-slate-100">
                    <span class="text-xs text-slate-500">${escapeHtml(article.source)}</span>
                    <a href="${escapeHtml(article.url)}" target="_blank" rel="noopener" class="text-xs text-green-700 hover:underline flex items-center gap-1">
                        Read more
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                    </a>
                </div>
            </div>
        </article>
    `;
}

function getCategoryBadge(category) {
    const classes = {
        Kerala: "badge-kerala",
        India: "badge-india",
        International: "badge-international",
    };
    return `<span class="${classes[category] || "badge-kerala"}">${category}</span>`;
}

function getImportanceBadge(importance) {
    const classes = {
        HIGH: "badge-high",
        MEDIUM: "badge-medium",
        LOW: "badge-low",
    };
    return `<span class="${classes[importance] || "badge-low"}">${importance}</span>`;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
