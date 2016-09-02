{% if error %}
**Error**: {{error}}
{% else %}
### {{pool.name}}

**region** {{pool.region.split('/')[-1]}}

name | zone
- | - 
{% for instance in pool.instances %}{{instance.split('/')[-1]}} | {{instance.split('/')[-3]}} 
{%endfor%}

{% endif %}

