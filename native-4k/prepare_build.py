#!/usr/bin/env python3
"""Small explicit, idempotent build corrections for this Avenzo source version."""
from pathlib import Path

here=Path(__file__).resolve().parent
render=here/'render.py'
s=render.read_text()
s=s.replace('Anisotropic IOR Level','Anisotropic')
compile(s,str(render),'exec')
render.write_text(s)

assembler=here/'assemble.py'
s=assembler.read_text()
old="soup=BeautifulSoup(html,'html.parser');before=soup.main.get_text(' ',strip=True);changes=0"
new=old+"\n        for preload in soup.select('link[as=font]'):\n            if preload.get('href','') == '/assets/body.woff':\n                preload['href']='https://avenzodigital.nl/assets/body.woff'"
if "for preload in soup.select('link[as=font]')" not in s:
    if old not in s:raise RuntimeError('Unexpected assembly template: font reference')
    s=s.replace(old,new)
old="elif stem.startswith('hero-'):el['sizes']='100vw'"
new="elif stem=='hero-desktop-apps':el['sizes']='(min-width: 1280px) 100vw, (min-width: 1025px) 1210px, (min-width: 761px) 1032px, 100vw'\n            elif stem=='hero-mobile-apps':el['sizes']='100vw'"
if old in s:s=s.replace(old,new)
if "shutil.copy2(Path(__file__).parent/'resolution.js'" not in s:
    old="for name in brand.ASSETS:shutil.copy2(refresh_path.parent/'assets'/name,assets/name)"
    if old not in s:raise RuntimeError('Unexpected assembly template: native resolution script')
    s=s.replace(old,old+"\n    shutil.copy2(Path(__file__).parent/'resolution.js',assets/'avenzo-native-resolution.js')")
if "soup.new_tag('script',src='/assets/avenzo-native-resolution.js')" not in s:
    old="for el in soup.select('img,source'):"
    if old not in s:raise RuntimeError('Unexpected assembly template: native script link')
    new="script=soup.new_tag('script',src='/assets/avenzo-native-resolution.js');script['defer']='';soup.head.append(script)\n        "+old
    s=s.replace(old,new)
compile(s,str(assembler),'exec')
assembler.write_text(s)
print('Verified build corrections: Blender socket, retained remote font and measured crop-aware source selection.')
