[English](resources/README-en.md) | 简体中文

<div align="center">
<h1>Awesome Technology Weekly Zh-Hans</h1>

<p> 🧐 共分设类目 {{lenGroupNum}} 个，📥 计收录周刊 {{lenItemNum}} 个。</p>
<p> 🧰 记录每一个值得关注的中文技术类（月/周/日）刊，⚗️ 项目内表格通过 GitHub Action 自动生成。</p>

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

</div>

## 目录

{{- range $key, $val := .}}
- [{{$key}}](#{{$key}})
{{- end}}

{{- range $key, $val := .}}

## {{$key}}

<p align="right">
📥 此类目收录周刊 {{len .}} 个。
</p>

| 名称 | 描述 | 网址 | 最近更新 |
|:-:|:-:|:-:|:-:|
{{- range $item := $val}}
| {{$item.name}} | {{$item.desc}} | [{{$item.link}}]({{$item.link}}) | 最近更新时间&文章 |
{{- end}}

<div align="right">

🔝[回到顶部](#目录)
</div>

{{end}}
