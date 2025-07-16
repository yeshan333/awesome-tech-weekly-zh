class TechWeeklyApp {
    constructor() {
        this.data = [];
        this.filteredData = [];
        this.currentCategory = 'all';
        this.searchTerm = '';
        
        this.init();
    }

    async init() {
        try {
            await this.loadData();
            this.setupEventListeners();
            this.render();
        } catch (error) {
            console.error('初始化应用失败:', error);
            this.showError('加载数据失败，请刷新页面重试');
        }
    }

    async loadData() {
        try {
            const response = await fetch('README.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.data = await response.json();
            this.filteredData = [...this.data];
        } catch (error) {
            console.error('加载数据失败:', error);
            this.data = this.getFallbackData();
            this.filteredData = [...this.data];
        }
    }

    getFallbackData() {
        return [
            {
                category: "AI",
                feeds: [
                    {
                        name: "AIGC Weekly",
                        desc: "每周一更新，主要介绍上周AIGC领域发布的一些产品以及值得关注的研究成果",
                        published_date: "2025-07-14T04:37:53Z",
                        latest_post: "[AIGC Weekly #130](https://quaily.com/op7418/p/aigc-weekly-one-thirty)",
                        link: "[https://quail.ink/op7418](https://quail.ink/op7418)"
                    }
                ]
            }
        ];
    }

    setupEventListeners() {
        const searchInput = document.getElementById('searchInput');
        const searchHint = document.querySelector('.search-hint');

        searchInput.addEventListener('input', this.debounce((e) => {
            this.searchTerm = e.target.value.toLowerCase().trim();
            this.applyFilters();
        }, 300));

        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                searchInput.focus();
            }
            if (e.key === 'Escape') {
                searchInput.blur();
                searchInput.value = '';
                this.searchTerm = '';
                this.applyFilters();
            }
        });

        searchInput.addEventListener('focus', () => {
            searchHint.style.opacity = '0.3';
        });

        searchInput.addEventListener('blur', () => {
            searchHint.style.opacity = '1';
        });
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    applyFilters() {
        let filtered = [...this.data];

        if (this.currentCategory !== 'all') {
            filtered = filtered.filter(item => item.category === this.currentCategory);
        }

        if (this.searchTerm) {
            filtered = filtered.map(category => ({
                ...category,
                feeds: category.feeds.filter(feed => 
                    feed.name.toLowerCase().includes(this.searchTerm) ||
                    feed.desc.toLowerCase().includes(this.searchTerm) ||
                    feed.latest_post.toLowerCase().includes(this.searchTerm)
                )
            })).filter(category => category.feeds.length > 0);
        }

        this.filteredData = filtered;
        this.render();
    }

    render() {
        this.renderStats();
        this.renderFilters();
        this.renderContent();
    }

    renderStats() {
        const totalFeeds = this.filteredData.reduce((sum, category) => sum + category.feeds.length, 0);
        const totalCategories = this.filteredData.length;
        
        let latestDate = null;
        this.data.forEach(category => {
            category.feeds.forEach(feed => {
                if (feed.published_date) {
                    const date = new Date(feed.published_date);
                    if (!latestDate || date > latestDate) {
                        latestDate = date;
                    }
                }
            });
        });

        document.getElementById('totalCount').textContent = totalFeeds;
        document.getElementById('categoryCount').textContent = totalCategories;
        document.getElementById('lastUpdate').textContent = latestDate ? 
            latestDate.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }) : '未知';
    }

    renderFilters() {
        const categoryFilters = document.getElementById('categoryFilters');
        const categories = [...new Set(this.data.map(item => item.category))].sort();
        
        categoryFilters.innerHTML = '';
        
        categories.forEach(category => {
            const button = document.createElement('button');
            button.textContent = category;
            button.className = this.currentCategory === category ? 'active' : '';
            button.addEventListener('click', () => {
                this.currentCategory = category;
                this.applyFilters();
            });
            categoryFilters.appendChild(button);
        });

        const allButton = document.querySelector('[data-category="all"]');
        if (allButton) {
            allButton.className = this.currentCategory === 'all' ? 'filter-btn active' : 'filter-btn';
            allButton.addEventListener('click', () => {
                this.currentCategory = 'all';
                this.applyFilters();
            });
        }
    }

    renderContent() {
        const content = document.getElementById('content');
        
        if (this.filteredData.length === 0) {
            content.innerHTML = `
                <div class="no-results">
                    <p>没有找到匹配的内容</p>
                    <p style="font-size: 0.875rem; color: var(--text-muted); margin-top: 0.5rem;">
                        尝试调整搜索词或筛选条件
                    </p>
                </div>
            `;
            return;
        }

        content.innerHTML = this.filteredData.map(category => `
            <div class="category-section fade-in">
                <div class="category-header">
                    <h2 class="category-title">${this.escapeHtml(category.category)}</h2>
                    <p class="category-count">${category.feeds.length} 个周刊</p>
                </div>
                <div class="feed-list">
                    ${category.feeds.map(feed => this.renderFeedItem(feed)).join('')}
                </div>
            </div>
        `).join('');
    }

    renderFeedItem(feed) {
        const isNew = this.isNewArticle(feed.published_date);
        const cleanLatestPost = this.cleanLatestPost(feed.latest_post);
        const cleanLink = this.cleanLink(feed.link);
        
        return `
            <div class="feed-item">
                <h3 class="feed-name">${this.escapeHtml(feed.name)} ${isNew ? '<span class="new-badge">NEW</span>' : ''}</h3>
                <p class="feed-desc">${this.escapeHtml(feed.desc)}</p>
                <div class="feed-meta">
                    <span class="feed-date">${this.formatDate(feed.published_date)}</span>
                    <a href="${cleanLink}" target="_blank" rel="noopener noreferrer" class="feed-link">访问周刊 →</a>
                </div>
                <div class="feed-latest">${cleanLatestPost}</div>
            </div>
        `;
    }

    isNewArticle(publishedDate) {
        if (!publishedDate) return false;
        const date = new Date(publishedDate);
        const now = new Date();
        const daysDiff = (now - date) / (1000 * 60 * 60 * 24);
        return daysDiff <= 7;
    }

    cleanLatestPost(latestPost) {
        return latestPost.replace(/!\[news\]\([^)]*\)/g, '');
    }

    cleanLink(link) {
        const match = link.match(/\[([^\]]*)\]\(([^)]*)\)/);
        return match ? match[2] : link;
    }

    formatDate(dateString) {
        if (!dateString) return '未知';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        } catch {
            return '未知';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        const content = document.getElementById('content');
        content.innerHTML = `
            <div class="no-results">
                <p>⚠️ ${message}</p>
                <button onclick="location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: var(--accent-color); color: white; border: none; border-radius: var(--border-radius); cursor: pointer;">
                    重新加载
                </button>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new TechWeeklyApp();
});

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => console.log('SW registered'))
            .catch(registrationError => console.log('SW registration failed'));
    });
}