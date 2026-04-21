{% if metadata.get('tags') %}{{ metadata.tags }}
{% endif %}
---
title: "{{ metadata.get('title', 'Untitled') }}"
{% if metadata.get('date') %}
date: {{ metadata.date }}
{% endif %}
{% if metadata.get('tags') %}
tags: {{ metadata.tags }}
{% endif %}
---

{{ content }}
