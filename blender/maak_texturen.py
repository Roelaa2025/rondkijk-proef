# Maakt bakjes-texturen uit de echte KnapVers-productfoto's (Beelden/Afbeeldingen Eurosalad/Product foto's,
# 2.500-4.700 px, bakje schuin van boven op wit) en prijskaartjes voor de rails.
#   python blender/maak_texturen.py
# Uitvoer: blender/assets/prod_<naam>_top.png (bovenkant, rond met alpha), prod_<naam>_zij.png (zijband,
# 2x herhaald), kaart_<n>.png; en assets/producten.json met de lijst per categorie.
import glob, json, os, re
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageFont
import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HIER, "assets")
BRON = r"C:\Users\RoelAarten\KnapVers\KnapVers-Marketing en Sales 3.0 - Documenten\Marketing en Sales 3.0\Beelden\Afbeeldingen Eurosalad\Product foto's"
NAMEN = {  # DSC-nummer -> (categorie, naam, prijs)
    "02152": ("rauwkost", "Waldorf salade", "2.49"), "02180": ("rauwkost", "Salade van het huis", "1.99"),
    "02194": ("rauwkost", "Witte kool salade", "1.79"), "02204": ("rauwkost", "Eitje preitje", "2.19"),
    "02237": ("rauwkost", "Rode bieten salade", "1.99"), "02248": ("rauwkost", "Coleslaw", "1.79"),
    "02262": ("rauwkost", "Boerenkool salade", "2.19"), "02277": ("rauwkost", "Rode kool salade", "1.99"),
    "02288": ("rauwkost", "Waldorf salade", "2.49"), "02572": ("rauwkost", "Rode kool appel", "1.99"),
    "02580": ("rauwkost", "Rode kool", "1.79"), "02591": ("rauwkost", "Selderij salade", "2.19"),
    "02302": ("fruit", "Watermeloen", "2.29"), "02326": ("fruit", "Granaatappel", "2.99"),
    "02332": ("fruit", "Meloen", "2.29"), "02348": ("fruit", "Fruitsalade", "2.79"),
    "02355": ("fruit", "Fruitmix", "2.79"), "02369": ("fruit", "Fruitsalade groot", "3.49"),
    "02372": ("fruit", "Fruitsalade kiwi", "2.79"), "02390": ("fruit", "Ananas mix", "2.79"),
}

def bbox_niet_wit(im, drempel=28):
    # de achtergrond is lichtgrijs, niet wit: neem de randkleur als referentie en zoek wat daar duidelijk van afwijkt
    a = np.asarray(im.convert("RGB")).astype(int)
    rand = np.concatenate([a[:40].reshape(-1, 3), a[-40:].reshape(-1, 3), a[:, :40].reshape(-1, 3), a[:, -40:].reshape(-1, 3)])
    bg = np.median(rand, axis=0)
    m = np.abs(a - bg).sum(axis=2) > drempel * 3
    m[:, :a.shape[1] // 50] = False; m[:, -a.shape[1] // 50:] = False      # randen negeren (schaduw/vignet)
    # ruis wegfilteren: alleen rijen/kolommen met voldoende afwijkende pixels
    rijen = np.where(m.sum(axis=1) > a.shape[1] * 0.02)[0]
    kols = np.where(m.sum(axis=0) > a.shape[0] * 0.02)[0]
    return kols.min(), rijen.min(), kols.max(), rijen.max()

uit = []
for pad in sorted(glob.glob(os.path.join(BRON, "*", "DSC*.*"))):
    nr = re.search(r"DSC(\d{5})", pad).group(1)
    if nr not in NAMEN:
        continue
    cat, naam, prijs = NAMEN[nr]
    im = ImageOps.exif_transpose(Image.open(pad)).convert("RGB")
    x0, y0, x1, y1 = bbox_niet_wit(im)
    w, h = x1 - x0, y1 - y0
    # bovenkant: ellips in het bovenste deel van het bakje (schuine foto: ~55 % van de hoogte), tot een cirkel gerekt
    top = im.crop((x0 + int(w * 0.06), y0, x1 - int(w * 0.06), y0 + int(h * 0.60))).resize((768, 768), Image.LANCZOS)
    masker = Image.new("L", (768, 768), 0); ImageDraw.Draw(masker).ellipse((8, 8, 760, 760), fill=255)
    masker = masker.filter(ImageFilter.GaussianBlur(3)); top.putalpha(masker)
    # zijband: onder de rand, door de wand heen zichtbare salade
    band = im.crop((x0 + int(w * 0.22), y0 + int(h * 0.73), x1 - int(w * 0.24), y0 + int(h * 0.91))).resize((640, 256), Image.LANCZOS)
    zij = Image.new("RGB", (1280, 256)); zij.paste(band, (0, 0)); zij.paste(band.transpose(Image.FLIP_LEFT_RIGHT), (640, 0))
    sleutel = f"prod_{nr}"
    top.save(os.path.join(ASSETS, sleutel + "_top.png")); zij.save(os.path.join(ASSETS, sleutel + "_zij.png"))
    uit.append({"sleutel": sleutel, "cat": cat, "naam": naam, "prijs": prijs})
    print(sleutel, cat, naam, im.size, (w, h))

# prijskaartjes: wit kaartje met naam, gewicht en prijs (zoals de papieren tags op de rail)
try:
    f_naam = ImageFont.truetype("arial.ttf", 34); f_prijs = ImageFont.truetype("arialbd.ttf", 72); f_klein = ImageFont.truetype("arial.ttf", 26)
except Exception:
    f_naam = f_prijs = f_klein = ImageFont.load_default()
for i, p in enumerate(uit):
    k = Image.new("RGB", (560, 256), (255, 255, 255)); d = ImageDraw.Draw(k)
    d.text((18, 14), p["naam"][:22], fill=(20, 20, 20), font=f_naam)
    d.text((18, 58), "200 g · KnapVers", fill=(90, 90, 90), font=f_klein)
    d.text((18, 110), p["prijs"], fill=(20, 20, 20), font=f_prijs)
    d.text((300, 150), "per stuk", fill=(90, 90, 90), font=f_klein)
    d.rectangle((18, 215, 540, 240), fill=(20, 20, 20))     # 'barcode'-balk
    for x in range(24, 536, 7):
        if (x // 7) % 3: d.line((x, 215, x, 240), fill=(255, 255, 255), width=2)
    k.save(os.path.join(ASSETS, f"kaart_{i:02d}.png"))
json.dump(uit, open(os.path.join(ASSETS, "producten.json"), "w"), indent=1)
print(len(uit), "producten,", len(uit), "kaartjes")
