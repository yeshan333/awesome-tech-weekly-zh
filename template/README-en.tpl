English | [简体中文](../README.md)

<div align="center">
<h1>Awesome Technology Weekly Zh-Hans</h1>

<p>🧐 Divided into {{lenGroupNum}} categories. 📥 Includes {{lenItemNum}} weeklies.</p>
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

| Name | Description | Addr | UpdatedAt |
|:-:|:-:|:-:|:-:|:-:|
{{- range $item := $val}}
| {{$item.name}} | {{$item.desc}} | [{{$item.link}}]({{$item.link}}) | {{ getFeedLatestPostPublishedDate $item.feed_url }} | {{ getFeedLatestPost $item.feed_url $item.link }} |
{{- end}}

<div align="right">

🔝[Back To Top](#Contents)
</div>

{{end}}