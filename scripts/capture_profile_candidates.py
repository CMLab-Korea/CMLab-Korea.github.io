import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
profiles={
 'geon-yeong-park-top':('https://geonyeong-park.github.io/','img, [role="img"]'),
 'agus-profile':('https://agusgun.github.io/','header img, img, [role="img"]'),
 'ziyu-github':('https://raywzy.github.io/','img, [role="img"]'),
 'geon-chang-lee-inshorts':('https://www.inshorts.ai/en','img, [role="img"]'),
 'logo-cornell-official':('https://tech.cornell.edu/','header a svg, header a img, header [class*="logo"], a[href="/"] svg'),
 'logo-neurips-official':('https://neurips.cc/','header a svg, .navbar-brand, nav [class*="logo"], a[href="/"] svg'),
}
def capture(item):
 name,(url,selector)=item
 dest=Path('capture/portraits')/name
 dest.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome')
  page=browser.new_page()
  try:
   response=page.goto(url,wait_until='domcontentloaded',timeout=18000)
   if not response.ok: raise RuntimeError(str(response.status))
   page.wait_for_timeout(1000)
   images=page.locator(selector)
   records=[]
   for idx in range(min(images.count(),40)):
    image=images.nth(idx)
    if not image.is_visible():continue
    size=image.bounding_box()
    if not size or size['width']<36 or size['height']<14:continue
    record=image.evaluate("""e=>({alt:e.getAttribute('alt'),html:e.outerHTML.slice(0,700),context:e.closest('article,section,header')?.innerText.slice(0,320)})""")
    record['idx']=idx
    records.append(record)
    try:
     file=dest/f'{idx:02}.png'
     image.screenshot(path=str(file),timeout=1000)
     with Image.open(file) as im:
      im.thumbnail((850,850));im.convert('RGB').save(dest/f'{idx:02}.webp',quality=90)
     file.unlink()
    except Exception:pass
    if len(records)>=8:break
   (dest/'sources.json').write_text(json.dumps({'url':page.url,'title':page.title(),'head':page.locator('body').inner_text()[:2200],'items':records},ensure_ascii=False,indent=2))
  except Exception as error:(dest/'error.txt').write_text(str(error).splitlines()[0])
  finally:browser.close()
with ThreadPoolExecutor(max_workers=6) as pool: list(pool.map(capture,profiles.items()))
