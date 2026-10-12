"""Visualization output generated from a *validated* RCPL model.

The renderer only reads the textX model object (never the raw pipeline data),
so every visualization corresponds to a specification accepted by the grammar.
"""

from __future__ import annotations

from html import escape

from .catalog import CATEGORY_TITLES
from .profiles import PROFILES

_CSS = """
:root{
  --ink:#1d2433; --muted:#5f6b7d; --paper:#f6f7f9; --sheet:#ffffff;
  --rule:#d7dce4; --state:#2c4a8a; --accept:#0f766e; --reject:#a1403a;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.55 "Work Sans","Segoe UI",system-ui,sans-serif}
main{max-width:860px;margin:40px auto;padding:40px 44px;background:var(--sheet);
  border:1px solid var(--rule);border-radius:6px}
h1{font:600 2.3rem/1.15 "Source Serif 4",Georgia,serif;margin:0 0 .3rem}
h2{font:600 1.15rem/1.3 "Source Serif 4",Georgia,serif;margin:2.2rem 0 .8rem;
  padding-bottom:.35rem;border-bottom:1px solid var(--rule)}
.lede{color:var(--muted);margin:0 0 .8rem}
.contact{display:flex;flex-wrap:wrap;gap:.4rem 1.4rem;margin:0;padding:0;list-style:none}
.contact a{color:var(--state)}
.tok{font:500 .82rem/1 "IBM Plex Mono",Consolas,monospace;letter-spacing:.01em}
.match{margin:0 0 1.4rem}
.match h3{margin:0 0 .15rem;font-size:1.02rem}
.match p{margin:0 0 .6rem;color:var(--muted);font-size:.92rem}
.path{display:flex;flex-wrap:wrap;align-items:center;row-gap:.8rem;padding:.5rem 0 .9rem}
.node{flex:0 0 auto;width:40px;height:40px;border-radius:50%;border:2px solid var(--state);
  display:grid;place-items:center;font:600 .78rem "IBM Plex Mono",monospace;color:var(--state)}
.node.final{box-shadow:0 0 0 3px var(--sheet),0 0 0 5px var(--accept);
  border-color:var(--accept);color:var(--accept)}
.edge{flex:0 0 auto;display:flex;flex-direction:column;align-items:center;padding:0 .3rem;
  min-width:92px}
.edge .tok{color:var(--ink);padding-bottom:.25rem}
.edge .line{height:2px;width:100%;background:var(--state);position:relative}
.edge .line::after{content:"";position:absolute;right:-1px;top:-4px;
  border-left:8px solid var(--state);border-top:5px solid transparent;border-bottom:5px solid transparent}
.status{font-weight:600}
.status.ok{color:var(--accept)} .status.no{color:var(--reject)}
table{width:100%;border-collapse:collapse;font-size:.95rem}
td,th{text-align:left;padding:.45rem .5rem;border-bottom:1px solid var(--rule);vertical-align:top}
th{font-weight:600;width:34%}
.skills .tok{display:inline-block;margin:0 .35rem .35rem 0;padding:.3rem .45rem;
  border:1px solid var(--rule);border-radius:3px;background:var(--paper)}
.rejected li{margin-bottom:.35rem}
footer{margin-top:2.4rem;color:var(--muted);font-size:.82rem}
@media (max-width:640px){main{margin:0;border:0;border-radius:0;padding:24px 18px}
  h1{font-size:1.8rem}}
"""


_KIND = {"DFA": "DFA", "NFA": "NFA", "ENFA": "ε-NFA"}


def _path_html(result) -> str:
    parts = ['<div class="path" role="img" aria-label="Accepting path">',
             '<span class="node">0</span>']
    n = len(result.sequence)
    for i, tok in enumerate(result.sequence, start=1):
        cls = "node final" if i == n else "node"
        parts.append(f'<span class="edge"><span class="tok">{escape(tok)}</span>'
                     f'<span class="line"></span></span><span class="{cls}">{i}</span>')
    parts.append("</div>")
    return "".join(parts)


