import importlib.util, json, tempfile, unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'motion-refresh'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
motion=module('motion_apply_test',HERE/'apply.py')
media=module('motion_media_test',HERE/'build_media.py')
fixture='<!doctype html><html><head><title>Avenzo Digital</title></head><body><main><h1>Test</h1><a href="mailto:info@avenzodigital.nl">Mail</a></main></body></html>'
class MotionTests(unittest.TestCase):
 def test_main_is_unchanged(self):
  self.assertEqual(motion.main_fragment(fixture),motion.main_fragment(motion.enhance_html(fixture)))
 def test_idempotent(self):
  once=motion.enhance_html(fixture);self.assertEqual(once,motion.enhance_html(once))
 def test_only_one_script_and_stylesheet(self):
  text=motion.enhance_html(fixture);self.assertEqual(text.count(motion.CSS),1);self.assertEqual(text.count(motion.JS),1)
 def test_unknown_site_refused(self):
  with self.assertRaises(ValueError):motion.enhance_html(fixture.replace('Avenzo Digital','Other site'))
 def test_malformed_html_refused(self):
  with self.assertRaises(ValueError):motion.enhance_html(fixture.replace('</head>',''))
 def test_nested_output_refused(self):
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(ValueError):motion.build(Path(tmp),Path(tmp)/'output')
 def test_media_does_not_upscale(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);Image.new('RGB',(800,500)).save(p/'test.png')
   result=media.export_one('service-test',p/'test.png',p/'out')
   self.assertFalse(result['upscaled']);self.assertFalse(result['native_4k_width_available'])
   self.assertEqual(max(v['width'] for v in result['versions']),800)
   self.assertTrue(all(v['width']<=800 for v in result['versions']))
 def test_media_path_safety(self):
  with self.assertRaises(ValueError):media.export_one('../escape',Path('missing'),Path('out'))
 def test_source_contains_no_tracking_or_network_dependency(self):
  js=(HERE/'assets/avenzo-motion-20260909.js').read_text()
  for text in ['fetch(','XMLHttpRequest','sendBeacon','document.cookie','eval(','new Function']:
   self.assertNotIn(text,js)
 def test_all_recovery_main_content_preserved(self):
  recovery=ROOT/'recovery'
  pages=list(recovery.glob('*.html'))
  self.assertTrue(pages,'Recovery fixtures required')
  for p in pages:
   text=p.read_text();self.assertEqual(motion.main_fragment(text),motion.main_fragment(motion.enhance_html(text)))
if __name__=='__main__':unittest.main()
