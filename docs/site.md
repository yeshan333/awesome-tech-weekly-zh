# 周刊目录网站

网站从 `README.json` 构建，内容继续由现有 YAML / RSS 采集流程维护。页面模板、样式、交互和字体放在 `template/site/`，生成器为 `scripts/build_site.py`。构建只依赖 Python 标准库，不需要前端框架或外部 CDN。

## 本地预览

```sh
rtk proxy python3 scripts/build_site.py --fetch-covers
rtk proxy python3 -m http.server 8765 --directory site
```

打开 <http://localhost:8765>。如果已有需要保留的 `site/`，使用独立输出目录：

```sh
rtk proxy python3 scripts/build_site.py --fetch-covers --output-dir /tmp/weekly-taste-preview
rtk proxy python3 -m http.server 8765 --directory /tmp/weekly-taste-preview
```

`--feed-only` 只生成聚合 RSS；`--site-url` 设置 RSS 的网站地址。Netlify 流程会传入自己的域名，GitHub Pages 流程从仓库配置读取实际地址，因此也适用于用户站点继承的自定义域名和项目子路径。

## 每期封面自动更新

封面随定时数据更新与站点构建获取，不需要访客浏览器跨站请求。当前数据模型保留每份周刊的最新一期，新一期发布后按新的文章 URL 重新获取，不会沿用上一期缓存。

获取顺序：RSS / Atom 当期图片附件、Media RSS 或正文候选 → 文章页的分享图、Article JSON-LD → 正文、懒加载或响应式图片 → 已适配站点的当期脚本数据 / 公开消息嵌入 → 本地主题插画。**原文配图不一定是原刊封面**，正文产品截图也属于原文配图。会排除头像、导航区图片、与主页相同的通用分享图、推荐文章中重复使用的配图，以及编号与 GitHub release 不一致的 `weekly-header` 图片。无法可靠提取时使用插画；这些规则不能保证未来所有来源都正确，原站结构变化、错误元数据或没有可识别期号的旧图仍需要人工复核。

RSS 采集器将首图和候选列表写入 `README.json` 的 `cover_url`、`cover_urls` 字段；`scripts/covers.py` 下载图片到 `.cover-cache/`，构建时复制到 `site/covers/`。`covers/sources.json` 保留原始来源与对应文章；`covers/status.json` 记录每篇的状态、尝试过的图片和错误原因。单张图片最多 4 MB，限制并发数与网络超时。成功结果缓存 7 天，失败结果 30 分钟；当 RSS 候选图片地址改变时提前刷新。提取规则升级会使旧缓存失效，避免继续展示已知误图。缓存按当前文章清理，GitHub Actions 与 Netlify 的定时构建均启用了缓存恢复。

工作流计划在 UTC 00:00、10:00、20:00 运行（UTC+8 为 08:00、18:00、次日 04:00），实际开始时间取决于 GitHub Actions 调度。新一期在下次成功采集、构建和部署后展示，并非每次浏览器刷新都即时抓取。当前改动尚未发布，远端不会提前获得这些行为。

`--fetch-covers` 开启联网更新；不传时只复用本地缓存，适合离线调样式。`--force-cover-refresh` 忽略有效期并重新核验；`--cover-cache-dir` 可以指定独立缓存目录。`--feed-only` 不抓图。

详见 [有图但漏抓的边界场景](cover-edge-cases.md)，包含真实来源、修复方式与保留兜底的原因。

## 发布到 GitHub Pages

1. 将代码合入 `main`。
2. 在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
3. 在 Actions 中运行 **Deploy newsletter directory to GitHub Pages**。

流程也会在模板、构建器、README.json 更新后自动运行。数据生成工作流完成后通过 `workflow_run` 触发部署，以兼容机器人提交不会触发其他 push 工作流的情况。原有 Netlify 发布仍可使用。

发布方式参考 [GitHub 官方文档](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。本次改动只准备了代码，没有更改远端发布源或部署线上页面。

## 验证

```sh
rtk proxy bun test tests/feed-cover.test.ts
rtk proxy python3 -m unittest discover -s tests -p 'test_*.py' -v
rtk proxy node scripts/verify_site.mjs --dir /tmp/weekly-taste-preview
```

浏览器验证使用已安装的 Playwright（本地包或全局 `@playwright/cli` 的依赖）及其 Chromium。覆盖分类、搜索、近 7 天组合筛选、空结果恢复、鼠标拖拽、触摸滑动、上下滚动、主题持久化、无脚本阅读、存储被禁用和减少动态效果等场景。

## 设计依据

采用 [taste-skill](https://github.com/Leonxlnx/taste-skill) 的 app-screen 路线：此网站的主要任务是查找周刊与阅读文章。抽取方向为 **Editorial greeting**，seed 为 `1249696212`，没有重新抽取。以真实周刊目录组成版面：1100px 居中阅读区、分类侧栏、浅色分区、Instrument Sans 和系统中文字体，青绿色只强调近期更新与阅读入口。手机端将分类折叠为原生下拉框。

页面使用全部真实收录数据，不含示例统计或虚构文章。最新文章优先使用对应原文配图，缺图时使用 4 张统一印刷风格的 AI 主题插画：编程与系统、社区阅读、AI 创意温室和探索新知。插画由内置 image_gen 工具生成，按周刊领域匹配，不代表原文封面。WebP 文件放在 `template/site/images/`，合计约 470 KB，完整提示词保存在同目录的 `PROMPTS.md`，页脚标注图片来源。首张图优先加载，其余首屏图片正常加载，后续图片懒加载。

Instrument Sans 字体随站点自托管，授权文件位于 `template/site/fonts/OFL.txt`。

2026-10-22 验证结果：

- Bun：10 个 RSS 图片提取与元数据生成场景通过。
- Python：48 个数据、RSS、图片获取与缓存场景通过。
- 真实浏览器：69 项交互、图片加载与兜底检查通过。
- 第一轮下载成功的 20 张中发现了头像、通用图和错期期号；成功下载不代表封面正确，修正与逐项核验见 [配图核验记录](cover-audit.md)。
- taste-skill 源码检查：0 FAIL、0 WARN。
- 1440 / 768 / 390px 渲染检查：0 FAIL、1 WARN。允许原始周刊描述中的 emoji，避免擅改来源内容；界面自身没有 emoji 装饰。保留的 `panel-void` 提示来自最新文章标题长度不同，底部阅读入口统一对齐，空白不来自固定高度占位。

最终截图复查：

1. 最大的信息区呈现真实最新文章，周刊目录提供下一步阅读入口。
2. 页面左右边界统一，首屏展示图文文章和目录入口；手机不会横向溢出。
3. 配图优先保留原文视觉内容，兜底图使用青绿纸质印刷风格；界面强调色集中在阅读入口与近期更新，普通分类选中状态使用中性色。
4. 收录总数、分类数和近期更新数均由数据计算；筛选后分类计数与结果一致。
5. 无发布日期显示“暂无发布日期”，无最新文章保留周刊主页入口，不伪装成新文章。
6. 本站没有图表或图例；无需用图表重复目录数据。
7. 手机保留完整描述、文章链接和主页入口，分类改为可键盘及触屏操作的原生控件。
