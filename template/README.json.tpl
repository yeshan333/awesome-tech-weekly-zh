[
{{- $totalKeys := len . -}}
{{- $currentIndex := 0 -}}
{{- range $key, $items := . }}
    {
        "category": "{{$key}}",
        "feeds": [
    {{- $totalItems := len $items -}}
    {{- range $itemIndex, $item := $items}}
            {
                "name": "{{$item.name}}",
                "desc": "{{$item.desc}}",
                "published_date": "{{ getFeedLatestPostPublishedDate $item.feed_url }}",
                "latest_post": "{{ getFeedLatestPost $item.feed_url $item.link }}",
                "link": "[{{goUrlDecode $item.link}}]({{$item.link}})"
            }{{if lt $itemIndex (sub $totalItems 1)}},{{end}}
    {{- end}}
        ]
    }{{if lt $currentIndex (sub $totalKeys 1)}},{{end}}
{{- $currentIndex = add $currentIndex 1 -}}
{{- end}}
]