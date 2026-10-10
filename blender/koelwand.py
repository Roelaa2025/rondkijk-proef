# Koelwand (open multideck, zoals in een echte supermarkt) met het KnapVers-module in het midden.
# Referentie: Roels foto's van 10-10 — vol gezet, prijsrails met kaartjes, lichtstrip per plank,
# licht hellende planken, glazen zijschotten, zwarte binnenkant.
#
#   blender -b -P blender/koelwand.py -- --still      beoordelingsrender (perspectief, 1600x1000)
#   blender -b -P blender/koelwand.py -- --preview    stereo-360 klein (1024)
#   blender -b -P blender/koelwand.py                 stereo-360 definitief (4096x4096, transparant)
#
# Assen: Blender Z omhoog, camera in de oorsprong op ooghoogte, kijkt langs +Y (= A-Frame -Z).

import bpy, bmesh, math, os, sys, random, json

HIER = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HIER, "assets")
UIT = os.path.join(HIER, "..")
STILL = "--still" in sys.argv
PREVIEW = "--preview" in sys.argv
random.seed(11)

# ---------- maten (m); het middenmodule valt samen met de foto (sessie 13) ----------
AFSTAND = 1.20              # ogen -> voorkant wand
MIDDEN_Y = -0.16            # middenhoogte van de opening van het middenmodule t.o.v. de ogen
OPEN_H = 1.295
MOD_B = 1.215               # binnenmaat per module
STIJL = 0.06                # gele stijl tussen modules
N_MOD = 3                   # links fruit · midden KnapVers · rechts overig
WAND_B = N_MOD * MOD_B + (N_MOD + 1) * STIJL
DIEP = 0.62
Z_OP_ONDER = MIDDEN_Y - OPEN_H / 2
Z_OP_BOVEN = MIDDEN_Y + OPEN_H / 2
Z_ONDER = Z_OP_ONDER - 0.34
Z_BOVEN = 0.95
N_SCHAP = 5
SCHAP_H = (OPEN_H - 0.06) / N_SCHAP
HELLING = math.radians(6)   # planken hellen licht naar voren
BAK_D, BAK_H = 0.115, 0.060

# ---------- helpers ----------
def mat(naam, kleur=(0.8, 0.8, 0.8, 1), ruw=0.5, metaal=0.0, emissie=0.0, alpha=1.0, spec=0.5):
    m = bpy.data.materials.new(naam); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = kleur
    b.inputs["Roughness"].default_value = ruw
    b.inputs["Metallic"].default_value = metaal
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Specular IOR Level"].default_value = spec
    if emissie:
        b.inputs["Emission Color"].default_value = kleur
        b.inputs["Emission Strength"].default_value = emissie
    return m

def mat_img(naam, pad, ruw=0.55, alpha=False, repeat=False):
    m = bpy.data.materials.new(naam); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = ruw
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(pad)
    t.extension = "REPEAT" if repeat else "CLIP"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if alpha:
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    return m

def doos(naam, pos, afm, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos, rotation=rot)
    o = bpy.context.active_object; o.name = naam; o.scale = afm; o.data.materials.append(m); return o

def cil(naam, pos, r, h, m, r_boven=None, segs=36):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segs, radius=r, depth=h, location=pos)
    o = bpy.context.active_object; o.name = naam; o.data.materials.append(m)
    if r_boven and r_boven != r:
        bm = bmesh.new(); bm.from_mesh(o.data)
        for v in bm.verts:
            if v.co.z > 0: v.co.x *= r_boven / r; v.co.y *= r_boven / r
        bm.to_mesh(o.data); bm.free()
    bpy.ops.object.shade_smooth(); return o

def uv_boven(o, r):
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for p in me.polygons:
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (0.5 + v.x / (2 * r), 0.5 + v.y / (2 * r))

def uv_zij(o, h):
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for p in me.polygons:
        zij = abs(p.normal.z) < 0.5
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = ((math.atan2(v.y, v.x) / (2 * math.pi)) % 1.0, (v.z + h / 2) / h) if zij else (0.5 + v.x / h, 0.5 + v.y / h)
    for p in me.polygons:
        us = [uv[li].uv[0] for li in p.loop_indices]
        if max(us) - min(us) > 0.5:
            for li in p.loop_indices:
                if uv[li].uv[0] < 0.5: uv[li].uv = (uv[li].uv[0] + 1.0, uv[li].uv[1])

