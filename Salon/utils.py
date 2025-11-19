import markdown2
import bleach

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u",
    "ul", "ol", "li", "blockquote",
    "h1","h2","h3","h4",
    "code", "pre"
]

ALLOWED_ATTRIBUTES = {
    # npr. da jednom dopustiš linkove:
    # "a": ["href", "title"]
}

ALLOWED_ATTRS = {
    "code": ["class"],
    "pre": ["class"]
}

def sanitize_markdown(md_text: str) -> str:
    if not md_text:
        return ""
    # 1. markdown → html
    html = markdown2.markdown(md_text, extras=["fenced-code-blocks", "tables"])
    # 2. bleach očisti HTML
    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return clean

def sanitize_html(text: str) -> str:
    """Očisti korisnički unos od opasnog HTML-a (XSS zaštita)."""
    if not text:
        return ""
    clean = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,     # izbaci sve nedozvoljene tagove
    )
    return clean

