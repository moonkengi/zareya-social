#!/usr/bin/env python3
"""Zareya social post renderer. Usage: python3 render.py post.json OUTDIR
Slides (1080x1350 JPEG):
  cover     dark grid, kicker, title, optional sub
  statement dark grid single post (kicker, title, sub)
  point     light teaching slide (auto numbered), title, body
  cta       dark closing slide, title, button
In any title, wrap a phrase in *asterisks* to set it in italic serif inside the pink selection box.
"""
import base64, json, os, re, sys, html
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
def b64(p): return base64.b64encode(open(p, 'rb').read()).decode()
FS = os.path.join(HERE, 'node_modules/@fontsource')
def face(fam, d, w, st='normal'):
    return (f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:{st};"
            f"src:url(data:font/woff2;base64,{b64(f'{FS}/{d}/files/{d}-latin-{w}-{st}.woff2')})}}")
FONTS = (face('LS', 'league-spartan', 700) + face('PP', 'poppins', 400) + face('PP', 'poppins', 500)
         + face('PP', 'poppins', 600) + face('IS', 'instrument-serif', 400, 'italic'))
LP = 'data:image/png;base64,' + b64(os.path.join(HERE, 'logo_pink.png'))
LW = 'data:image/png;base64,' + b64(os.path.join(HERE, 'logo_white.png'))

CSS = FONTS + """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden}
.s{position:relative;width:1080px;height:1350px;padding:0 80px;display:flex;flex-direction:column;font-family:'PP'}
.dark{background:#120011;color:#fff7fd}
.dark:before{content:'';position:absolute;inset:0;pointer-events:none;
 background-image:linear-gradient(rgba(255,255,255,.09) 1.5px,transparent 1.5px),linear-gradient(90deg,rgba(255,255,255,.09) 1.5px,transparent 1.5px);
 background-size:90px 90px;background-position:-1px -1px}
.dark:after{content:'';position:absolute;inset:0;pointer-events:none;
 background:radial-gradient(55% 40% at 100% 0%,rgba(255,3,237,.28),transparent 70%),
            radial-gradient(50% 38% at 0% 100%,rgba(255,3,237,.42),transparent 70%)}
.light{background:#fdf6fb;color:#32002f}
.s>*{position:relative;z-index:1}
.top{height:198px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid}
.dark .top,.dark .bot{border-color:rgba(255,247,253,.2)} .light .top,.light .bot{border-color:rgba(50,0,47,.14)}
.top img{height:40px}
.cnt{font-weight:500;letter-spacing:.12em;font-size:30px;opacity:.75}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center}
.bot{height:150px;border-top:2px solid;display:flex;align-items:center;
 font-weight:600;letter-spacing:.22em;font-size:28px;text-transform:uppercase;opacity:.7}
.bar{width:120px;height:6px;border-radius:3px;background:linear-gradient(90deg,#ff03ed,#ffb3f8);margin-bottom:34px}
.kick{font-weight:600;letter-spacing:.2em;font-size:28px;text-transform:uppercase;opacity:.75;margin-bottom:30px}
h1{font-family:'LS';font-weight:700;letter-spacing:-.02em;line-height:1.06}
.cover h1,.statement h1{font-size:104px}.cta h1{font-size:90px}
.hl{position:relative;display:inline-block;font-family:'IS';font-style:italic;font-weight:400;letter-spacing:0;
 font-size:1.12em;line-height:1;padding:.02em .16em .1em;margin:.06em 0;background:rgba(255,3,237,.30);
 border-left:5px solid #ff03ed;border-right:5px solid #ff03ed}
.hl:before,.hl:after{content:'';position:absolute;width:24px;height:24px;border-radius:50%;background:#ff03ed}
.hl:before{left:-14.5px;top:-20px}.hl:after{right:-14.5px;bottom:-20px}
.light .hl{background:rgba(255,3,237,.14)}
.sub{margin-top:48px;font-size:44px;line-height:1.3;max-width:760px;opacity:.9}
.sub i{font-family:'IS';font-size:1.15em}
.num{font-family:'LS';font-weight:700;font-size:250px;line-height:.85;letter-spacing:-.04em;margin-bottom:40px;
 background:linear-gradient(90deg,#ff03ed,#7a0074);-webkit-background-clip:text;color:transparent;width:max-content}
.point h1{font-size:84px;margin-bottom:34px}
.body{font-size:40px;line-height:1.38;color:#6b5a69;max-width:860px}
.btn{margin-top:70px;align-self:flex-start;background:#ff03ed;color:#fff;border-radius:60px;padding:26px 50px;font-weight:600;font-size:36px}
"""

def rich(t):
    t = html.escape(t)
    return re.sub(r'\*(.+?)\*', r'<span class=hl>\1</span>', t)

def slide(s, i, n, tag, pn):
    t = s['type']; g = lambda k: s.get(k, '')
    dark = t != 'point'
    cnt = f'{i:02d} / {n:02d}' if n > 1 else ''
    kick = f"<div class=kick>{html.escape(g('kicker'))}</div>" if g('kicker') else ''
    sub = f"<div class=sub>{rich(g('sub')).replace('class=hl','class=x')}</div>" if g('sub') else ''
    if t in ('cover', 'statement'):
        mid = f"<div class=bar></div>{kick}<h1>{rich(g('title'))}</h1>{sub}"
    elif t == 'point':
        mid = f"<div class=num>{pn:02d}</div><h1>{rich(g('title'))}</h1><div class=body>{html.escape(g('body'))}</div>"
    else:
        mid = (f"<div class=bar></div><h1>{rich(g('title'))}</h1>"
               f"<div class=btn>{html.escape(g('button') or 'Send us a DM')}</div>")
    foot = 'zareya.co.ke' if t == 'cta' or not tag else ('African brands, brilliantly told' if t == 'statement' else html.escape(tag))
    return (f"<div class='s {'dark' if dark else 'light'} {t}'><div class=top><img src='{LW if dark else LP}'>"
            f"<div class=cnt>{cnt}</div></div><div class=mid>{mid}</div><div class=bot>{foot}</div></div>")

def render(post, out):
    os.makedirs(out, exist_ok=True)
    sl = post['slides']; files = []; pn = 0
    with sync_playwright() as p:
        chrome = '/usr/bin/google-chrome'
        b = p.chromium.launch(executable_path=chrome if os.path.exists(chrome) else None)
        pg = b.new_page(viewport={'width': 1080, 'height': 1350})
        for i, s in enumerate(sl, 1):
            if s['type'] == 'point': pn += 1
            pg.set_content(f"<html><head><style>{CSS}</style></head><body>{slide(s, i, len(sl), post.get('tag', ''), pn)}</body></html>")
            pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(150)
            f = os.path.join(out, f'{i:02d}.jpg'); pg.screenshot(path=f, type='jpeg', quality=90); files.append(f)
        b.close()
    return files

if __name__ == '__main__':
    print('\n'.join(render(json.load(open(sys.argv[1])), sys.argv[2])))
