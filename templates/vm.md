

{% if error %}
**Error**: {{error}}
{% else %}

name | zone | status | type
- | - | - | -
{% for vm in vms %}{{vm.name}} | {{vm.zone.split('/')[-1]}} | {{vm.status}} | {{vm.machineType.split('/')[-1]}}
{%endfor%}
{% endif %}

