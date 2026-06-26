English | [简体中文](../README.md)

<div align="center">
<h1>Awesome Technology Weekly Zh-Hans</h1>

<p>
  <a href="https://github.com/yeshan333/awesome-tech-weekly-zh">
    <img src="https://img.shields.io/badge/Categories-{{lenGroupNum}}-blue?style=flat-square" alt="Categories">
  </a>
  <a href="https://github.com/yeshan333/awesome-tech-weekly-zh">
    <img src="https://img.shields.io/badge/Weeklies-{{lenItemNum}}-brightgreen?style=flat-square" alt="Total Items">
  </a>
  <a href="https://awesome.re">
    <img src="https://awesome.re/badge.svg" alt="Awesome">
  </a>
</p>

<p>🧰 Record every noteworthy Chinese technical journal (monthly/weekly/daily), and ⚗️ the tables in the project are automatically generated through GitHub Action. 🧰</p>
<p><img src="assets/news.png"/> This is a newly published article this week.</p>

</div>

<a id="Contents"></a>
## Contents

<p align="center">
{{- range $key, $val := .}}
  <a href="#{{$key}}"><code>{{$key}}</code></a> &nbsp;
{{- end}}
</p>

{{- range $key, $val := .}}

<a id="{{$key}}"></a>
## {{$key}} <img src="https://img.shields.io/badge/weeklies-{{len .}}-brightgreen?style=flat-square" valign="middle">

| Name | Description | UpdatedAt | Article | Addr |
|:-:|:-|:-:|:-|:-:|
{{- range $item := $val}}
| {{$item.name}} | {{$item.desc}} | {{ getFeedLatestPostPublishedDate $item.feed_url }} | {{ getFeedLatestPost $item.feed_url $item.link }} | [{{goUrlDecode $item.link}}]({{$item.link}}) |
{{- end}}

<div align="right">
<a href="#Contents">Back To Top</a>
</div>

{{end}}

## Related Projects

- [RSSHub](https://rsshub.app/): Get RSS feed links from any website.
- [yaml-readme](https://github.com/LinuxSuRen/yaml-readme): A helper to generate the READE file automatically from YAML-based metadata files.
- [awesome-ops](https://github.com/eryajf/awesome-ops): README template [README.tpl](template/README.tpl) reference.
