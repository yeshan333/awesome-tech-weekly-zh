class WeeklyNavigator {
    constructor() {
        this.data = [];
        this.filteredData = [];
        this.currentCategory = 'all';
        this.searchTerm = '';
        this.debounceTimer = null;
        
        this.init();
    }

    async init() {
        try {
            await this.loadData();
            this.setupEventListeners();
            this.render();
            this.updateStats();
        } catch (error) {
            console.error('Failed to initialize:', error);
            this.showError('加载数据失败，请刷新页面重试');
        }
    }

    async loadData() {
        try {
            const response = await fetch('../README.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.data = await response.json();
            this.filteredData = this.getAllFeeds();
        } catch (error) {
            console.warn('Using fallback data:', error);
            this.data = [
                {
                    category: "AI",
                    feeds: [{
                        name: "AIGC Weekly",
                        desc: "每周一更新，主要介绍上周AIGC领域发布的一些产品以及值得关注的研究成果",
                        published_date: "2025-07-14T04:37:53Z",
                        latest_post: "[AIGC Weekly #130](https://quaily.com/op7418/p/aigc-weekly-one-thirty)",
                        link: "[https://quail.ink/op7418](https://quail.ink/op7418)"
                    }]
                }
            ];
            this.filteredData = this.getAllFeeds();
        }
    }

    getAllFeeds() {
        return this.data.flatMap(item => 
            item.feeds.map(feed => ({
                ...feed,
                category: item.category
            }))
        );
    }

    setupEventListeners() {
        const searchInput = document.getElementById('searchInput');
        const filterButtons = document.querySelectorAll('.filter-btn');

        searchInput.addEventListener('input', (e) => {
            this.debounceSearch(e.target.value);
        });

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.target.value = '';
                this.searchTerm = '';
                this.filterData();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                searchInput.focus();
            }
        });

        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const category = e.target.dataset.category;
                this.setCategory(category);
            });
        });
    }

    debounceSearch(term) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.searchTerm = term.toLowerCase().trim();
            this.filterData();
        }, 300);
    }

    setCategory(category) {
        this.currentCategory = category;
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.category === category);
        });

        this.filterData();
    }

    filterData() {
        let filtered = this.getAllFeeds();

        if (this.currentCategory !== 'all') {
            filtered = filtered.filter(feed => feed.category === this.currentCategory);
        }

        if (this.searchTerm) {
            filtered = filtered.filter(feed => 
                feed.name.toLowerCase().includes(this.searchTerm) ||
                feed.desc.toLowerCase().includes(this.searchTerm) ||
                this.stripMarkdown(feed.latest_post).toLowerCase().includes(this.searchTerm)
            );
        }

        this.filteredData = filtered;
        this.render();
        this.updateStats();
    }

    stripMarkdown(text) {
        return text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/!\[([^\]]*)\]\([^)]+\)/g, '');
    }

    parseMarkdownLink(text) {
        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
        const imgRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
        
        let cleanText = text.replace(imgRegex, '').trim();
        let links = [];
        let match;
        
        while ((match = linkRegex.exec(cleanText)) !== null) {
            links.push({
                text: match[1],
                url: match[2]
            });
        }

        if (links.length === 0) {
            const urlRegex = /(https?:\/\/[^\s]+)/g;
            let urlMatch;
            while ((urlMatch = urlRegex.exec(text)) !== null) {
                links.push({
                    text: urlMatch[1],
                    url: urlMatch[1]
                });
            }
        }

        return links.length > 0 ? links : [{ text: cleanText, url: null }];
    }

    isNewPost(publishedDate) {
        if (!publishedDate) return false;
        
        try {
            const postDate = new Date(publishedDate);
            const now = new Date();
            const diffTime = Math.abs(now - postDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            return diffDays <= 7;
        } catch {
            return false;
        }
    }

    render() {
        this.renderCategories();
        this.renderWeeklyGrid();
    }

    renderCategories() {
        const categories = [...new Set(this.data.map(item => item.category))];
        const container = document.getElementById('filterTags');
        
        container.innerHTML = '';
        
        categories.forEach(category => {
            const button = document.createElement('button');
            button.className = 'filter-btn';
            button.dataset.category = category;
            button.textContent = category;
            button.addEventListener('click', () => this.setCategory(category));
            container.appendChild(button);
        });
    }

    renderWeeklyGrid() {
        const container = document.getElementById('weeklyGrid');
        const emptyState = document.getElementById('emptyState');

        if (this.filteredData.length === 0) {
            container.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        container.style.display = 'grid';
        emptyState.style.display = 'none';

        container.innerHTML = '';

        this.filteredData.forEach(feed => {
            const card = this.createWeeklyCard(feed);
            container.appendChild(card);
        });
    }

    createWeeklyCard(feed) {
        const card = document.createElement('div');
        card.className = `weekly-card ${this.isNewPost(feed.published_date) ? 'new' : ''}`;

        const latestPostLinks = this.parseMarkdownLink(feed.latest_post);
        const linkLinks = this.parseMarkdownLink(feed.link);

        const latestPostHtml = latestPostLinks.map(link => 
            link.url ? `<a href="${link.url}" target="_blank" rel="noopener">${link.text}</a>` : link.text
        ).join('');

        const linkHtml = linkLinks.map(link => 
            link.url ? `<a href="${link.url}" target="_blank" rel="noopener" class="weekly-link">🔗 访问周刊</a>` : ''
        ).join('');

        const hasNewBadge = feed.latest_post.includes('![news]') || this.isNewPost(feed.published_date);

        card.innerHTML = `
            <div class="category-tag">${feed.category}</div>
            <h3 class="weekly-name">${feed.name}${hasNewBadge ? ' <span style="color: var(--primary-color);">🆕</span>' : ''}</h3>
            <p class="weekly-desc">${feed.desc}</p>
            
            <div class="latest-post">
                <div class="latest-post-label">最新文章</div>
                <div class="latest-post-content">${latestPostHtml}</div>
            </div>
            
            <div class="weekly-links">
                ${linkHtml}
            </div>
        `;

        return card;
    }

    updateStats() {
        const totalCount = this.getAllFeeds().length;
        const categoryCount = this.data.length;
        const updatedCount = this.getAllFeeds().filter(feed => this.isNewPost(feed.published_date)).length;

        document.getElementById('totalCount').textContent = totalCount;
        document.getElementById('categoryCount').textContent = categoryCount;
        document.getElementById('updatedCount').textContent = updatedCount;
    }

    showError(message) {
        const container = document.getElementById('weeklyGrid');
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>发生错误</h3>
                <p>${message}</p>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new WeeklyNavigator();
});

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    
    document.addEventListener('keydown', function(e) {
        if (e.key === '/' && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
    });
});