def to_html(model) -> str:
    name = escape(model.candidate.name)
    exp = model.experience
    lede = []
    if exp is not None and exp.total is not None:
        lede.append(f"{exp.total} years of experience")
    if exp is not None and exp.summary:
        lede.append(escape(exp.summary))

    contact = []
    for item in model.contact.items:
        cls = item.__class__.__name__
        if cls == "EmailItem":
            contact.append(f'<li><a href="mailto:{escape(item.value)}">{escape(item.value)}</a></li>')
        elif cls == "PhoneItem":
            contact.append(f"<li>{escape(item.value)}</li>")
        else:
            contact.append(f'<li><a href="{escape(item.value)}">{escape(item.kind)}</a></li>')

    accepted = [r for r in model.classification.results if r.status == "ACCEPTED"]
    rejected = [r for r in model.classification.results if r.status == "REJECTED"]

    body = [f"<header><h1>{name}</h1>"]
    if lede:
        body.append(f'<p class="lede">{" — ".join(lede)}</p>')
    if contact:
        body.append(f'<ul class="contact">{"".join(contact)}</ul>')
    body.append("</header>")

    body.append("<section><h2>Profile patterns satisfied</h2>")
    if accepted:
        for r in accepted:
            p = PROFILES[r.profile]
            body.append(
                f'<div class="match"><h3>{escape(p.title)} '
                f'<span class="status ok">accepted</span></h3>'
                f"<p>Recognised by the {_KIND[r.automaton]} of the profile. Each arrow is "
                f"one symbol of the canonical sequence; the double circle marks "
                f"acceptance.</p>"
                f"{_path_html(r)}</div>")
    else:
        body.append("<p>No supported profile pattern is satisfied by the qualifications "
                    "found in this résumé.</p>")
    if rejected:
        body.append('<ul class="rejected">')
        for r in rejected:
            miss = ", ".join(escape(m) for m in r.missing) or "order or pattern mismatch"
            body.append(f"<li>{escape(PROFILES[r.profile].title)}: "
                        f'<span class="status no">not satisfied</span>. Missing: {miss}.</li>')
        body.append("</ul>")
    body.append("</section>")

    if model.skills.groups:
        body.append('<section class="skills"><h2>Normalized qualifications</h2><table>')
        for g in model.skills.groups:
            toks = "".join(f'<span class="tok">{escape(s)}</span>' for s in g.skills)
            body.append(f"<tr><th>{escape(CATEGORY_TITLES[g.category])}</th><td>{toks}</td></tr>")
        body.append("</table></section>")

    if model.education is not None:
        body.append("<section><h2>Education</h2><table>")
        for d in model.education.records:
            where = escape(d.institution) if d.institution else ""
            year = f" ({d.year})" if d.year else ""
            body.append(f"<tr><th>{d.level.title()}</th>"
                        f"<td>{escape(d.title)}<br><small>{where}{year}</small></td></tr>")
        body.append("</table></section>")

    if exp is not None and exp.jobs:
        body.append("<section><h2>Experience</h2><table>")
        for j in exp.jobs:
            end = "present" if j.end == "PRESENT" else j.end
            body.append(f"<tr><th>{j.start} – {end}</th>"
                        f"<td>{escape(j.role)}, {escape(j.company)}</td></tr>")
        body.append("</table></section>")

    body.append("<footer>Generated by ResumeLens from a validated candidate profile "
                "specification. ResumeLens checks qualification patterns only; it does "
                "not rank candidates or make hiring decisions.</footer>")

    return ("<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{name} · ResumeLens</title>"
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600'
            '&family=Source+Serif+4:wght@600&family=Work+Sans:wght@400;600&display=swap" '
            'rel="stylesheet">'
            f"<style>{_CSS}</style></head><body><main>{''.join(body)}</main></body></html>\n")