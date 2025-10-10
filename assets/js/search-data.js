---
layout: null
---
window.searchData = [
  {% for page in site.pages %}
    {% unless page.url contains '/assets/' or page.url contains '/img/' %}
    {
      "title": "{{ page.title | default: page.name | escape }}",
      "url": "{{ page.url | relative_url }}",
      "content": "{{ page.content | strip_html | strip_newlines | escape }}"
    }{% unless forloop.last %},{% endunless %}
    {% endunless %}
  {% endfor %}
];
