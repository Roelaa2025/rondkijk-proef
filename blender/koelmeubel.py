# Koelmeubel met echte KnapVers-bakjes, gerenderd als stereo-360 (boven-onder) met transparante
# achtergrond. De laag komt in index.html óver de AI-panorama te liggen (component stereo-laag).
#
#   blender -b -P blender/koelmeubel.py -- --preview        snelle controle (1024x1024, 16 samples)
#   blender -b -P blender/koelmeubel.py                     definitief (4096x4096, 96 samples)
#
# Assenstelsel: Blender Z omhoog, camera in de oorsprong op ooghoogte, kijkt langs +Y.
# A-Frame kijkt langs -Z; de laag wordt daar zo gemapt dat Blender +Y = A-Frame -Z.
# Maten uit memory/project_jumbo_tender_rauwkosten.md (sessie 12): deuropening 0,87 x 1,81 m
# op 1,48 m, middenhoogte -0,20 m t.o.v. de ogen.

import bpy, bmesh, math, os, sys, random

HIER = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HIER, "assets")
UIT = os.path.join(HIER, "..")
PREVIEW = "--preview" in sys.argv
DETAIL = "--detail" in sys.argv     # gewone camera vlak voor het middelste schap: etiketten/salade beoordelen

random.seed(7)

# ---------- maten (m) ----------
AFSTAND = 1.48          # ogen -> voorkant meubel
MIDDEN_Y = -0.20        # middenhoogte opening t.o.v. ogen
OPEN_B, OPEN_H = 0.87, 1.81
KAST_B = 1.16           # buitenmaat kolom (geel), zoals in de foto
KAST_D = 0.62
KAST_H_ONDER = MIDDEN_Y - OPEN_H / 2 - 0.22   # gele sokkel
KAST_H_BOVEN = MIDDEN_Y + OPEN_H / 2 + 0.55   # kop met donker paneel
WAND = (KAST_B - OPEN_B) / 2
BAK_D = 0.115           # Ø bakje (Ilpra: 4-voudig formaatdeel Ø115)
BAK_H = 0.060

# ---------- helpers ----------
def maak_mat(naam, kleur=(0.8, 0.8, 0.8, 1), ruw=0.5, metaal=0.0, emissie=0.0, alpha=1.0, transmissie=0.0, ior=1.45):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = kleur
    b.inputs["Roughness"].default_value = ruw
    b.inputs["Metallic"].default_value = metaal
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Transmission Weight"].default_value = transmissie
    b.inputs["IOR"].default_value = ior
    if emissie:
        b.inputs["Emission Color"].default_value = kleur
        b.inputs["Emission Strength"].default_value = emissie
    if alpha < 1 or transmissie > 0:
        m.blend_method = "BLEND"
    return m

def mat_afbeelding(naam, pad, ruw=0.55, alpha_uit_beeld=False):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = ruw
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(pad)
    tex.extension = "CLIP"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    if alpha_uit_beeld:
        nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
        m.blend_method = "BLEND"
    return m

