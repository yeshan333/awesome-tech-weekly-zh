English | [简体中文](../README.md)

<div align="center">
<h1>Awesome Ops</h1>

<p>🧐 Divided into {{lenGroupNum}} categories. 📥 Includes {{lenItemNum}} entries.</p>
<p>🧰 Record every noteworthy Chinese technical journal (monthly/weekly/daily), and ⚗️ the tables in the project are automatically generated through GitHub Action. 🧰</p>

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

</div>

## Contents

{{- range $key, $val := .}}
- [{{$key}}](#{{$key}})
{{- end}}

{{- range $key, $val := .}}

## {{$key}}

<p align="right">
📥 This category contains {{len .}} items.
</p>

| Name | Description | Addr | Updated |
|:-:|:-:|:-:|:-:|
{{- range $item := $val}}
| {{$item.name}} | {{$item.desc}} | [{{$item.link}}]({{$item.link}}) | 最近更新时间&文章 |
{{- end}}

<div align="right">

🔝[Back To Top](#Contents)
</div>

{{end}}