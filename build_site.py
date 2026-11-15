"""Build a static HTML site from the Markdown lessons into docs/ (no Jekyll, no dependencies at view time)."""
import os, re, html, shutil, markdown2
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
FOLDERS = sorted(d for d in os.listdir(ROOT) if re.match(r"^\d\d-", d) and os.path.isdir(os.path.join(ROOT, d)))
LABEL = {"01-dsa": "Data structures and algorithms", "02-system-design": "System design", "03-low-level-design": "Low-level design",
         "05-devops-platform-basics": "DevOps and platform basics", "06-company-process-and-behavioural": "Company processes"}
def title_of(path):
    for l in open(path, encoding="utf-8"):
        m = re.match(r"^#\s+(.*)", l)
        if m: return re.sub(r"[`*_]", "", m.group(1)).strip()
    return os.path.splitext(os.path.basename(path))[0].replace("_", " ")
pages = []  # (folder, md name, html name, title)
for d in FOLDERS:
    for f in sorted(os.listdir(os.path.join(ROOT, d))):
        if f.endswith(".md"): pages.append((d, f, f[:-3] + ".html", title_of(os.path.join(ROOT, d, f))))
CSS = """
:root{--bg:#fff;--fg:#1f2328;--mut:#59636e;--bd:#d1d9e0;--ac:#0b57d0;--cb:#f6f8fa;--sb:#f6f8fa}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--bd:#30363d;--ac:#6cb6ff;--cb:#161b22;--sb:#010409}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{display:flex;min-height:100vh}nav{width:300px;flex:none;background:var(--sb);border-right:1px solid var(--bd);padding:16px;overflow:auto;position:sticky;top:0;height:100vh}
nav a{color:var(--fg);text-decoration:none;display:block;padding:3px 6px;border-radius:6px;font-size:14px}nav a:hover{background:var(--cb)}nav a.cur{background:var(--ac);color:#fff}
nav summary{cursor:pointer;font-weight:600;padding:6px 0}nav .home{font-weight:700;font-size:16px;margin-bottom:8px}
main{flex:1;min-width:0;max-width:900px;padding:24px 32px 80px;margin:0 auto}
h1,h2,h3{line-height:1.25}h1{border-bottom:1px solid var(--bd);padding-bottom:.3em}h2{border-bottom:1px solid var(--bd);padding-bottom:.25em;margin-top:2em}
a{color:var(--ac)}pre{background:var(--cb);border:1px solid var(--bd);border-radius:8px;padding:14px;overflow:auto;font-size:13.5px;line-height:1.5}
code{background:var(--cb);padding:.15em .35em;border-radius:5px;font-size:.92em}pre code{background:none;padding:0}
table{border-collapse:collapse;display:block;overflow:auto;max-width:100%}th,td{border:1px solid var(--bd);padding:6px 10px;text-align:left;vertical-align:top}th{background:var(--cb)}
blockquote{border-left:4px solid var(--bd);margin:0;padding:0 1em;color:var(--mut)}img{max-width:100%}
.top{display:none}.pn{display:flex;justify-content:space-between;gap:12px;margin-top:48px;border-top:1px solid var(--bd);padding-top:16px;font-size:14px}
@media(max-width:820px){.wrap{display:block}nav{width:auto;height:auto;position:static;border-right:0;border-bottom:1px solid var(--bd)}main{padding:16px}}
"""
def nav_html(cur_rel):
    o = ['<nav><a class="home" href="%sindex.html">Interview prep</a>' % ("../" if "/" in cur_rel else "")]
    for d in FOLDERS:
        op = " open" if cur_rel.startswith(d + "/") else ""
        o.append("<details%s><summary>%s</summary>" % (op, html.escape(LABEL.get(d, d))))
        for (fd, mdn, hn, t) in pages:
            if fd != d: continue
            href = ("" if cur_rel.startswith(d + "/") else d + "/") + hn
            if "/" in cur_rel and not cur_rel.startswith(d + "/"): href = "../" + d + "/" + hn
            cls = ' class="cur"' if cur_rel == d + "/" + hn else ""
            o.append('<a%s href="%s">%s</a>' % (cls, href, html.escape(re.sub(r"^\d+[a-z]?\.?\s*", "", t)[:60])))
        o.append("</details>")
    o.append("</nav>")
    return "".join(o)
def render(md_text):
    body = markdown2.markdown(md_text, extras=["fenced-code-blocks", "tables", "header-ids", "strike", "task_list", "cuddled-lists", "code-friendly"])
    body = re.sub(r'href="([^":#]+)\.md(#[^"]*)?"', lambda m: 'href="%s.html%s"' % (m.group(1), m.group(2) or ""), body)
    return body
def page(title, body, cur_rel, prev=None, nxt=None):
    pn = ""
    if prev or nxt:
        pn = '<div class="pn"><span>%s</span><span>%s</span></div>' % (('<a href="%s">&larr; %s</a>' % prev) if prev else "", ('<a href="%s">%s &rarr;</a>' % nxt) if nxt else "")
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s | Interview prep</title><style>%s</style></head><body><div class="wrap">%s<main>%s%s</main></div></body></html>') % (html.escape(title), CSS, nav_html(cur_rel), body, pn)
if os.path.isdir(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
open(os.path.join(OUT, ".nojekyll"), "w").write("")
for i, (d, mdn, hn, t) in enumerate(pages):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
    same = [p for p in pages if p[0] == d]; j = same.index((d, mdn, hn, t))
    prev = (same[j-1][2], html.escape(same[j-1][3][:40])) if j > 0 else None
    nxt = (same[j+1][2], html.escape(same[j+1][3][:40])) if j + 1 < len(same) else None
    body = render(open(os.path.join(ROOT, d, mdn), encoding="utf-8").read())
    open(os.path.join(OUT, d, hn), "w", encoding="utf-8").write(page(t, body, d + "/" + hn, prev, nxt))
readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
home = render(readme)
home = re.sub(r'href="(\d\d-[^"/]+)/"', r'href="\1/"', home)
# folder links in README point to directories: send them to the first page of the folder
for d in FOLDERS:
    first = [p for p in pages if p[0] == d][0][2]
    home = home.replace('href="%s/"' % d, 'href="%s/%s"' % (d, first))
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page("Interview prep", home, "index.html"))
print("built", len(pages), "pages")
