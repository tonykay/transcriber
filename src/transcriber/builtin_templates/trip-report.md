{% if metadata.get('tags') %}{{ metadata.tags }}
{% endif %}
# Trip Report
{% if metadata.get('event') %}
**Event**: {{ metadata.event }}
{% endif %}
{% if metadata.get('date') %}
**Date**: {{ metadata.date }}
{% endif %}
{% if metadata.get('location') %}
**Location**: {{ metadata.location }}
{% endif %}

## Summary

{{ content }}
