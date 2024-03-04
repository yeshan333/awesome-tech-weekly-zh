English | [简体中文](../README.md)

<div align="center">
<h1>Awesome Technology Weekly Zh-Hans</h1>

<p>🧐 Divided into {{lenGroupNum}} categories. 📥 Includes {{lenItemNum}} weeklies.</p>
<p>🧰 Record every noteworthy Chinese technical journal (monthly/weekly/daily), and ⚗️ the tables in the project are automatically generated through GitHub Action. 🧰</p>

<a href="https://awesome.re">
  <img src="https://awesome.re/badge.svg" alt="Awesome">
</a>

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

| Name | Description | Addr | UpdatedAt | Article |
|:-:|:-|:-:|:-:|:-:|
{{- range $item := $val}}
| {{$item.name}} | {{$item.desc}} | [{{goUrlDecode $item.link}}]({{$item.link}}) | {{ getFeedLatestPostPublishedDate $item.feed_url }} | {{ getFeedLatestPost $item.feed_url $item.link }} |
{{- end}}

<div align="right">
<a href="#Contents">Back To Top</a>
</div>

{{end}}

## Support Project

[为爱发电~](https://afdian.net/a/yeshan333)

<a href="https://afdian.net/a/yeshan333">
  <img src="https://pic1.afdiancdn.com/static/img/welcome/button-sponsorme.png" alt="为爱发电">
</a>

## Related Projects

- [RSSHub](https://rsshub.app/): Get RSS feed links from any website.
- [yaml-readme](https://github.com/LinuxSuRen/yaml-readme): A helper to generate the READE file automatically from YAML-based metadata files.
- [awesome-ops](https://github.com/eryajf/awesome-ops): README template [README.tpl](template/README.tpl) reference.
