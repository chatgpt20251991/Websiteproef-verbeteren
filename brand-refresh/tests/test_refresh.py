import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('avenzo_refresh',ROOT/'apply.py')
refresh=importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)
FIXTURE='''<!doctype html><html lang="nl"><head><title>Home | Avenzo Digital</title></head><body><header class="site-header"><div class="header-inner"><a class="brand" href="/" aria-label="Avenzo Digital — home"><span class="brand-name">avenzo</span><span class="brand-sub">DIGITAL</span></a><button class="menu-toggle" aria-expanded="false">Menu</button></div></header><main id="inhoud"><h1>Van visie.</h1><form id="contact-form"><input name="email" type="email"></form></main><footer class="site-footer"><p>Old footer</p></footer><script src="/assets/compiled/app.15bbad9d28a8afd3.js" defer></script></body></html>'''

class RefreshTests(unittest.TestCase):
    def test_replaces_exactly_two_logos(self):
        result=refresh.refresh_html(FIXTURE)
        self.assertEqual(result.count('<img src="/assets/avenzo-wordmark-20260909.svg"'),2)
        self.assertNotIn('brand-name',result)
    def test_main_and_form_preserved(self):
        before=re.search(r'<main.*?</main>',FIXTURE,re.S).group()
        self.assertIn(before,refresh.refresh_html(FIXTURE))
    def test_existing_script_and_menu_preserved(self):
        result=refresh.refresh_html(FIXTURE)
        self.assertIn('<button class="menu-toggle" aria-expanded="false">Menu</button>',result)
        self.assertIn('<script src="/assets/compiled/app.15bbad9d28a8afd3.js" defer></script>',result)
    def test_idempotent(self):
        once=refresh.refresh_html(FIXTURE)
        self.assertEqual(once,refresh.refresh_html(once))
        self.assertEqual(once.count(refresh.CSS_LINK),1)
    def test_unknown_site_rejected(self):
        with self.assertRaises(ValueError): refresh.refresh_html(FIXTURE.replace('Avenzo Digital','Other company'))
    def test_missing_footer_rejected(self):
        with self.assertRaises(ValueError): refresh.refresh_html(FIXTURE.replace('class="site-footer"','class="other"'))
    def test_duplicate_footer_rejected(self):
        with self.assertRaises(ValueError): refresh.refresh_html(FIXTURE.replace('</body>','<footer class="site-footer"></footer></body>'))
    def test_two_mail_addresses_and_kvk(self):
        result=refresh.refresh_html(FIXTURE)
        for item in ['mailto:info@avenzodigital.nl','mailto:avenzodigitalgroup@gmail.com','94554692','Projectaanvragen','Algemene vragen']:
            self.assertIn(item,result)
    def test_no_invented_social_links(self):
        result=refresh.refresh_html(FIXTURE)
        self.assertNotIn('linkedin.com',result)
        self.assertNotIn('instagram.com',result)
        self.assertNotRegex(result,r'href="#"')
    def test_only_platform_challenge_removed(self):
        source=FIXTURE.replace('</body>',"<script>window.__CF$cv$params={};</script><script>console.log('keep')</script></body>")
        result=refresh.refresh_html(source)
        self.assertNotIn('__CF$cv$params',result)
        self.assertIn("console.log('keep')",result)
    def test_output_separate_and_assets_present(self):
        with tempfile.TemporaryDirectory() as temp:
            src=Path(temp)/'source';src.mkdir();(src/'index.html').write_text(FIXTURE)
            out=Path(temp)/'output';m=refresh.apply_directory(src,out)
            self.assertFalse(m['deployment_performed'])
            self.assertTrue((out/'index.html').exists())
            self.assertTrue((out/'assets'/refresh.ASSETS[0]).exists())
            self.assertEqual((src/'index.html').read_text(),FIXTURE)
            with self.assertRaises(ValueError):refresh.apply_directory(src,src)
            with self.assertRaises(ValueError):refresh.apply_directory(src,out)
    def test_all_validation_before_write(self):
        with tempfile.TemporaryDirectory() as temp:
            src=Path(temp)/'source';src.mkdir();(src/'index.html').write_text(FIXTURE)
            (src/'broken.html').write_text(FIXTURE.replace('class="site-footer"','class="unexpected"'))
            out=Path(temp)/'output'
            with self.assertRaises(ValueError):refresh.apply_directory(src,out)
            self.assertFalse(out.exists())
    def test_vector_is_asset_not_font(self):
        svg=(ROOT/'assets'/refresh.ASSETS[0]).read_text()
        self.assertIn('viewBox="0 0 2062 509"',svg)
        self.assertNotIn('<text',svg)
        self.assertNotIn('<script',svg)
        self.assertNotIn('data:',svg)

if __name__=='__main__':unittest.main()
