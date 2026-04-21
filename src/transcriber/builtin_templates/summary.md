{% if metadata.get('tags') %}{{ metadata.tags }}
{% endif %}
## Summary
{% if metadata.get('date') %}
_{{ metadata.date }}_
{% endif %}

{{ content }}