def etiket_gebogen(naam, m, img, breedte, pos, r_top, r_bodem, hoek):
    hoogte = breedte * img.size[1] / img.size[0]
    bpy.ops.mesh.primitive_plane_add(size=1)
    e = bpy.context.active_object; e.name = naam; e.scale = (breedte, hoogte, 1); e.data.materials.append(m)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=10); bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.transform_apply(scale=True)
    for v in e.data.vertices:
        a = v.co.x / (r_top * 0.98)
        rr = r_bodem + (r_top - r_bodem) * (v.co.y + hoogte / 2) / BAK_H
        v.co = (rr * 1.004 * math.sin(a), -rr * 1.004 * math.cos(a), v.co.y)
    e.location = pos; e.rotation_euler[2] = hoek; return e

# ---------- scène ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

M_GEEL = mat("geel", (0.93, 0.66, 0.05, 1), ruw=0.35)
M_ZWART = mat("zwart", (0.02, 0.02, 0.022, 1), ruw=0.55)
M_BINNEN = mat("binnen", (0.035, 0.035, 0.04, 1), ruw=0.65)        # zwarte binnenkant, zoals in de foto
M_SCHAP = mat("schap", (0.55, 0.56, 0.58, 1), ruw=0.4, metaal=0.7)
M_ALU = mat("alu", (0.75, 0.76, 0.78, 1), ruw=0.3, metaal=0.9)
M_GLAS = mat("glas", (0.9, 0.95, 1.0, 1), ruw=0.05, alpha=0.12)
M_LED = mat("led", (1.0, 0.98, 0.93, 1), emissie=25.0)
M_RAIL = mat("rail", (0.93, 0.93, 0.93, 1), ruw=0.5)
M_KAART = mat("kaart", (1.0, 1.0, 1.0, 1), ruw=0.6)
M_KAART_ROOD = mat("kaart_rood", (0.85, 0.08, 0.08, 1), ruw=0.6)
M_PP = mat("pp", (0.97, 0.98, 1.0, 1), ruw=0.18, alpha=0.07, spec=0.25)
M_PET = mat("pet", (0.98, 0.99, 1.0, 1), ruw=0.08, alpha=0.1, spec=0.4)
M_STRIP = {"basis": mat("s_basis", (0.52, 0.5, 0.47, 1)), "seizoen": mat("s_seizoen", (0.35, 0.55, 0.25, 1)),
           "innovatie": mat("s_innov", (0.14, 0.42, 0.25, 1))}

salades = {"basis": ["salade_salade-van-het-huis", "salade_coleslaw"],
           "seizoen": ["salade_rode-bieten-salade", "salade_waldorf-salade", "salade_rode-kool-salade"],
           "innovatie": ["salade_eitje-preitje", "salade_broccoli-salade"]}
alle_sal = [n for l in salades.values() for n in l]
etiket = {"basis": "basis_heerlijk-bijgerecht", "seizoen": "seizoen_herfst-special", "innovatie": "innovatie_100-gram-groente"}
m_top = {n: mat_img(n + "_t", os.path.join(ASSETS, n + "_top.png"), 0.75, alpha=True) for n in alle_sal}
m_zij = {n: mat_img(n + "_z", os.path.join(ASSETS, n + "_zij.png"), 0.85, repeat=True) for n in alle_sal}
m_et = {l: mat_img("et_" + l, os.path.join(ASSETS, etiket[l] + "_zijkant.png"), 0.45) for l in etiket}
m_dek = {l: mat_img("dek_" + l, os.path.join(ASSETS, etiket[l] + "_deksel.png"), 0.45) for l in etiket}
img_et = {l: m_et[l].node_tree.nodes["Image Texture"].image for l in etiket}
img_dek = {l: m_dek[l].node_tree.nodes["Image Texture"].image for l in etiket}

wand = bpy.data.objects.new("koelwand", None); sc.collection.objects.link(wand)
def ouder(o): o.parent = wand; return o

y0 = AFSTAND; yc = y0 + DIEP / 2
# romp
ouder(doos("romp_achter", (0, y0 + DIEP, (Z_ONDER + Z_BOVEN) / 2), (WAND_B, 0.02, Z_BOVEN - Z_ONDER), M_ZWART))
ouder(doos("sokkel", (0, yc, (Z_ONDER + Z_OP_ONDER) / 2), (WAND_B, DIEP, Z_OP_ONDER - Z_ONDER), M_ZWART))
ouder(doos("sokkelrooster", (0, y0 + 0.005, Z_ONDER + (Z_OP_ONDER - Z_ONDER) * 0.5), (WAND_B * 0.98, 0.01, (Z_OP_ONDER - Z_ONDER) * 0.7), M_BINNEN))
ouder(doos("kop", (0, yc, (Z_OP_BOVEN + Z_BOVEN) / 2), (WAND_B, DIEP, Z_BOVEN - Z_OP_BOVEN), M_ZWART))
ouder(doos("kopstrook_geel", (0, y0 + 0.003, Z_OP_BOVEN + 0.03), (WAND_B, 0.006, 0.06), M_GEEL))
# modules
x_links = -WAND_B / 2
for i in range(N_MOD + 1):
    x = x_links + STIJL / 2 + i * (MOD_B + STIJL)
    ouder(doos(f"stijl_{i}", (x, yc, (Z_ONDER + Z_BOVEN) / 2), (STIJL, DIEP, Z_BOVEN - Z_ONDER), M_GEEL))
