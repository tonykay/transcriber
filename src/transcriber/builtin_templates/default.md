# Transcript
{% if metadata.get('source_file') %}
**Source**: {{ metadata.source_file }}
{% endif %}
{% if metadata.get('date') %}
**Date**: {{ metadata.date }}
{% endif %}

---

{{ content }}
