# 技术周刊导航 - Bento Grid 风格网站

这是基于 Awesome Technology Weekly Zh-Hans 项目数据创建的 Bento Grid 卡片风格网站实现。

## 功能特点

- **Bento Grid卡片布局**：美观现代的卡片式布局，灵感来自日本便当盒
- **响应式设计**：完美适配桌面、平板和移动设备
- **分类过滤**：可按技术领域过滤周刊
- **搜索功能**：支持实时搜索周刊标题、描述和内容
- **最新内容标记**：自动为7天内更新的内容添加"New"标签
- **平滑动画**：加载和交互时的流畅动画效果

## 网站文件说明

- `index.html` - 网站主页面结构
- `styles.css` - Bento Grid 样式和响应式设计
- `script.js` - 数据加载、动态卡片生成和交互功能
- `README.json` - 周刊数据源（项目自动更新）

## 如何使用

1. 确保三个主要文件（index.html, styles.css, script.js）和数据文件（README.json）在同一目录
2. 使用任何HTTP服务器托管文件，例如:
   ```bash
   python -m http.server
   ```
3. 或者直接在浏览器中打开`index.html`文件

## 技术说明

### HTML结构
- 使用语义化HTML5标签构建页面结构
- 主要包含头部、搜索过滤区、Bento Grid卡片区和页脚

### CSS特性
- 原生CSS3变量定义主题颜色和样式
- 使用Grid布局实现Bento Grid卡片风格
- 响应式设计使用媒体查询适配不同设备
- 平滑过渡和动画效果提升用户体验

### JavaScript功能
- 异步加载README.json数据
- 动态生成卡片内容并应用差异化布局
- 实现分类过滤和全文搜索功能
- 优化链接处理和日期格式化

## 自定义和扩展

如需修改网站外观和功能，可以：

1. 在styles.css中更改CSS变量，自定义配色方案
2. 在index.html中调整过滤类别和页面结构
3. 在script.js中修改卡片生成逻辑和交互功能

## 许可

与原项目保持一致的许可协议