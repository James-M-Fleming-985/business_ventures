"""Generated subscription site. Content lives in SITE; behaviour lives in mvp_runtime."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

import mvp_runtime as rt

SITE = __SITE__

rt.configure(
    product_name=SITE["name"],
    tagline=SITE["tagline"],
    free_features=SITE["free_features"],
    premium_features=SITE["premium_features"],
    sample_data=SITE["sample_data"],
    ga4_measurement_id=SITE["ga4_measurement_id"],
)

ITEMS = SITE["items"]
PREMIUM_FIELDS = tuple(SITE["premium_fields"])
LABELS = SITE["field_labels"]
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
esc = rt.esc

app = FastAPI(title=SITE["name"], docs_url=None, redoc_url=None, openapi_url=None)
rt.install_security_headers(app)
app.include_router(rt.router)


def _price_text(request: Request) -> str:
    return rt.format_price(rt.price_for(rt.detect_country(request)))


def _ticks(items) -> str:
    return '<ul class="ticks">' + "".join("<li>" + esc(i) + "</li>" for i in items) + "</ul>"


def _card(item: dict) -> str:
    if item.get("locked"):
        return (
            '<div class="card"><h3>' + esc(item.get("title", "")) + "</h3>"
            '<p class="muted small">' + esc(item.get("category", "")) + "</p>"
            '<p class="lock small">&#128274; Premium. <a href="/pricing">Subscribe to unlock</a></p></div>'
        )
    return (
        '<div class="card"><h3><a href="/item/' + esc(item["id"]) + '">' + esc(item["title"]) + "</a></h3>"
        '<p class="muted small">' + esc(item.get("category", "")) + "</p>"
        "<p>" + esc(item.get("summary", "")) + "</p></div>"
    )


def _paywall(request: Request, fields) -> str:
    names = ", ".join(LABELS.get(f, f) for f in fields) or "the full details"
    return (
        '<div class="card" style="border-color:#fbbf24"><h3 class="lock">&#128274; Premium content</h3>'
        "<p>Subscribe to unlock " + esc(names) + ".</p>"
        '<a class="btn" href="/pricing">Unlock for ' + esc(_price_text(request)) + " / month</a></div>"
    )


def _premium_block(view: dict) -> str:
    blocks = []
    for field in PREMIUM_FIELDS:
        value = view.get(field)
        if not value:
            continue
        label = esc(LABELS.get(field, field))
        href = rt.safe_href(value) if field.endswith(("link", "url")) else ""
        shown = (
            '<a href="' + esc(href) + '" rel="noopener noreferrer nofollow">' + esc(href) + "</a>"
            if href
            else esc(value)
        )
        blocks.append('<div class="card"><h3>' + label + "</h3><p>" + shown + "</p></div>")
    return "".join(blocks)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    access = rt.get_access(request)
    preview = rt.apply_access(ITEMS, PREMIUM_FIELDS, access)[:3]
    body = (
        '<section class="hero"><span class="badge">' + esc(SITE["why_now"]) + "</span>"
        "<h1>" + esc(SITE["name"]) + '</h1><p class="muted">' + esc(SITE["tagline"]) + "</p>"
        '<p><a class="btn" href="/pricing">See plans from ' + esc(_price_text(request)) + " / month</a> "
        '<a class="btn secondary" href="/explore">Browse free</a></p></section>'
        '<h2>Free preview</h2><div class="grid">' + "".join(_card(i) for i in preview) + "</div>"
        '<h2>What you get</h2><div class="cols">'
        '<div class="card"><h3>Free</h3>' + _ticks(SITE["free_features"]) + "</div>"
        '<div class="card"><h3>Premium</h3>' + _ticks(SITE["premium_features"])
        + '<a class="btn" href="/pricing">Go premium</a></div></div>'
    )
    return HTMLResponse(rt.page("Home", body, active="/", description=SITE["tagline"]))


_FILTER_JS = (
    "<script>(function(){var cat='',q='';var cells=[].slice.call(document.querySelectorAll('.cell'));"
    "function apply(){cells.forEach(function(c){var a=!cat||c.dataset.cat===cat;"
    "var b=!q||c.dataset.text.indexOf(q)>-1;c.style.display=a&&b?'':'none'})}"
    "document.getElementById('q').addEventListener('input',function(e){q=e.target.value.toLowerCase();apply()});"
    "[].forEach.call(document.querySelectorAll('.chip'),function(b){b.addEventListener('click',"
    "function(){cat=b.dataset.cat;apply()})})})();</script>"
)


@app.get("/explore", response_class=HTMLResponse)
def explore(request: Request):
    access = rt.get_access(request)
    items = rt.apply_access(ITEMS, PREMIUM_FIELDS, access)
    categories = sorted({i.get("category", "") for i in ITEMS if i.get("category")})
    chips = '<button class="btn secondary chip" data-cat="">All</button> ' + " ".join(
        '<button class="btn secondary chip" data-cat="' + esc(c) + '">' + esc(c) + "</button>" for c in categories
    )
    cells = "".join(
        '<div class="cell" data-cat="' + esc(i.get("category", "")) + '" data-text="'
        + esc((i.get("title", "") + " " + i.get("summary", "")).lower()) + '">' + _card(i) + "</div>"
        for i in items
    )
    note = (
        ""
        if access.subscriber
        else '<p class="small muted">You are seeing the free preview. <a href="/pricing">Subscribe</a> to unlock everything.</p>'
    )
    body = (
        "<h1>Explore</h1>" + note
        + '<p><input id="q" type="search" placeholder="Search" aria-label="Search"></p><p>' + chips + "</p>"
        + '<div class="grid">' + cells + "</div>" + _FILTER_JS
    )
    return HTMLResponse(rt.page("Explore", body, active="/explore"))


@app.get("/item/{item_id}", response_class=HTMLResponse)
def item_page(item_id: str, request: Request):
    access = rt.get_access(request)
    view = rt.find_item(ITEMS, item_id, PREMIUM_FIELDS, access) if ID_RE.match(item_id) else None
    if view is None:
        body = '<h1>Not found</h1><p><a href="/explore">Back to explore</a></p>'
        return HTMLResponse(rt.page("Not found", body), status_code=404)
    head = '<p class="muted small">' + esc(view.get("category", "")) + "</p><h1>" + esc(view["title"]) + "</h1>"
    if view.get("locked"):
        body = head + _paywall(request, view.get("locked_fields") or PREMIUM_FIELDS)
    else:
        body = head + "<p>" + esc(view.get("summary", "")) + "</p>"
        body += _premium_block(view) if access.subscriber else _paywall(request, view.get("locked_fields", []))
    return HTMLResponse(rt.page(view["title"], body, active="/explore"))


@app.get("/api/items")
def api_items(request: Request):
    access = rt.get_access(request)
    return {
        "items": rt.apply_access(ITEMS, PREMIUM_FIELDS, access),
        "subscriber": access.subscriber,
        "sample_data": SITE["sample_data"],
    }


@app.get("/api/items/{item_id}")
def api_item(item_id: str, request: Request):
    view = rt.find_item(ITEMS, item_id, PREMIUM_FIELDS, rt.get_access(request)) if ID_RE.match(item_id) else None
    if view is None:
        raise HTTPException(status_code=404, detail="Not found")
    return view


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/status")
def api_status():
    return {"service": SITE["name"], "status": "running", "sample_data": SITE["sample_data"]}
