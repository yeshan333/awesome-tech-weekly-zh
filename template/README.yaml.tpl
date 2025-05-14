{{- range $key, $val := .}}

# category
{{$key}}:
{{- range $item := $val}}
  - name: "{{$item.name}}"
    desc: "{{$item.desc}}"
    published_date: "{{ getFeedLatestPostPublishedDate $item.feed_url }}"
    latest_post: "{{ getFeedLatestPost $item.feed_url $item.link }}"
    link: "[{{goUrlDecode $item.link}}]({{$item.link}})"
{{- end}}

{{end}}