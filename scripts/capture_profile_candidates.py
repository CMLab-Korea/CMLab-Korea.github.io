import json,re,time
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit
from concurrent.futures import ThreadPoolExecutor
pages={
'geon-yeong-park':'https://geonyeong-park.github.io/',
'jae-shin-yoon':'https://gorokee.github.io/jsyoon/',
'ziyu-wan':'https://raywzy.com/',
'sangwoon-kwak':'https://skwak-kaist.github.io/',
'kyle-min':'https://sites.google.com/view/kylemin',
'soo-ye-kim':'https://sites.google.com/view/sooyekim',
'juan-luis-gonzalez-bello':'https://sites.google.com/view/juan-luis-gb/home',
'agus-gunawan':'https://agusgun.github.io/',
'geon-chang-lee':'https://www.linkedin.com/in/andy-lee-b4122a98/',
'taekyung-kim':'https://taekyungkim918.github.io/',
'logo-cornell-tech':'https://tech.cornell.edu/',
'logo-microsoft':'https://www.microsoft.com/en-us/',
'logo-ieee':'https://www.ieee.org/',
'logo-cvpr':'https://cvpr.thecvf.com/',
'logo-eccv':'https://eccv.ecva.net/',
'logo-iccv':'https://iccv.thecvf.com/',
'logo-aaai':'https://aaai.org/',
'logo-neurips':'https://neurips.cc/',
'logo-iclr':'https://iclr.cc/'
}
def capture(item):
 slug,url=item
 target=Path('capture/portraits')/slug
 target.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
  page=b.new_page()
  try:
   response=page.goto(url,wait_until='domcontentloaded',timeout=23000)
   if response and not response.ok:raise RuntimeError(str(response.status))
   page.wait_for_timeout(1500)
   links=page.evaluate("""() => [...document.querySelectorAll('a[href]')].map(a=>({url:a.href,label:a.innerText.trim()})).filter(a=>a.label)""")
   (target/'links.json').write_text(json.dumps(links,ensure_ascii=False,indent=2))
   if slug.endswith('-lab'):
    candidate=next((x['url'] for x in links if re.search(r'professor|faculty|^PI$',x['label'],re.I)
      and urlsplit(x['url']).netloc==urlsplit(page.url).netloc),None)
    if candidate:
     page.goto(candidate,wait_until='domcontentloaded',timeout=20000)
     page.wait_for_timeout(1400)
   candidates=page.evaluate(r"""isLogo => [...document.images].filter(i=>isLogo || !i.closest('header, nav, footer')).map(i=>{
    const box=i.closest('section, article, li, tr')||i.parentElement?.parentElement;
    return {url:i.currentSrc||i.src,alt:i.alt,context:box?.innerText?.trim().slice(0,370)||'',w:i.naturalWidth,h:i.naturalHeight};
   }).filter(i=>isLogo ? i.w>=80 && i.h>=16 : i.w>=85 && i.h>=85).slice(0, isLogo ? 10 : 5)""",slug.startswith('logo-'))
   (target/'sources.json').write_text(json.dumps({'title':page.title(),'url':page.url,'head':page.locator('body').inner_text()[:2400],'items':candidates},ensure_ascii=False,indent=2))
   for i,item in enumerate(candidates):
    im=page.locator('img').evaluate_all('(items,url)=>items.findIndex(i=>(i.currentSrc||i.src)===url)',item['url'])
    if im<0:continue
    try:
     page.locator('img').nth(im).screenshot(path=str(target/f'{i:02}.png'),timeout=1800,scale='css')
     f=target/f'{i:02}.png'
     with Image.open(f) as img:
      img.thumbnail((850,850));img.convert('RGB').save(target/f'{i:02}.webp',quality=89)
     f.unlink()
    except Exception:continue
  except Exception as e:(target/'error.txt').write_text(str(e).splitlines()[0])
  finally:b.close()
with ThreadPoolExecutor(max_workers=6) as pool: list(pool.map(capture,pages.items()))
