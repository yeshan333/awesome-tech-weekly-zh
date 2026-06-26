[English](resources/README-en.md) | 简体中文

<div align="center">
<h1>Awesome Technology Weekly Zh-Hans</h1>
<img src="https://telegraph.shansan.top/file/5490d8cd92c071e62d84c.png" alt="Awesome Technology Weekly Zh-Hans">

<p>
  <a href="https://github.com/yeshan333/awesome-tech-weekly-zh">
    <img src="https://img.shields.io/badge/类目数量-{{lenGroupNum}}-blue?style=flat-square" alt="Categories">
  </a>
  <a href="https://github.com/yeshan333/awesome-tech-weekly-zh">
    <img src="https://img.shields.io/badge/累计收录-{{lenItemNum}}-brightgreen?style=flat-square" alt="Total Items">
  </a>
  <a href="https://awesome.re">
    <img src="https://awesome.re/badge.svg" alt="Awesome">
  </a>
</p>

<p>🧰 记录每一个值得关注的中文技术类（月/周/日）刊，⚗️ 项目内表格通过 GitHub Action 自动生成。</p>
<p>🕰️ 每天刷新一次。<img src="assets/news.png"/> 表示为本周新发的文章。</p>

</div>

## 目录

<p align="center">
{{- range $key, $val := .}}
  <a href="#{{slugify $key}}"><code>{{$key}}</code></a> &nbsp;
{{- end}}
</p>

{{- range $key, $val := .}}

## {{$key}} <img src="https://img.shields.io/badge/收录-{{len .}}个-brightgreen?style=flat-square" valign="middle">

| 名称 | 描述 | 最近更新时间-(北京时间) | 最新文章 | 网址 |
|:-:|:-|:-:|:-|:-:|
{{- range $item := $val}}
| {{$item.name}} | {{$item.desc}} | {{ getFeedLatestPostPublishedDate $item.feed_url }} | {{ getFeedLatestPost $item.feed_url $item.link }} | [{{goUrlDecode $item.link}}]({{$item.link}}) |
{{- end}}

<div align="right">
<a href="#目录">🔝回到顶部</a>
</div>

{{end}}

## 关联项目

- [RSSHub](https://rsshub.app/) 以及[公共实例](https://docs.rsshub.app/zh/guide/instances): 获取 RSS 订阅链接
- [yaml-readme](https://github.com/LinuxSuRen/yaml-readme): Github Action, 基于 yaml 配置自动生成 README
- [awesome-ops](https://github.com/eryajf/awesome-ops): README 模版 [README.tpl](template/README.tpl) 参考