def doos(naam, pos, afm, mat, ouder=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.active_object
    o.name = naam
    o.scale = afm
    o.data.materials.append(mat)
    if ouder:
        o.parent = ouder
    return o

def cilinder(naam, pos, r, h, mat, r_boven=None, segs=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segs, radius=r, depth=h, location=pos)
    o = bpy.context.active_object
    o.name = naam
    o.data.materials.append(mat)
    if r_boven and r_boven != r:
        # bovenste ring schalen: bakje loopt licht taps toe
        bm = bmesh.new(); bm.from_mesh(o.data)
        for v in bm.verts:
            if v.co.z > 0:
                v.co.x *= r_boven / r; v.co.y *= r_boven / r
        bm.to_mesh(o.data); bm.free()
    bpy.ops.object.shade_smooth()
    return o

def uv_van_boven(o, r):
    """Projecteer de bovenkant (foto van de salade) van boven: UV = (x,y) binnen straal r."""
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (0.5 + v.x / (2 * r), 0.5 + v.y / (2 * r))

def label_vlak(naam, pad, breedte, pos, rot, mat=None):
    img = bpy.data.images.load(pad)
    hoogte = breedte * img.size[1] / img.size[0]
    bpy.ops.mesh.primitive_plane_add(size=1, location=pos, rotation=rot)
    o = bpy.context.active_object
    o.name = naam
    o.scale = (breedte, hoogte, 1)
    m = mat or mat_afbeelding(naam + "_mat", pad, ruw=0.45)
    o.data.materials.append(m)
    return o

# ---------- schoon beginnen ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------- materialen ----------
M_GEEL = maak_mat("geel", (0.93, 0.66, 0.05, 1), ruw=0.35)
M_DONKER = maak_mat("donker", (0.06, 0.06, 0.07, 1), ruw=0.6)
M_BINNEN = maak_mat("binnenwand", (0.12, 0.12, 0.13, 1), ruw=0.7)
M_SCHAP = maak_mat("schap", (0.62, 0.63, 0.65, 1), ruw=0.35, metaal=0.8)
M_LED = maak_mat("led", (1.0, 0.97, 0.9, 1), emissie=18.0)
# helder PP: geen transmissie (de cilinder is massief en zou als glazen puck breken), wel doorzicht via alpha
M_PP = maak_mat("pp_helder", (0.97, 0.98, 1.0, 1), ruw=0.18, alpha=0.07, ior=1.49)
M_PP.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.25
M_PRIJSRAIL = maak_mat("prijsrail", (0.85, 0.85, 0.85, 1), ruw=0.5)
M_STRIP = {
    "basis": maak_mat("strip_basis", (0.55, 0.53, 0.50, 1), ruw=0.6),
    "seizoen": maak_mat("strip_seizoen", (0.35, 0.55, 0.25, 1), ruw=0.6),
    "innovatie": maak_mat("strip_innovatie", (0.14, 0.42, 0.25, 1), ruw=0.6),   # KnapVers DarkGreen
}

# ---------- de kast ----------
y0 = AFSTAND                      # voorkant
yc = AFSTAND + KAST_D / 2         # midden kastdiepte
z_onder = KAST_H_ONDER
z_boven = KAST_H_BOVEN
z_op_onder = MIDDEN_Y - OPEN_H / 2
z_op_boven = MIDDEN_Y + OPEN_H / 2

kast = bpy.data.objects.new("koelmeubel", None); sc.collection.objects.link(kast)
# zijwangen, sokkel, kop (geel)
doos("wang_links", (-KAST_B/2 + WAND/2, yc, (z_onder+z_boven)/2), (WAND, KAST_D, z_boven-z_onder), M_GEEL, kast)
doos("wang_rechts", (KAST_B/2 - WAND/2, yc, (z_onder+z_boven)/2), (WAND, KAST_D, z_boven-z_onder), M_GEEL, kast)
doos("sokkel", (0, yc, (z_onder+z_op_onder)/2), (KAST_B, KAST_D, z_op_onder-z_onder), M_GEEL, kast)
doos("kop", (0, yc, (z_op_boven+z_boven)/2), (KAST_B, KAST_D, z_boven-z_op_boven), M_GEEL, kast)
doos("koppaneel", (0, y0+0.01, z_op_boven + (z_boven-z_op_boven)*0.55), (KAST_B*0.86, 0.02, (z_boven-z_op_boven)*0.6), M_DONKER, kast)
doos("sokkelrooster", (0, y0+0.01, z_onder + (z_op_onder-z_onder)*0.45), (KAST_B*0.86, 0.02, (z_op_onder-z_onder)*0.55), M_DONKER, kast)
# binnenwanden
doos("achterwand", (0, y0+KAST_D-0.02, MIDDEN_Y), (OPEN_B, 0.02, OPEN_H), M_BINNEN, kast)
doos("binnen_links", (-OPEN_B/2+0.01, yc, MIDDEN_Y), (0.02, KAST_D, OPEN_H), M_BINNEN, kast)
doos("binnen_rechts", (OPEN_B/2-0.01, yc, MIDDEN_Y), (0.02, KAST_D, OPEN_H), M_BINNEN, kast)
doos("binnen_boven", (0, yc, z_op_boven-0.01), (OPEN_B, KAST_D, 0.02), M_BINNEN, kast)
doos("binnen_onder", (0, yc, z_op_onder+0.01), (OPEN_B, KAST_D, 0.02), M_BINNEN, kast)
# led-strip bovenin
doos("led_boven", (0, y0+0.10, z_op_boven-0.03), (OPEN_B*0.9, 0.03, 0.012), M_LED, kast)

# ---------- schappen + bakjes ----------
# vijf schappen; hoogte per schap 0,33 m; bakjes 60 mm hoog laten ruim lucht
N_SCHAP = 5
schap_h = (OPEN_H - 0.10) / N_SCHAP
schap_d = KAST_D - 0.16
lagen = ["basis", "basis", "seizoen", "seizoen", "innovatie"]   # van onder naar boven
salades = {
    "basis": ["salade_salade-van-het-huis", "salade_coleslaw"],
    "seizoen": ["salade_rode-bieten-salade", "salade_waldorf-salade", "salade_rode-kool-salade"],
    "innovatie": ["salade_eitje-preitje", "salade_broccoli-salade"],
}
etiket = {"basis": "basis_heerlijk-bijgerecht", "seizoen": "seizoen_herfst-special", "innovatie": "innovatie_100-gram-groente"}
import json
kleuren = json.load(open(os.path.join(ASSETS, "salade_kleuren.json")))
# bovenkant: uitgesneden foto van de salade (rond, met alpha); zijkant: gemiddelde kleur van de salade
mat_sal_top = {n: mat_afbeelding(n + "_top", os.path.join(ASSETS, n + "_top.png"), ruw=0.75, alpha_uit_beeld=True) for lijst in salades.values() for n in lijst}
mat_sal_zij = {n: mat_afbeelding(n + "_zij", os.path.join(ASSETS, n + "_zij.png"), ruw=0.85) for lijst in salades.values() for n in lijst}
for m in mat_sal_zij.values():
    m.node_tree.nodes["Image Texture"].extension = "REPEAT"

def uv_zijkant(o, h):
    """Zijvlakken: u = hoek rondom, v = hoogte; kapvlakken: van boven."""
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        zij = abs(poly.normal.z) < 0.5
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            if zij:
                u = (math.atan2(v.y, v.x) / (2 * math.pi)) % 1.0
                uv[li].uv = (u, (v.z + h / 2) / h)
            else:
                uv[li].uv = (0.5 + v.x / h, 0.5 + v.y / h)
    # naad rechttrekken: loops van één vlak die over 0/1 springen
    for poly in me.polygons:
        us = [uv[li].uv[0] for li in poly.loop_indices]
        if max(us) - min(us) > 0.5:
            for li in poly.loop_indices:
                if uv[li].uv[0] < 0.5:
                    uv[li].uv = (uv[li].uv[0] + 1.0, uv[li].uv[1])
mat_zij = {l: mat_afbeelding("zij_" + l, os.path.join(ASSETS, etiket[l] + "_zijkant.png"), ruw=0.45) for l in etiket}
mat_dek = {l: mat_afbeelding("dek_" + l, os.path.join(ASSETS, etiket[l] + "_deksel.png"), ruw=0.45) for l in etiket}

def bakje(naam, pos, laag, sal, hoek):
    x, y, z = pos
    r_top, r_bodem = BAK_D/2, BAK_D/2*0.90
    # salade: ruwe cilinder in de saladekleur, met bovenop een schijf met de uitgesneden foto
    s = cilinder(naam+"_salade", (x, y, z + BAK_H*0.47), r_bodem*0.96, BAK_H*0.86, mat_sal_zij[sal], r_boven=r_top*0.95, segs=40)
    bm = bmesh.new(); bm.from_mesh(s.data)
    for v in bm.verts:
        if v.co.z > 0:
            v.co.z += random.uniform(-0.004, 0.006)
    bm.to_mesh(s.data); bm.free()
    uv_zijkant(s, BAK_H*0.86)
    bpy.ops.mesh.primitive_circle_add(vertices=40, radius=r_top*0.95, fill_type="NGON", location=(x, y, z + BAK_H*0.92))
    st = bpy.context.active_object; st.name = naam+"_saladetop"
    st.data.materials.append(mat_sal_top[sal])
    uv_van_boven(st, r_top*0.95)
    # het bakje zelf (helder PP) + deksel met rand
    b = cilinder(naam+"_bak", (x, y, z + BAK_H/2), r_bodem, BAK_H, M_PP, r_boven=r_top)
    d = cilinder(naam+"_deksel", (x, y, z + BAK_H + 0.003), r_top*1.02, 0.006, M_PP)
    for o in (s, st, b, d):
        o.rotation_euler[2] = hoek
        o.parent = kast
    # zijetiket: gebogen om de voorkant (naar de kijker, -Y)
    img = mat_zij[laag].node_tree.nodes["Image Texture"].image
    breedte = 0.046
    hoogte = breedte * img.size[1] / img.size[0]
    bpy.ops.mesh.primitive_plane_add(size=1)
    e = bpy.context.active_object; e.name = naam+"_etiket"
    e.scale = (breedte, hoogte, 1)
    e.data.materials.append(mat_zij[laag])
    # buigen: subdivide en op de cilinder leggen
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=10); bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.transform_apply(scale=True)
    me = e.data
    for v in me.vertices:
        a = v.co.x / (r_top*0.98)             # boogpositie in radialen
        rr = r_bodem + (r_top-r_bodem) * (v.co.y + hoogte/2) / BAK_H
        v.co = (rr*1.004*math.sin(a), -rr*1.004*math.cos(a), v.co.y)
    e.location = (x, y, z + BAK_H*0.5)
    e.rotation_euler[2] = hoek
    e.parent = kast
    # dekseletiket: plat op de deksel, koepel naar de kijker
    label_vlak(naam+"_dekseletiket", os.path.join(ASSETS, etiket[laag]+"_deksel.png"), 0.048,
               (x, y, z + BAK_H + 0.0065), (0, 0, hoek), mat_dek[laag])
    bpy.context.active_object.parent = kast

