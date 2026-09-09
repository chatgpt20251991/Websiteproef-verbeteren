# Avenzo Cinematic: complete delivery

## Delivered files in the Avenzo conversation

- `Avenzo_Cinematic_complete_website.html`: self-contained implementation of all nine pages, with embedded cinematic media. SHA-256: `6e8703a128e6359bba5491d124bc07c61fc81f469258330dd217507d15f4d7d8`.
- `Avenzo_Cinematic_website_en_broncode.zip`: complete static website, editable CSS/JS, generator and original content, editable Blender scene, 72 original frames, production code, reproducible checks and reports.
- `Avenzo_Cinematic_homepage.png` and `Avenzo_Cinematic_mobiel.png`: actual browser captures.
- `Avenzo_Cinematic_controleverslag.md`: detailed verification and limitations.

**The complete website source is in the attached ZIP, not fully uploaded to this repository.** This branch contains rendering source/workflows and this accurate delivery record. Do not mistake the older `motion-refresh` implementation for the new cinematic site.

## Actual implementation

Original physically rendered mechanical composition replaces the earlier small computer/robot scene. Authored metal materials, lighting, iris blades, separate moving housings and camera choreography. A cinematic opening starts automatically, without a play button or demo screen. Scroll position controls a second film. All six service routes, Studio and Contact are included, with the approved SVG wordmark, contact footer, both mail addresses and KvK 94554692.

This is pre-rendered physical 3D used as cinematic website media, **not freely manipulable realtime WebGL**. All 72 different source frames are native 3840x2160; no upscaling or motion interpolation. Optimized 1920 and 2560 variants are provided. The 6.583-second hero loop reuses the 72 poses forward/backward with holds; it does not claim 158 unique renders.

Native source provenance: Actions run 34409675701 produced frames 64–71; recovery run 34411557542 produced all 64 remaining frames with `missing: []`. All 72 dimensions and completeness were independently verified locally. Dedicated desktop/portrait covers came from run 34411060224.

## Final verification

Final checks on the exact delivery HTML completed 9 September 2026 around 22:41 UTC:
- 17 motion/media/browser checks passed;
- 58 structural/browser checks passed;
- 83 static content/file checks passed;
- zero failed checks in these groups.

Automatic movement was verified without a click or relaxed autoplay flags. Actual decoded video times change with scroll. Fixed-page browser captures after entrance transitions show moving geometry, not merely a scrolling page. All nine routes, navigation, reduced motion, mobile menu, form validation and required content were checked. These checks are not aesthetic acceptance or a promise of perfect performance.

The managed browser blocks file:// navigation, so tests loaded the exact self-contained HTML with Playwright `set_content`. No device-wide Safari/Firefox or real-device 60fps certification is claimed. No font files or credentials are distributed.

## Publication and scope boundaries

**Not published to avenzodigital.nl. No DNS, hosting, mailbox or live website settings were changed.** Apply only to the existing authorized website environment after review; preserve domain/mail configuration. No recurring task was created.

The contact form retains the original mailto preparation flow, requiring the visitor to send the message in their email client. No automatic email backend or customer-email send was added.

The full YouTube reference was not accessible for playback; exact reproduction of its transitions is not claimed. This new visual direction has not yet been approved by the user.
