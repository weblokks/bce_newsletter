import asyncio, re, sys, pathlib, html
from playwright.async_api import async_playwright
HERE = pathlib.Path(__file__).parent
OUT = HERE/'qa'; OUT.mkdir(exist_ok=True)

def lint(path):
    s = path.read_text(encoding='utf-8')
    issues = []
    for m in re.finditer(r'<img\b[^>]*>', s):
        tag = m.group(0)
        for a in ('alt=', 'width=', 'height='):
            if a not in tag: issues.append(f'img ohne {a} {tag[:80]}')
        if 'alt=""' in tag: issues.append('leeres alt')
    hrefs = re.findall(r'href="([^"]*)"', s)
    for h in hrefs:
        if not re.match(r'^(https://|mailto:)', h): issues.append(f'Link verdächtig: {h}')
    for pat, why in [(r'\[[A-ZÄÖÜa-z][^\]]{2,}\]', 'Platzhalter in []'), (r'lorem|TODO|XXX|Platzhalter', 'Platzhaltertext'),
                     (r'\s[-–—]\s', 'freistehender Strich'), (r'display:\s*flex|position:|<style|<script|class=', 'nicht mailtaugliches CSS/HTML'),
                     (r"font-family:\s*'?(Inter|SCHABO)", 'Webfont zuerst im Stack'), (r'opacity:(?!0;)', 'opacity')]:
        clean = re.sub(r'<!--.*?-->', '', re.sub(r'<div style="display:none[^>]*>.*?</div>', '', s, flags=re.S), flags=re.S)
        for m in re.finditer(pat, clean, re.I):
            issues.append(f'{why}: …{m.group(0)[:60]}…')
    text = html.unescape(re.sub(r'<[^>]+>', ' ', s.split('<body')[1]))
    issues.append(f'INFO Größe {len(s.encode())/1024:.1f} KB, Links {len(hrefs)}, Ausrufezeichen {text.count("!")}')
    heads = re.findall(r'<h([1-6])', s); issues.append(f'INFO Überschriften-Folge {"".join(heads)}')
    return issues, sorted(set(hrefs))

async def shots(path):
    stem = path.stem
    photo = (HERE/'photo_stub.jpg').read_bytes(); logo = (HERE/'bce-logo-header.png').read_bytes()
    async with async_playwright() as p:
        br = await p.chromium.launch()
        async def run(name, w, images=True, js=None, mobile=False):
            ctx = await br.new_context(viewport={'width': w, 'height': 900}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile)
            pg = await ctx.new_page()
            async def route(r):
                u = r.request.url
                if not images and r.request.resource_type == 'image': return await r.abort()
                if u.endswith('.png'): return await r.fulfill(body=logo, content_type='image/png')
                if u.endswith('.jpg'): return await r.fulfill(body=photo, content_type='image/jpeg')
                await r.continue_()
            await pg.route('**/*', route)
            await pg.goto(path.resolve().as_uri()); await pg.wait_for_timeout(300)
            if js: await pg.evaluate(js)
            await pg.wait_for_timeout(200)
            sw = await pg.evaluate('document.documentElement.scrollWidth')
            await pg.screenshot(path=str(OUT/f'{stem}_{name}.png'), full_page=True)
            await ctx.close()
            return sw
        res = {}
        res['desktop'] = await run('desktop', 700)
        res['mobile'] = await run('mobile375', 375, mobile=True)
        res['bilder_aus'] = await run('bilder_aus', 375, images=False, mobile=True)
        res['dark_invert'] = await run('dark_invert', 375, mobile=True, js="""document.documentElement.style.filter='invert(1) hue-rotate(180deg)';document.querySelectorAll('img').forEach(i=>i.style.filter='invert(1) hue-rotate(180deg)')""")
        res['langtext'] = await run('langtext', 320, mobile=True, js="""document.querySelectorAll('h1,h2,h3').forEach(h=>h.innerHTML+=' Donaudampfschifffahrtsgesellschaft');document.querySelectorAll('td').forEach(td=>{if(td.textContent.trim()==='bisher Alexander Hüller')td.textContent='bisher Maximilian-Alexander von Hohenzollern-Sigmaringen'})""")
        await br.close()
        return res

async def main():
    for f in sys.argv[1:]:
        f = pathlib.Path(f)
        issues, hrefs = lint(f)
        print('==', f.name); [print('  ', i) for i in issues]
        print('   Links:'); [print('    ', h[:130]) for h in hrefs]
        print('   scrollWidth je Szenario:', await shots(f))
asyncio.run(main())