for i in range(N_SCHAP):
    laag = lagen[i]
    z_s = z_op_onder + 0.05 + i * schap_h
    y_s = y0 + 0.06 + schap_d/2
    sch = doos(f"schap_{i}", (0, y_s, z_s), (OPEN_B-0.03, schap_d, 0.012), M_SCHAP, kast)
    # prijsrail / kleurstrip vooraan
    doos(f"rail_{i}", (0, y0+0.065, z_s-0.012), (OPEN_B-0.03, 0.012, 0.035), M_PRIJSRAIL, kast)
    doos(f"strip_{i}", (0, y0+0.058, z_s-0.012), (OPEN_B-0.05, 0.004, 0.028), M_STRIP[laag], kast)
    # led onder elk schap (behalve onderste)
    if i > 0:
        doos(f"led_{i}", (0, y0+0.09, z_s-0.010), (OPEN_B*0.9, 0.02, 0.006), M_LED, kast)
    # bakjes: rijen naar achteren, kolommen opzij; bovenste schap = premium met minder bakjes
    n_kol = 5 if laag == "innovatie" else 7
    n_rij = 2 if laag == "innovatie" else 3
    stap_x = (OPEN_B - 0.06) / n_kol
    stap_y = BAK_D + 0.012
    keuze = salades[laag]
    for r in range(n_rij):
        for k in range(n_kol):
            if laag == "innovatie" and (k in (0, 4)) and r == 1:
                continue   # wat lucht op het premium-schap
            sal = keuze[k % len(keuze)]
            x = -OPEN_B/2 + 0.03 + stap_x*(k+0.5) + random.uniform(-0.004, 0.004)
            y = y0 + 0.11 + BAK_D/2 + r*stap_y + random.uniform(-0.003, 0.003)
            bakje(f"bak_{i}_{r}_{k}", (x, y, z_s + 0.006), laag, sal, random.uniform(-0.12, 0.12))

