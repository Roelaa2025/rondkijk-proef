# Maakt van een deel-panorama (200° x 85°, zoals de Nano Banana-beelden) een volledige
# 360° x 180° equirect: een AI-gegenereerd 360°-beeld van dezelfde scène als achtergrond,
# met het origineel exact in het midden teruggeplakt (zachte overgang van `rand` px).
# Zo blijven de gemeten posities van deur, stippen en labels kloppen.
#
#   python blender/pano360.py origineel.jpg gegenereerd.png uit.jpg [--graden 202.5]
#
# `--graden` = de verticale dekking van het gegenereerde beeld: 16:9 = 360 x 202,5°,
# 2:1 = 180°. Het gegenereerde beeld wordt geschaald naar de pixel-per-graad van het origineel.

import sys
from PIL import Image, ImageFilter
import numpy as np

BREED_GR, HOOG_GR = 200.0, 85.0      # dekking van het origineel

def main(orig_pad, gen_pad, uit_pad, gen_hoog_gr=202.5, rand=70, kwaliteit=90):
    o = Image.open(orig_pad).convert("RGB")
    g = Image.open(gen_pad).convert("RGB")
    ppg = o.width / BREED_GR                        # pixels per graad (origineel)
    W, H = int(round(360 * ppg)), int(round(180 * ppg))
    # gegenereerd beeld: 360° breed, gen_hoog_gr hoog -> schalen en verticaal bijsnijden tot 180°
    gW = W
    gH = int(round(gen_hoog_gr * ppg))
    g = g.resize((gW, gH), Image.LANCZOS)
    y_snij = (gH - H) // 2
    g = g.crop((0, y_snij, gW, y_snij + H))
    # origineel in het midden
    x0 = (W - o.width) // 2
    y0 = (H - o.height) // 2
    a = np.asarray(o).astype(np.int32)
    b = np.asarray(g.crop((x0, y0, x0 + o.width, y0 + o.height))).astype(np.int32)
    verschil = np.abs(a - b).sum(axis=2)            # per pixel, 0..765
    # Links en rechts: geen rechte rand met zachte overgang (geeft dubbelbeeld waar de AI
    # de objecten iets verschoven heeft), maar een kronkelende naad door de zone waar
    # origineel en gegenereerd beeld het minst verschillen (dynamisch programmeren, als
    # bij seam carving). Boven en onder (plafond/vloer, egaal) volstaat een brede feather.
    ZONE = 320
    def naad(kost):                                  # kost: (h, zone) -> kolom per rij
        h, w = kost.shape
        acc = kost.astype(np.float64).copy()
        for y in range(1, h):
            vorige = acc[y - 1]
            links = np.concatenate(([np.inf], vorige[:-1]))
            rechts = np.concatenate((vorige[1:], [np.inf]))
            acc[y] += np.minimum(vorige, np.minimum(links, rechts))
        pad = np.zeros(h, dtype=int)
        pad[-1] = int(np.argmin(acc[-1]))
        for y in range(h - 2, -1, -1):
            x = pad[y + 1]
            lo, hi = max(0, x - 1), min(w, x + 2)
            pad[y] = lo + int(np.argmin(acc[y, lo:hi]))
        return pad
    naad_l = naad(verschil[:, :ZONE])                            # kolom (0..ZONE) per rij
    naad_r = o.width - ZONE + naad(verschil[:, o.width - ZONE:])
    # masker: 255 = origineel; per rij tussen de twee naden
    m = np.zeros((o.height, o.width), dtype=np.uint8)
    kol = np.arange(o.width)[None, :]
    m[(kol >= naad_l[:, None]) & (kol < naad_r[:, None])] = 255
    masker_o = Image.fromarray(m).filter(ImageFilter.GaussianBlur(6))   # smalle feather langs de naad
    # boven/onder: brede feather
    v = np.ones((o.height, 1), dtype=np.float32)
    ramp = np.linspace(0, 1, rand, dtype=np.float32)
    v[:rand, 0] = ramp; v[-rand:, 0] = ramp[::-1]
    m2 = (np.asarray(masker_o).astype(np.float32) * v).clip(0, 255).astype(np.uint8)
    masker = Image.new("L", (W, H), 0)
    masker.paste(Image.fromarray(m2), (x0, y0))
    doek = g.copy()
    doek.paste(o, (x0, y0))
    doek = Image.composite(doek, g, masker)
    doek.save(uit_pad, quality=kwaliteit, subsampling=0, optimize=True)
    print(f"{uit_pad}: {W}x{H}, origineel op ({x0},{y0}), gem. verschil midden {verschil.mean()/3:.1f}/255, "
          f"langs naad links {verschil[np.arange(o.height), naad_l].mean()/3:.1f}, rechts {verschil[np.arange(o.height), naad_r].mean()/3:.1f}")

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    gr = 202.5
    if "--graden" in sys.argv:
        gr = float(sys.argv[sys.argv.index("--graden") + 1])
    main(args[0], args[1], args[2], gr)
