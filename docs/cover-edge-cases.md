# 有图但漏抓的边界场景

2026-10-22 对现有 31 篇文章实测。原文配图从上一轮的 20 篇增加到 23 篇，新增 3 篇均核对了原文位置和图片内容。它们是原文配图，不一律等同于作者设计的刊物封面。

## 已修复的真实漏抓

| 来源 | 原因 | 修复与核验 |
|---|---|---|
| [HelloGitHub 第 126 期](https://hellogithub.com/periodical/volume/126) | 能解析图片 URL，但 CDN 在无来源页时返回 403 | 使用公开站点来源请求图片；第一张图对应原文 ArmorPaint 项目截图，已成功下载 |
| [独立开发周记](https://www.v2ex.com/t/1250029) | 正文在 `topic_content / markdown_body` 容器中，原规则只认 article / main；正文图片还要求 `no-referrer` | 识别正文容器，跳过 Rightbar 广告及评论；尊重图片的来源策略，已取得正文第一张图 |
| [三号设计周刊第 41 期](https://sanhao-design-weekly.pages.dev/?issue=41) | 首次 HTML 只有二维码，实际文章由 script.js 按 issue 参数加载 | 只读取请求期号的 `lead.image` 字面量，同时校验文件中的期号；不执行远端脚本、不退回最新一期。已取得 vol41 配图 |

## 一并处理的边界

| 场景 | 处理方式 |
|---|---|
| 图片只写在 data-original / data-lazy-src / data-src | 读取真实地址，避免把 1×1 占位图当成没有图片 |
| picture / srcset / data-srcset / noscript | 保留可用尺寸与备用图；CDN URL 中的逗号不被误拆 |
| 页面设置 base href | 按页面声明的基准地址解析相对图片 URL |
| Article JSON-LD 中的 ImageObject | 读取当前文章的 image，支持 @graph 引用；不读取 Organization 图片或其他文章的 image |
| 图片 endpoint 用查询参数区分内容 | 保留 id、url 等内容参数，仅忽略尺寸参数，避免把当期图与主页通用图误判为同一张 |
| RSS / Atom 有多张媒体图片 | 保留最多 12 张候选，构建时按序尝试；支持多个 Media RSS、图片附件、摘要与正文备用图 |
| 前 4 张图片都失效 | 每篇最多尝试 8 张候选，继续尝试后面的有效图片 |
| 图片被标为 application/octet-stream | 用图片文件头确认类型，不因通用 MIME 错过图片，也不接受 HTML 错误页 |
| 公共 CDN 的来源页要求相反 | 尊重 no-referrer；一般图片使用公开站点 origin，403 时最多再尝试一次不带 Referer，不携带凭据 |
| 偶发 5xx、超时、短暂限流 | 有界重试一次；较长 Retry-After 不立即重试。CSDN 本轮曾返回 521，后续重试已恢复 |
| 压缩 HTML | 支持 gzip，并对解压后的内容继续施加大小限制 |
| 临时失败长期卡在缓存里 | 失败缓存缩短为 30 分钟；同一期成功图片刷新失败时可保留显示，但 30 分钟后重新尝试，不再等待 7 天 |

响应式图片依据 [MDN picture 文档](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/picture)，结构化文章信息依据 [Schema.org Article](https://schema.org/Article)。

## 仍使用插画的 8 篇

| 来源 | 当前核验结果 |
|---|---|
| ElixirStatus 当前文章 | 只有作者头像和站点 logo；头像即使经重定向也会被排除 |
| Go 语言爱好者当前链接 | Python 请求遇到 TLS 握手失败；另用 curl 检查公开页面，当前正文为纯文本，页面图片是头像和二维码，不补成文章封面 |
| Python 潮流周刊 Telegram 当前消息 | 检查公开嵌入后，当前消息仍是纯文本通知；频道头像不作为消息配图 |
| Rust 中文社区当前文章 | 正文未提供图片，只看到站点标志 |
| Hacker News 每日摘要 | 图片是菜单、目录和站点图标，没有当期文章图片 |
| 肖恩技术周刊迁移公告 | 当前条目是纯文本迁移说明，没有正文图片 |
| SecWiki | 当前地址持续返回 502，无法确认当期图片；记录错误并等待重试 |
| Software Testing Weekly #313 | 提供的是通用站点分享图及作者头像，继续过滤 |

## 排查和验证

- `covers/sources.json`：成功图片与对应文章的来源记录。
- `covers/status.json`：包括无图文章在内的全部状态、候选数量、下载尝试与失败原因。
- `--force-cover-refresh`：主动重查，不必删除缓存或等待过期。
- Python 48 个场景通过；Bun 10 个 RSS / 元数据场景通过。
- 已保留头像、通用图、推荐区图片、错期期号等准确性检查。新增提取途径不意味着允许借用别期图片。

现有页面显示和来源均已核验；未来原站改版、网络故障或错误元数据仍可能影响抓取。三号设计周刊适配器在格式或期号不匹配时安全退回插画，不猜测其他期的图。代码尚未发布。
