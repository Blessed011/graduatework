from django import template

register = template.Library()

@register.filter
def ms_to_mmss(milliseconds):
    if milliseconds is None:
        return "-"
    try:
        seconds = int(milliseconds) // 1000
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"0{minutes}:{remaining_seconds:02}"
    except Exception:
        return "-"