# glazen zijschotten aan beide einden
for s in (-1, 1):
    x = s * (WAND_B / 2 + 0.004)
    ouder(doos(f"zijglas_{s}", (x, y0 + 0.2, MIDDEN_Y), (0.008, 0.4, OPEN_H), M_GLAS))
    ouder(doos(f"zijglas_rand_{s}", (x, y0 + 0.02, MIDDEN_Y), (0.012, 0.03, OPEN_H), M_ALU))
# binnenwanden per module + led boven
for i in range(N_MOD):
    xm = x_links + STIJL + MOD_B / 2 + i * (MOD_B + STIJL)
    ouder(doos(f"binnen_{i}", (xm, y0 + DIEP - 0.03, MIDDEN_Y), (MOD_B, 0.02, OPEN_H), M_BINNEN))
    ouder(doos(f"led_top_{i}", (xm, y0 + 0.08, Z_OP_BOVEN - 0.02), (MOD_B * 0.92, 0.03, 0.012), M_LED))

def bakje(naam, pos, laag, sal, hoek, materiaal=M_PP):
    x, y, z = pos
    r_top, r_bod = BAK_D / 2, BAK_D / 2 * 0.90
    s = cil(naam + "_s", (x, y, z + BAK_H * 0.47), r_bod * 0.96, BAK_H * 0.86, m_zij[sal], r_boven=r_top * 0.95)
    bm = bmesh.new(); bm.from_mesh(s.data)
    for v in bm.verts:
        if v.co.z > 0: v.co.z += random.uniform(-0.004, 0.006)
    bm.to_mesh(s.data); bm.free(); uv_zij(s, BAK_H * 0.86)
    bpy.ops.mesh.primitive_circle_add(vertices=36, radius=r_top * 0.95, fill_type="NGON", location=(x, y, z + BAK_H * 0.92))
    st = bpy.context.active_object; st.name = naam + "_st"; st.data.materials.append(m_top[sal]); uv_boven(st, r_top * 0.95)
    b = cil(naam + "_b", (x, y, z + BAK_H / 2), r_bod, BAK_H, materiaal, r_boven=r_top)
    d = cil(naam + "_d", (x, y, z + BAK_H + 0.003), r_top * 1.02, 0.006, materiaal)
    e = etiket_gebogen(naam + "_e", m_et[laag], img_et[laag], 0.046, (x, y, z + BAK_H * 0.5), r_top, r_bod, hoek)
    img = img_dek[laag]; bw = 0.048
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z + BAK_H + 0.0065), rotation=(0, 0, hoek))
    dk = bpy.context.active_object; dk.name = naam + "_dk"; dk.scale = (bw, bw * img.size[1] / img.size[0], 1); dk.data.materials.append(m_dek[laag])
    for o in (s, st, b, d, e, dk):
        o.rotation_euler[2] = hoek if o not in (e, dk) else o.rotation_euler[2]; ouder(o)

