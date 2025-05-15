document.addEventListener('DOMContentLoaded', function() {
    const bentoContainer = document.getElementById('bento-container');
    const searchInput = document.getElementById('search');
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    let allWeeklies = [];  // 存储所有周刊数据
    
    // 加载JSON数据
    fetch('https://fastly.jsdelivr.net/gh/yeshan333/awesome-tech-weekly-zh@main/README.json')
        .then(response => response.json())
        .then(data => {
            allWeeklies = data;
            renderWeeklies(allWeeklies);
            setupFilterButtons();
        })
        .catch(error => {
            console.error('Error loading data:', error);
            bentoContainer.innerHTML = `<div class="error-message">加载数据失败，请刷新页面重试。</div>`;
        });
    
    // 渲染周刊卡片
    function renderWeeklies(weeklies) {
        bentoContainer.innerHTML = '';
        
        if (weeklies.length === 0) {
            bentoContainer.innerHTML = `<div class="no-results">没有找到匹配的周刊。</div>`;
            return;
        }
        
        let delay = 0;
        weeklies.forEach(category => {
            const { category: categoryName, feeds } = category;
            
            feeds.forEach(weekly => {
                const card = createWeeklyCard(weekly, categoryName);
                card.style.animationDelay = `${delay}ms`;
                bentoContainer.appendChild(card);
                delay += 50;  // 递增延迟，创建瀑布效果
            });
        });
    }
    
    // 创建单个周刊卡片
    function createWeeklyCard(weekly, categoryName) {
        const { name, desc, published_date, latest_post, link } = weekly;
        
        // 提取链接URL和文本
        const linkUrl = extractUrl(link);
        const latestPostUrl = extractUrl(latest_post);
        const latestPostText = extractText(latest_post);
        
        // 检查是否为新内容（7天内发布）
        const isNew = isRecentlyPublished(published_date, 7);
        
        // 创建卡片容器
        const card = document.createElement('div');
        card.className = 'card fade-in';
        card.dataset.category = categoryName;
        
        // 卡片内容
        card.innerHTML = `
            ${isNew ? '<span class="new-badge">New</span>' : ''}
            <div class="card-header">
                <span class="card-category">${categoryName}</span>
                <h3 class="card-title">${name}</h3>
                <p class="card-description">${desc || '暂无描述'}</p>
            </div>
            <div class="card-content">
                ${published_date ? `<p class="post-date">最近更新: ${formatDate(published_date)}</p>` : ''}
                <div class="latest-post">
                    ${latestPostUrl ? `<a href="${latestPostUrl}" target="_blank">${latestPostText}</a>` : latestPostText || '暂无最新内容'}
                </div>
            </div>
            <div class="card-footer">
                <a href="${linkUrl}" class="visit-link" target="_blank">访问周刊 <i class="ph-arrow-right"></i></a>
            </div>
        `;
        
        return card;
    }
    
    // 设置过滤按钮
    function setupFilterButtons() {
        // 获取所有可用类别
        const allCategories = getAllCategories(allWeeklies);
        
        // 更新过滤器按钮
        const categoryFilter = document.querySelector('.category-filter');
        categoryFilter.innerHTML = '<button class="filter-btn active" data-category="all">全部</button>';
        
        // 显示所有类别按钮
        allCategories.forEach(category => {
            categoryFilter.innerHTML += `<button class="filter-btn" data-category="${category}">${category}</button>`;
        });
        
        // 添加事件监听
        const allFilterButtons = document.querySelectorAll('.filter-btn');
        allFilterButtons.forEach(button => {
            button.addEventListener('click', function() {
                const category = this.dataset.category;
                
                // 更新激活状态
                allFilterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // 过滤卡片
                filterCardsByCategory(category);
            });
        });
    }
    
    // 获取所有可用类别
    function getAllCategories(weeklies) {
        return weeklies.map(item => item.category);
    }
    
    // 根据类别过滤卡片
    function filterCardsByCategory(category) {
        const cards = document.querySelectorAll('.card');
        
        cards.forEach(card => {
            if (category === 'all' || card.dataset.category === category) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }
    
    // 搜索功能
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase().trim();
        
        if (searchTerm === '') {
            // 如果搜索框为空，显示所有卡片
            const activeCategory = document.querySelector('.filter-btn.active').dataset.category;
            filterCardsByCategory(activeCategory);
            return;
        }
        
        const cards = document.querySelectorAll('.card');
        
        cards.forEach(card => {
            const title = card.querySelector('.card-title').textContent.toLowerCase();
            const description = card.querySelector('.card-description').textContent.toLowerCase();
            const latestPost = card.querySelector('.latest-post').textContent.toLowerCase();
            const category = card.dataset.category.toLowerCase();
            
            if (title.includes(searchTerm) || 
                description.includes(searchTerm) || 
                latestPost.includes(searchTerm) ||
                category.includes(searchTerm)) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    });
    
    // 从Markdown链接格式中提取URL
    function extractUrl(text) {
        if (!text) return '';
        
        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/;
        const match = text.match(linkRegex);
        
        return match ? match[2] : text;
    }
    
    // 从Markdown链接格式中提取文本
    function extractText(text) {
        if (!text) return '';
        
        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/;
        const match = text.match(linkRegex);
        
        return match ? match[1] : text;
    }
    
    // 格式化日期显示
    function formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays <= 1) {
            return '今天';
        } else if (diffDays <= 2) {
            return '昨天';
        } else if (diffDays <= 7) {
            return `${diffDays}天前`;
        } else {
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        }
    }
    
    // 检查是否为最近发布（用于显示New标签）
    function isRecentlyPublished(dateString, days = 7) {
        if (!dateString) return false;
        
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        return diffDays <= days;
    }
});