# ---------- licht en wereld ----------
w = sc.world = bpy.data.worlds.new("wereld")
w.use_nodes = True
wn = w.node_tree
bg = wn.nodes["Background"]
env = wn.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(UIT, "pano360_2.jpg"))   # echte 360x180 (pano360.py)
wn.links.new(env.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.45
# alleen voor licht/reflecties, niet in beeld (film transparant); beeldmidden = +Y, net als de camera

bpy.ops.object.light_add(type="AREA", location=(0, AFSTAND-0.4, 1.4))
l = bpy.context.active_object; l.data.energy = 160; l.data.size = 1.6; l.data.color = (1.0, 0.95, 0.88)
l.rotation_euler = (math.radians(35), 0, 0)

# ---------- camera: stereo equirect ----------
bpy.ops.object.camera_add(location=(0, 0, 0), rotation=(math.radians(90), 0, 0))   # kijkt langs +Y
cam = bpy.context.active_object
cam.data.type = "PANO"
try:
    cam.data.panorama_type = "EQUIRECTANGULAR"          # Blender 4.x
except Exception:
    cam.data.cycles.panorama_type = "EQUIRECTANGULAR"   # oudere API
cam.data.stereo.convergence_mode = "OFFAXIS"
cam.data.stereo.interocular_distance = 0.064
cam.data.stereo.use_spherical_stereo = True
cam.data.stereo.use_pole_merge = True
cam.data.stereo.pole_merge_angle_from = math.radians(60)
cam.data.stereo.pole_merge_angle_to = math.radians(75)
sc.camera = cam

# ---------- render ----------
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 16 if PREVIEW else 96
sc.cycles.use_denoising = True
sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 6
sc.cycles.transparent_max_bounces = 12
sc.render.film_transparent = True
sc.render.use_multiview = True
sc.render.views_format = "STEREO_3D"
sc.render.image_settings.views_format = "STEREO_3D"
sc.render.image_settings.stereo_3d_format.display_mode = "TOPBOTTOM"
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
sc.render.image_settings.compression = 60
res = 1024 if PREVIEW else 4096
sc.render.resolution_x = res
sc.render.resolution_y = res // 2      # per oog 2:1; boven-onder maakt het totaal vierkant
sc.render.resolution_percentage = 100
sc.render.filepath = os.path.join(UIT, "koelmeubel_preview.png" if PREVIEW else "koelmeubel_stereo.png")
if DETAIL:
    cam.data.type = "PERSP"; cam.data.lens = 35
    cam.location = (0.05, AFSTAND - 0.55, MIDDEN_Y + 0.15)
    cam.rotation_euler = (math.radians(80), 0, 0)
    sc.render.use_multiview = False
    sc.render.film_transparent = False
    sc.render.resolution_x, sc.render.resolution_y = 1400, 900
    sc.cycles.samples = 48
    sc.render.filepath = os.path.join(UIT, "_detail.png")

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HIER, "koelmeubel.blend"))
bpy.ops.render.render(write_still=True)
print("KLAAR:", sc.render.filepath)
