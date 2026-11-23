from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from playwright.sync_api import sync_playwright

sources={
 'ziyu-verified-avatar':('https://avatars.githubusercontent.com/u/5800781?v=4&s=400','#ffffff'),
 'cvpr-mark':('https://cvpr.thecvf.com/static/core/img/cvpr-navbar-logo.svg','#ffffff'),
 'eccv-mark':('https://eccv.ecva.net/static/core/img/eccv-navbar-logo.svg','#22252b'),
 'iccv-mark':('https://iccv.thecvf.com/static/core/img/iccv-navbar-logo.svg','#22252b'),
 'iclr-mark':('https://iclr.cc/static/core/img/ICLR-logo.svg','#ffffff'),
 'ieee-mark':('https://media.icml.cc/Conferences/CVPR2023/img/ieee_cs_.svg','#ffffff'),
 'aaai-mark':('https://aaai.org/wp-content/uploads/2024/03/AAAI-Logo-Title-White.png','#142d53'),
 'neurips-mark':('https://neurips.cc/static/core/img/neurips-navbar-logo.svg','#282b31'),
 'microsoft-mark':('https://uhf.microsoft.com/images/microsoft/RE1Mu3b.png','#ffffff'),
}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome')
 for name,(url,bg) in sources.items():
  out=Path('capture/portraits')/name
  out.mkdir(parents=True,exist_ok=True)
  page=browser.new_page(viewport={'width':620,'height':400})
  try:
   from html import escape
   page.set_content(f'<body style="background:{bg};margin:0;display:flex;align-items:flex-start;"><img src="{escape(url, quote=True)}" alt="" style="width:340px;height:140px;object-fit:contain;">',wait_until='load',timeout=10000)
   image=page.locator('img')
   assert image.evaluate('e=>e.naturalWidth>0')
   if name=='ziyu-verified-avatar':
    image.evaluate("img=>{img.style.width='340px';img.style.height='340px'}")
   temp=out/'asset.png'
   image.screenshot(path=str(temp))
   with Image.open(temp) as data:data.convert('RGB').save(out/'asset.webp',quality=94)
   temp.unlink()
   (out/'source.txt').write_text(url)
  except Exception as exc:(out/'error.txt').write_text(str(exc).splitlines()[0] or type(exc).__name__)
  finally:page.close()
 browser.close()