lagen = ["basis", "basis", "seizoen", "seizoen", "innovatie"]
for i in range(N_SCHAP):
    laag = lagen[i]
    z_s = Z_OP_ONDER + 0.04 + i * SCHAP_H
    schap_d = DIEP - 0.14
    for mnr in range(N_MOD):
        xm = x_links + STIJL + MOD_B / 2 + mnr * (MOD_B + STIJL)
        # plank, licht hellend naar voren (voorkant lager)
        ouder(doos(f"plank_{mnr}_{i}", (xm, y0 + 0.06 + schap_d / 2, z_s + math.sin(HELLING) * schap_d / 2), (MOD_B - 0.02, schap_d, 0.012), M_SCHAP, rot=(-HELLING, 0, 0)))
        # prijsrail + kaartjes
        ouder(doos(f"rail_{mnr}_{i}", (xm, y0 + 0.055, z_s - 0.018), (MOD_B - 0.02, 0.012, 0.04), M_RAIL))
        n_k = 7 if mnr == 1 else 8
        for k in range(n_k):
            xk = xm - MOD_B / 2 + 0.03 + (MOD_B - 0.06) * (k + 0.5) / n_k
            rood = (mnr != 1 and random.random() < 0.18)
            ouder(doos(f"kaart_{mnr}_{i}_{k}", (xk, y0 + 0.048, z_s - 0.018), (0.07, 0.002, 0.032), M_KAART_ROOD if rood else M_KAART))
            ouder(doos(f"kaarttekst_{mnr}_{i}_{k}", (xk, y0 + 0.046, z_s - 0.012), (0.05, 0.001, 0.004), M_BINNEN))
            ouder(doos(f"kaartprijs_{mnr}_{i}_{k}", (xk - 0.012, y0 + 0.046, z_s - 0.026), (0.03, 0.001, 0.009), M_BINNEN if not rood else M_KAART))
        if mnr == 1:
            ouder(doos(f"strip_{i}", (xm, y0 + 0.049, z_s - 0.041), (MOD_B - 0.06, 0.003, 0.008), M_STRIP[laag]))
        # led onder de plank, naar voren
        if i > 0:
            ouder(doos(f"led_{mnr}_{i}", (xm, y0 + 0.085, z_s - 0.009), (MOD_B * 0.92, 0.022, 0.006), M_LED))
        # producten: vol, rijen diep, tot de rand
        n_kol = 10
        n_rij = 4
        stap_x = (MOD_B - 0.03) / n_kol
        stap_y = BAK_D + 0.006
        for r in range(n_rij):
            for k in range(n_kol):
                if random.random() < 0.06 and r == 0: continue           # enkele gaten: er is al gekocht
                x = xm - MOD_B / 2 + 0.015 + stap_x * (k + 0.5) + random.uniform(-0.003, 0.003)
                y = y0 + 0.075 + BAK_D / 2 + r * stap_y + random.uniform(-0.002, 0.002)
                z = z_s + 0.006 + math.sin(HELLING) * (y - (y0 + 0.06))
                if mnr == 1:
                    sal = salades[laag][k % len(salades[laag])]
                    bakje(f"b{mnr}_{i}_{r}_{k}", (x, y, z), laag, sal, random.uniform(-0.1, 0.1))
                else:
                    # buurmodules: fruit (links) en overig (rechts) — zelfde bakjes, andere salades en PET-helder;
                    # fruit gestapeld twee hoog zoals in de foto
                    sal = alle_sal[(k + i + mnr * 3) % len(alle_sal)]
                    bakje(f"b{mnr}_{i}_{r}_{k}", (x, y, z), lagen[(i + 1) % 5], sal, random.uniform(-0.3, 0.3), M_PET)
                    if mnr == 0 and i < 3 and random.random() < 0.7:
                        bakje(f"b{mnr}_{i}_{r}_{k}_2", (x, y, z + BAK_H + 0.009), lagen[(i + 2) % 5], sal, random.uniform(-0.3, 0.3), M_PET)

# ---------- licht en wereld ----------
w = sc.world = bpy.data.worlds.new("wereld"); w.use_nodes = True
wn = w.node_tree; bg = wn.nodes["Background"]
env = wn.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(UIT, "pano360_2.jpg"))
wn.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.4
bpy.ops.object.light_add(type="AREA", location=(0, AFSTAND - 0.5, 1.5))
l = bpy.context.active_object; l.data.energy = 120; l.data.size = 2.5; l.data.color = (1.0, 0.96, 0.9); l.rotation_euler = (math.radians(30), 0, 0)

# ---------- camera + render ----------
bpy.ops.object.camera_add(location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
cam = bpy.context.active_object; sc.camera = cam
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.compression = 60
if STILL:
    cam.data.type = "PERSP"; cam.data.lens = 28
    cam.location = (-0.35, AFSTAND - 1.3, 0.05); cam.rotation_euler = (math.radians(86), 0, math.radians(-8))
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1000; sc.cycles.samples = 64
    sc.render.film_transparent = False; sc.render.image_settings.color_mode = "RGB"
    sc.render.filepath = os.path.join(UIT, "_koelwand_still.png")
else:
    cam.data.type = "PANO"; cam.data.panorama_type = "EQUIRECTANGULAR"
    cam.data.stereo.convergence_mode = "OFFAXIS"; cam.data.stereo.interocular_distance = 0.064
    cam.data.stereo.use_spherical_stereo = True; cam.data.stereo.use_pole_merge = True
    sc.render.film_transparent = True; sc.render.use_multiview = True; sc.render.views_format = "STEREO_3D"
    sc.render.image_settings.views_format = "STEREO_3D"; sc.render.image_settings.stereo_3d_format.display_mode = "TOPBOTTOM"
    sc.render.image_settings.color_mode = "RGBA"
    res = 1024 if PREVIEW else 4096
    sc.render.resolution_x, sc.render.resolution_y = res, res // 2; sc.cycles.samples = 16 if PREVIEW else 96
    sc.render.filepath = os.path.join(UIT, "koelwand_preview.png" if PREVIEW else "koelwand_stereo.png")
sc.render.resolution_percentage = 100
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HIER, "koelwand.blend"))
bpy.ops.render.render(write_still=True)
print("KLAAR:", sc.render.filepath)
