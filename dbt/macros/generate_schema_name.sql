{#
    By default dbt glues schema names together: "analytics" + "staging" -> "analytics_staging".
    This override makes dbt use the schema name exactly as written in dbt_project.yml,
    so models land in "staging" and "analytics".
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
