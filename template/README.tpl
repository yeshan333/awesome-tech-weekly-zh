[English](resources/README-en.md) | 简体中文

<div align="center">
<h1>Awesome Technology Weekly Zh-Hans</h1>

<p> 🧐 共分设类目 {{lenGroupNum}} 个，📥 累计收录（月/周/日）刊 {{lenItemNum}} 个。</p>
<p> 🧰 记录每一个值得关注的中文技术类（月/周/日）刊，⚗️ 项目内表格通过 GitHub Action 自动生成。</p>
<p> 🕰️ 每 3 小时刷新一次。</p>

<a href="https://awesome.re">
  <img src="https://awesome.re/badge.svg" alt="Awesome">
</a>

</div>

## 目录

{{- range $key, $val := .}}
- [{{$key}}](#{{$key}})
{{- end}}

{{- range $key, $val := .}}

## {{$key}}

<p align="right">
📥 此类目收录（月/周/日）刊 {{len .}} 个。
</p>

| 名称 | 描述 | 最近更新时间-(北京时间) | 最新文章 | 网址 |
|:-:|:-|:-:|:-:|:-:|
{{- range $item := $val}}
| {{$item.name}} | {{$item.desc}} | {{ getFeedLatestPostPublishedDate $item.feed_url }} | {{ getFeedLatestPost $item.feed_url $item.link }} | [{{goUrlDecode $item.link}}]({{$item.link}}) |
{{- end}}

<div align="right">
<a href="#目录">🔝回到顶部</a>
</div>

{{end}}

## 支持一下

[为爱发电~](https://afdian.net/a/yeshan333)

<a href="https://afdian.net/a/yeshan333">
  <img src="https://pic1.afdiancdn.com/static/img/welcome/button-sponsorme.png" alt="为爱发电">
</a>

## 关联项目

- [RSSHub](https://rsshub.app/): 获取 RSS 订阅链接
- [yaml-readme](https://github.com/LinuxSuRen/yaml-readme): Github Action, 基于 yaml 配置自动生成 README
- [awesome-ops](https://github.com/eryajf/awesome-ops): README 模版 [README.tpl](template/README.tpl) 参考
