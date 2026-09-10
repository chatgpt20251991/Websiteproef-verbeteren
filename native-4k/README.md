# Avenzo Digital: native 4K website delivery

## Completed delivery

The complete website package was built successfully in run **34536982011** from commit `e72f173f3a7cd5f8b50cdaaa147376ce0b9f6e57`.

Artifact: **Avenzo-Digital-Native-4K**, ID **10176077387**, 14,497,974 bytes.
Archive SHA-256: `de209c676b8e1f0de70e99bdb5a5e2adb180e48fb4f83710e173b8aaa3476f9e`.
It was transferred to the owner as `Avenzo-Digital-Native-4K.zip` in the normal chat.
The repository artifact expires on 24 September 2026; the render source code remains in this folder.

**This is not a live deployment. The existing custom domain, hosting, DNS and mail configuration were not changed.**

## What the package contains

- All nine public pages with their original main copy and layout, and the previously approved SVG wordmark and footer.
- Nine newly authored 3D images, rendered directly at 3840 pixels wide with Blender 4.2.3 / Cycles. Desktop hero and software close-up are 3840 x 2160, service images are 3840 x 2402, and the separately framed mobile hero is 3840 x 4937.
- 63 responsive WebP files. Smaller variants were downsampled from the native final images, never enlarged from the earlier website images.
- The production directory `website/` and a separate direct-open preview starting at `BEKIJK-WEBSITE.html`. Extract the entire ZIP before opening it. This preview does not require Python or a web server.
- Source scripts, render provenance, image hashes and browser reports in `source/` and `reports/`.

The new artwork consists of original procedural geometry, vector typography, analytic materials and lighting. It uses zero input raster textures. These are **new 3D interpretations of the existing visual direction**, not pixel-identical restorations of the earlier photographs.

## Verification actually performed

All nine native rendering jobs in run **34535503130** completed successfully. The corrected render source SHA-256 is `f85cb63b6cf383274b3c4de6c284a363d488396798296a703fcf27d85ee15559`. `prepare_build.py` applies the tested Blender 4.2 material socket correction before assembly.

The final package workflow passed:

- 54 Chromium page/viewport checks: all nine pages at six viewport and pixel-density configurations, including 3840 x 2160 and 1920 x 1080 at device-pixel-ratio 2.
- 18 file-URL preview checks: all nine pages on mobile and desktop.
- Assertions for local asset availability, horizontal overflow, image decoding and actual selected image pixel coverage, approved logo instances, main copy preservation, internal links/anchors, mobile menu, accordion behavior and contact-service preselection.

The 4K hero crop uses a 68% vertical focal point above 2400 CSS pixels, based on measured 3D device bounds. This changes the image crop, not the original page layout.

Screenshots were produced, but **a visual inspection of those screenshots was not completed because the chat's image/file viewing environment timed out**. Automated checks and geometry inspection are not a claim of complete visual design approval, universal bug freedom or an accessibility audit.

## Preserved limitations

Font binaries are not included. The existing Body font is referenced on the original Avenzo host, with the existing Arial fallback. Preserve that font on the hosting when publishing; cross-origin font availability in a local preview is not guaranteed.

The existing contact form prepares a mailto draft. It is not an independently sending server-backed form. No test message was sent and no email delivery was claimed.

Publishing still requires authorized access to the existing site's actual publication environment. Saving this code or running these validation workflows does not update avenzodigital.nl.
