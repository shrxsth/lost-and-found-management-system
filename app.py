
"""Campus Lost and Found website. Run this file from VS Code."""

from datetime import date
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import webbrowser

DATA_FILE = Path(__file__).with_name("items.json")
CATEGORIES = ["Electronics", "ID / cards", "Wallet", "Keys", "Bags", "Books", "Clothing", "Other"]


def load_items():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            items = json.load(file)
        return items if isinstance(items, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_items(items):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(items, file, indent=2)


def safe(text):
    return escape(str(text), quote=True)


def match_score(lost, found):
    score = 0
    if lost["category"].lower() == found["category"].lower():
        score += 40
    if lost["location"].lower() == found["location"].lower():
        score += 30
    lost_words = set((lost["name"] + " " + lost["description"]).lower().split())
    found_words = set((found["name"] + " " + found["description"]).lower().split())
    score += min(len(lost_words & found_words) * 10, 30)
    return score


STYLE = """
body{font:16px Arial;background:#f4f7f5;color:#243b35;margin:0}
header{background:#176b55;color:white;padding:18px 6%;display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}
header a{color:white;margin-right:16px;text-decoration:none;font-weight:bold}
main{max-width:900px;margin:32px auto;padding:0 18px}
.card{background:white;padding:18px;margin:12px 0;border:1px solid #dce6df;border-radius:12px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
input,select,textarea{box-sizing:border-box;width:100%;padding:10px;margin:5px 0 13px;border:1px solid #bbc9c1;border-radius:7px}
textarea{height:90px}button,.button{background:#176b55;color:white;border:0;padding:10px 14px;border-radius:7px;cursor:pointer;text-decoration:none}
small,.muted{color:#61756d}.notice{background:#e3f4e8;padding:12px;border-radius:8px}
@media(max-width:600px){.grid{grid-template-columns:1fr}main{margin-top:20px}}
"""


def layout(title, page, content, message=""):
    links = """
    <a href="/?page=home">Home</a>
    <a href="/?page=report">Report item</a>
    <a href="/?page=items">Browse items</a>
    <a href="/?page=matches">Find matches</a>
    """
    note = f'<p class="notice">{safe(message)}</p>' if message else ""
    return f"""<!doctype html><html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{safe(title)} - Campus Lost and Found</title><style>{STYLE}</style></head>
    <body><header><strong>Campus Lost and Found</strong><nav>{links}</nav></header>
    <main>{note}{content}</main></body></html>"""


def home_page(items):
    lost = 0
    found = 0
    returned = 0
    for item in items:
        if item["status"] == "returned":
            returned += 1
        elif item["type"] == "LOST":
            lost += 1
        else:
            found += 1
    content = f"""
    <h1>Welcome</h1><p>Report lost belongings and help people find their items.</p>
    <div class="grid">
      <div class="card"><h2>{lost}</h2>Items reported lost</div>
      <div class="card"><h2>{found}</h2>Items found</div>
      <div class="card"><h2>{returned}</h2>Items returned</div>
    </div><p><a class="button" href="/?page=report">Make a report</a></p>"""
    return layout("Home", "home", content)


def report_page(error=""):
    options = "".join(f'<option>{safe(category)}</option>' for category in CATEGORIES)
    message = f'<p class="notice">{safe(error)}</p>' if error else ""
    content = f"""
    <h1>Report an item</h1>{message}
    <form method="post">
      <input type="hidden" name="action" value="report">
      <label>Type</label><select name="type"><option>LOST</option><option>FOUND</option></select>
      <label>Item name</label><input name="name" required>
      <label>Category</label><select name="category">{options}</select>
      <label>Location</label><input name="location" required>
      <label>Description</label><textarea name="description" required></textarea>
      <label>Contact details</label><input name="contact" required>
      <label>Date</label><input type="date" name="date" value="{date.today()}" required>
      <button type="submit">Save report</button>
    </form>"""
    return layout("Report item", "report", content)


def item_card(item):
    action = ""
    if item["status"] == "open":
        action = f"""<form method="post"><input type="hidden" name="action" value="return">
        <input type="hidden" name="id" value="{safe(item['id'])}">
        <button type="submit">Mark returned</button></form>"""
    return f"""<div class="card"><h3>{safe(item['type'])}: {safe(item['name'])}</h3>
    <p>{safe(item['description'])}</p>
    <p class="muted">Category: {safe(item['category'])} | Location: {safe(item['location'])}</p>
    <p class="muted">Date: {safe(item['date'])} | Status: {safe(item['status'])}</p>{action}</div>"""


def items_page(items, search=""):
    content = f"""<h1>Browse items</h1><form method="get">
    <input type="hidden" name="page" value="items">
    <input name="search" placeholder="Search reports" value="{safe(search)}">
    <button type="submit">Search</button></form>"""
    count = 0
    for item in items:
        words = (item["name"] + " " + item["category"] + " " + item["description"] + " " + item["location"]).lower()
        if search.lower() in words:
            content += item_card(item)
            count += 1
    if count == 0:
        content += '<p class="card">No reports found. Try another search or add a report.</p>'
    return layout("Browse items", "items", content)


def matches_page(items):
    content = "<h1>Possible matches</h1><p>Same category: 40 points; same location: 30; shared words: up to 30.</p>"
    count = 0
    for lost in items:
        for found in items:
            if lost["type"] == "LOST" and found["type"] == "FOUND" and lost["status"] == "open" and found["status"] == "open":
                score = match_score(lost, found)
                if score >= 50:
                    count += 1
                    content += f"""<div class="card"><h3>Match score: {score}</h3><div class="grid">
                    <p><b>Lost:</b> {safe(lost['name'])}<br>{safe(lost['description'])}<br>Contact: {safe(lost['contact'])}</p>
                    <p><b>Found:</b> {safe(found['name'])}<br>{safe(found['description'])}<br>Contact: {safe(found['contact'])}</p>
                    </div></div>"""
    if count == 0:
        content += '<p class="card">No likely matches yet.</p>'
    return layout("Find matches", "matches", content)


class Website(BaseHTTPRequestHandler):
    def send_page(self, content):
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, page):
        self.send_response(303)
        self.send_header("Location", "/?page=" + page)
        self.end_headers()

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        page = query.get("page", ["home"])[0]
        items = load_items()
        if page == "report":
            result = report_page()
        elif page == "items":
            result = items_page(items, query.get("search", [""])[0])
        elif page == "matches":
            result = matches_page(items)
        else:
            result = home_page(items)
        self.send_page(result)

    def do_POST(self):
        size = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(size).decode("utf-8"), keep_blank_values=True)
        action = form.get("action", [""])[0]
        items = load_items()

        if action == "report":
            item = {key: form.get(key, [""])[0].strip() for key in
                    ["type", "name", "category", "location", "description", "contact", "date"]}
            if not all(item.values()):
                self.send_page(report_page("Please fill in every field."))
                return
            item["id"] = len(items) + 1
            item["status"] = "open"
            items.append(item)
            save_items(items)
        elif action == "return":
            item_id = form.get("id", [""])[0]
            for item in items:
                if str(item["id"]) == item_id:
                    item["status"] = "returned"
            save_items(items)
        self.redirect("items")


if __name__ == "__main__":
    print("Starting website at http://127.0.0.1:8000")
    print("Stop it with Ctrl+C in the VS Code terminal.")
    server = HTTPServer(("127.0.0.1", 8000), Website)
    webbrowser.open("http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
