# Productietour — prompts en referenties (10-10-2026)

Route: Jumbo-entree → glazen schuifdeur (bord "Kijk in onze productieruimte", tekst in de pagina
zelf, niet door de AI) → ontvangst → hygiënesluis → productieruimte → terug.

Werkwijze per scène: nano_banana_2, 21:9, 4K, 2 varianten, referentiebeelden = stills uit de
Facebook-reel (`C:\AIOS\data\knapvers\vr-productie\ref_*.jpg`, gedownload met yt-dlp, één still
per seconde in `frames/`). Daarna 360°-aanvulling met `pano360.py --breedte 8192` en loopclips met
FLUX 3 Video (begin- + eindframe = 90°-uitsnedes).

Vaste kop: *A seamless very wide equirectangular-style panorama photograph, full horizontal
wrap-around, eye level 1.6 m, photorealistic, sharp, no text, no logos.*

## 1. Schuifdeur in de Jumbo (bewerking van `bron_entree.jpg`)
> Exactly the same panorama. ONE change: in the wall on the right, between the produce crates and
> the flower buckets, a wide glass sliding door with a dark aluminium frame and a blank dark sign
> panel above it; through the glass a bright, clean corridor is visible. Everything else identical.

## 2. Ontvangst — ref `ref_entree.jpg` (reel 0 s)
> Standing just inside the entrance hall of the same small Dutch family food producer as in the
> reference image. A modest, tidy reception hall: light grey floor, one accent wall in deep green
> (#266A41), a cream wall opposite, a simple light oak reception desk with a small bell, a large
> framed photograph of a family vegetable field and a framed black-and-white photo of a
> greengrocer's shop from the 1960s, a wooden crate with fresh white cabbage, carrots and red
> beetroot, a small chilled display cabinet with round clear salad cups with green labels, a coat
> rack with white coats and a box of blue hairnets, and straight ahead a white door with a round
> window leading into a bright hygiene corridor. Daylight from the glass entrance door behind the
> viewer. No people.

## 3. Hygiënesluis — ref `ref_snijden.jpg` (reel 3 s, voor wanden/licht)
> Standing in the middle of a food-industry hygiene airlock corridor of the same company. On the
> left a stainless steel hand-wash trough with three knee-operated taps, soap and paper towel
> dispensers; on the right a dispenser wall with white hairnets, blue overshoes and blue gloves,
> and a rack of clean white coats; on the floor a blue-and-white hygiene zone line and a boot-wash
> station; straight ahead a white door with a round window through which a cold production room
> with stainless steel tables and workers in white coats is visible; behind the viewer the door
> back to the reception hall. Clean, slightly humid, no people in the corridor.

## 4. Productieruimte — refs `ref_snijden.jpg`, `ref_vullen.jpg`, `ref_etiketteren.jpg`
> Standing just inside the door of the same cold fresh-cut salad production room as in the
> reference images (same white wall panels, stainless steel tables, white coats, blue hairnets,
> blue gloves, blue cutting boards, yellow and white plastic crates, blue labelling machine, bright
> cool LED light). Directly ahead a long stainless steel work table where two workers fill round
> clear salad cups by hand with scoops from large white bins full of coleslaw; on the left a worker
> cuts red cabbage on a blue cutting board next to a vegetable cutting machine and crates of white
> cabbage, carrots and red beetroot; on the right the blue labelling machine with a worker placing
> green-labelled cups into black crates, stacks of finished cups; a weighing scale on a yellow
> crate in the foreground. Tiled floor with a drain, a light cold haze near the ceiling, a wall
> clock, a door with a round window to the hygiene corridor behind the viewer. All workers seen
> from the side or from behind, faces not recognisable. 6 degrees Celsius atmosphere.

## Resultaten (Higgsfield job-id's)
- productie: A `31dad7d5-…` · B `2b67e01e-…`
- ontvangst: A `78c6769d-…` · B `7443d37c-…`
- sluis: A `ac06c42e-…` · B `7ef22f86-…`
Bestanden: `C:\AIOS\data\knapvers\vr-productie\{prod,ontv,sluis}_{a,b}.png` (6336×2688).

## Open
- Mensen: AI-figuren, onherkenbaar (gekozen); echte collega's alleen met toestemming.
- Bord boven de schuifdeur als canvas-label in `index.html` (zelfde techniek als BASIS/SEIZOEN).
- Optioneel scène 5: expeditie/koelcel met kratten klaar voor Jumbo.
