# -*- coding: utf-8 -*-
"""
===========================================================================
 STREET WORKOUT PARK
 Projekt iz kolegija: 3D racunalna grafika
 Autor: Luka Baric
 Fakultet primijenjene matematike i informatike, Osijek
---------------------------------------------------------------------------
 Skripta u Blenderu gradi cijeli street workout park i animira tri vjezbaca.

 KAKO SKRIPTA RADI (kratko objasnjenje za prezentaciju):

   1. Sve u sceni crtam pomocu cetiri jednostavne funkcije:
        cijev()  - valjak izmedu dvije tocke   (stupovi, sipke, ruke, noge)
        kugla()  - kugla                        (zglobovi, glava, kape stupova)
        kvadar() - kocka zadanih dimenzija      (pod, ploca klupe)
        konus()  - valjak koji se suzava        (trup covjeka)

   2. Covjeculjke sastavljam od tih valjaka i kugli.

   3. Za animaciju koristim ZGLOBOVE. Zglob je obican prazan objekt (Empty).
      Dijelove tijela zakacim ("parentam") na zglob. Kad zarotiram zglob,
      svi njegovi dijelovi se zarotiraju zajedno s njim - kao pravi lakat.

   4. Animaciju radim tako da zglobu upisem dva kljucna kadra:
      polozaj "dolje" i polozaj "gore". Blender sam izracuna sve izmedu.

 POKRETANJE:
   Blender -> kartica Scripting -> New -> zalijepi kod -> Run Script (Alt+P)
===========================================================================
"""

import bpy
import math
from math import radians
from mathutils import Vector, Matrix


# ==========================================================================
# 1. POSTAVKE
# ==========================================================================

BROJ_SLICICA = 250              # trajanje animacije (250 / 25 fps = 10 sekundi)
SLICICA_PO_PONAVLJANJU = 50     # jedno ponavljanje vjezbe traje 50 slicica
MOTOR = "CYCLES"                # "CYCLES" (ljepse) ili "EEVEE" (puno brze)
UZORAKA = 128                   # kvaliteta rendera za Cycles


# ==========================================================================
# 2. POMOCNE FUNKCIJE
# ==========================================================================

def ocisti_scenu():
    """Brise sve iz scene da pocnemo od prazne datoteke."""
    for objekt in list(bpy.data.objects):
        bpy.data.objects.remove(objekt, do_unlink=True)
    for kolekcija in list(bpy.data.collections):
        bpy.data.collections.remove(kolekcija)


def napravi_materijal(ime, boja, hrapavost=0.4, metalnost=0.0):
    """Stvara jednostavan materijal (boja + koliko je sjajan)."""
    if ime in bpy.data.materials:
        return bpy.data.materials[ime]
    mat = bpy.data.materials.new(ime)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = boja
    bsdf.inputs["Roughness"].default_value = hrapavost
    bsdf.inputs["Metallic"].default_value = metalnost
    return mat


def oboji(objekt, materijal):
    """Dodjeljuje materijal objektu."""
    if objekt is not None and materijal is not None:
        objekt.data.materials.clear()
        objekt.data.materials.append(materijal)
    return objekt


def cijev(tocka_a, tocka_b, polumjer, materijal, ime="Cijev"):
    """
    Crta valjak izmedu dvije tocke u prostoru.

    Ovo je najvaznija funkcija u cijeloj skripti. Njome crtam sve sto je
    duguljasto: stupove sprava, sipke, lance, ruke i noge covjeculjaka.
    Blender sam okrene valjak u pravi smjer pomocu to_track_quat().
    """
    a = Vector(tocka_a)
    b = Vector(tocka_b)
    smjer = b - a
    duljina = smjer.length
    if duljina < 0.0001:
        return None

    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=polumjer,
                                        depth=duljina, location=(a + b) / 2)
    objekt = bpy.context.object
    objekt.name = ime
    objekt.rotation_mode = 'QUATERNION'
    objekt.rotation_quaternion = smjer.to_track_quat('Z', 'Y')
    return oboji(objekt, materijal)


def konus(tocka_a, tocka_b, polumjer_a, polumjer_b, materijal, ime="Konus"):
    """Isto kao cijev, samo se polumjer mijenja od pocetka prema kraju.
    Koristim ga za trup covjeka jer se suzava od prsa prema struku."""
    a = Vector(tocka_a)
    b = Vector(tocka_b)
    smjer = b - a
    duljina = smjer.length
    if duljina < 0.0001:
        return None

    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=polumjer_a,
                                    radius2=polumjer_b, depth=duljina,
                                    location=(a + b) / 2)
    objekt = bpy.context.object
    objekt.name = ime
    objekt.rotation_mode = 'QUATERNION'
    objekt.rotation_quaternion = smjer.to_track_quat('Z', 'Y')
    return oboji(objekt, materijal)


def kugla(sredina, polumjer, materijal, ime="Kugla"):
    """Crta glatku kuglu. Koristim je za zglobove, glave i kape stupova."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8,
                                         radius=polumjer, location=sredina)
    objekt = bpy.context.object
    objekt.name = ime
    for poligon in objekt.data.polygons:
        poligon.use_smooth = True
    return oboji(objekt, materijal)


def kvadar(sredina, dimenzije, materijal, ime="Kvadar", nagib=(0, 0, 0)):
    """Crta kocku zadane sirine, dubine i visine."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=sredina, rotation=nagib)
    objekt = bpy.context.object
    objekt.name = ime
    objekt.data.transform(Matrix.Diagonal((dimenzije[0], dimenzije[1],
                                           dimenzije[2], 1.0)))
    return oboji(objekt, materijal)


def zglob(ime, polozaj):
    """
    Stvara ZGLOB - prazan objekt koji sluzi kao os rotacije.

    Zglob se u renderu ne vidi. Njegova jedina uloga je da na njega
    zakacim dijelove tijela, pa kad zarotiram zglob, dijelovi se
    zarotiraju oko njega. Tako radi lakat, rame ili kuk.
    """
    bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.12, location=polozaj)
    objekt = bpy.context.object
    objekt.name = ime
    return objekt


def zakaci(dijete, roditelj, polozaj_roditelja):
    """
    Zakaci objekt na zglob (u Blenderu se to zove "parentanje").

    Objekt ostaje tocno tamo gdje je nacrtan, ali od sada prati svaku
    rotaciju svog roditelja.
    """
    if dijete is None:
        return None
    dijete.parent = roditelj
    dijete.matrix_parent_inverse = Matrix.Translation(-Vector(polozaj_roditelja))
    return dijete


def kljucni_kadar(objekt, slicica, rotacija):
    """Upisuje kljucni kadar - rotaciju objekta u odredenoj slicici."""
    objekt.rotation_euler = rotacija
    objekt.keyframe_insert("rotation_euler", frame=slicica)


# ==========================================================================
# 3. MATERIJALI (boje kao na stvarnim spravama: zuti okvir, crni detalji)
# ==========================================================================

ZUTA     = napravi_materijal("Zuta_Sprava",   (0.95, 0.62, 0.02, 1), 0.35, 0.25)
CRNA     = napravi_materijal("Crna_Detalj",   (0.02, 0.02, 0.02, 1), 0.45, 0.20)
PODLOGA  = napravi_materijal("Podloga_Guma",  (0.14, 0.15, 0.17, 1), 0.90, 0.00)
RUB      = napravi_materijal("Rub_Beton",     (0.42, 0.41, 0.39, 1), 0.85, 0.00)
TRAVA    = napravi_materijal("Trava",         (0.07, 0.17, 0.05, 1), 1.00, 0.00)

KOZA     = napravi_materijal("Koza",          (0.78, 0.56, 0.42, 1), 0.60, 0.00)
KOZA_T   = napravi_materijal("Koza_Tamna",    (0.45, 0.28, 0.17, 1), 0.60, 0.00)
HLACE    = napravi_materijal("Hlace",         (0.05, 0.06, 0.10, 1), 0.85, 0.00)
CIPELE   = napravi_materijal("Cipele",        (0.80, 0.80, 0.82, 1), 0.55, 0.00)

MAJICA_1 = napravi_materijal("Majica_Crvena", (0.62, 0.08, 0.06, 1), 0.80)
MAJICA_2 = napravi_materijal("Majica_Plava",  (0.05, 0.22, 0.48, 1), 0.80)
MAJICA_3 = napravi_materijal("Majica_Siva",   (0.52, 0.53, 0.55, 1), 0.80)


# ==========================================================================
# 4. PODLOGA
# ==========================================================================

def napravi_pod():
    """Travnata okolina i tamna gumena podloga na kojoj stoje sprave."""
    kvadar((0, 0, -0.32), (70, 70, 0.40), TRAVA, "Trava")
    kvadar((0, 0, -0.06), (16.0, 11.5, 0.24), PODLOGA, "Gumena_podloga")
    kvadar((0,  5.90, -0.04), (16.6, 0.5, 0.26), RUB, "Rub")
    kvadar((0, -5.90, -0.04), (16.6, 0.5, 0.26), RUB, "Rub")
    kvadar(( 8.25, 0, -0.04), (0.5, 12.1, 0.26), RUB, "Rub")
    kvadar((-8.25, 0, -0.04), (0.5, 12.1, 0.26), RUB, "Rub")


# ==========================================================================
# 5. SPRAVE
# ==========================================================================

def stup(x, y, visina):
    """Zuti nosivi stup s crnom kapom na vrhu - osnovni dio svake sprave."""
    cijev((x, y, 0.0), (x, y, visina), 0.055, ZUTA, "Stup")
    kvadar((x, y, visina + 0.035), (0.135, 0.135, 0.075), CRNA, "Kapa_stupa")


def okvir_za_zgibove():
    """Sprava za zgibove: cetiri stupa i dvije sipke na razlicitim visinama.
    Na visu sipku (2.50 m) stavljam prvog covjeculjka."""
    for x in (-5.0, -3.0):
        for y in (-1.0, 1.0):
            stup(x, y, 2.65)
    for y in (-1.0, 1.0):
        cijev((-5.0, y, 2.65), (-3.0, y, 2.65), 0.045, ZUTA, "Greda")
    cijev((-5.0, -1.06, 2.50), (-5.0, 1.06, 2.50), 0.025, ZUTA, "Sipka_visoka")
    cijev((-3.0, -1.06, 2.10), (-3.0, 1.06, 2.10), 0.025, ZUTA, "Sipka_niska")


def majmunske_ljestve():
    """Vodoravne ljestve po kojima se prelazi rukama."""
    for x in (-1.0, 3.0):
        for y in (-1.0, 1.0):
            stup(x, y, 2.55)
    for y in (-1.0, 1.0):
        cijev((-1.0, y, 2.45), (3.0, y, 2.45), 0.045, ZUTA, "Vodilica")
    x = -0.8
    while x < 2.9:
        cijev((x, -1.0, 2.45), (x, 1.0, 2.45), 0.024, ZUTA, "Precaga")
        x += 0.35


def paralelne_sipke():
    """Sipke za propadanja (dips)."""
    for x in (1.2, 3.0):
        for y in (2.7, 3.3):
            stup(x, y, 1.30)
    for y in (2.7, 3.3):
        cijev((1.1, y, 1.30), (3.1, y, 1.30), 0.028, ZUTA, "Sipka_propadanje")


def svedske_ljestve():
    """Okomite ljestve s puno precaga."""
    for y in (-1.0, 1.0):
        stup(6.2, y, 2.60)
    z = 0.45
    while z < 2.55:
        cijev((6.2, -1.0, z), (6.2, 1.0, z), 0.024, ZUTA, "Precaga_okomita")
        z += 0.22
    for y in (-1.0, 1.0):
        cijev((6.2, y, 2.60), (7.35, y, 0.06), 0.040, ZUTA, "Potpora")


def okvir_s_karikama():
    """Karike obješene na lancima. Na njima drugi covjeculjak radi
    australske zgibove - lezi koso i privlaci prsa prema karikama."""
    for y in (-3.7, -2.3):
        stup(-1.0, y, 2.60)
    cijev((-1.0, -3.75, 2.50), (-1.0, -2.25, 2.50), 0.045, ZUTA, "Greda_karike")
    for y in (-3.25, -2.75):
        cijev((-1.0, y, 2.50), (-1.0, y, 1.13), 0.013, CRNA, "Lanac")
        bpy.ops.mesh.primitive_torus_add(location=(-1.0, y, 1.05),
                                         rotation=(0, radians(90), 0),
                                         major_radius=0.11, minor_radius=0.018,
                                         major_segments=24, minor_segments=10)
        karika = bpy.context.object
        karika.name = "Karika"
        for poligon in karika.data.polygons:
            poligon.use_smooth = True
        oboji(karika, CRNA)


def klupa_za_trbusnjake():
    """Kosa klupa s valjcima za stopala. Na njoj treci covjeculjak radi
    trbusnjake."""
    kvadar((4.0, -3.05, 0.56), (0.46, 1.80, 0.09), CRNA, "Ploca_klupe",
           nagib=(radians(10), 0, 0))
    cijev((4.0, -3.85, 0.0), (4.0, -3.85, 0.42), 0.040, ZUTA, "Noga_klupe")
    cijev((4.0, -2.30, 0.0), (4.0, -2.30, 0.69), 0.040, ZUTA, "Noga_klupe")
    cijev((3.72, -3.85, 0.05), (4.28, -3.85, 0.05), 0.040, ZUTA, "Stopica")
    cijev((3.72, -2.30, 0.05), (4.28, -2.30, 0.05), 0.040, ZUTA, "Stopica")
    for y in (-2.28, -2.03):
        cijev((3.70, y, 0.60), (4.30, y, 0.60), 0.055, CRNA, "Valjak")
    cijev((4.0, -2.30, 0.69), (4.0, -2.03, 0.69), 0.035, ZUTA, "Drzac_valjaka")


def niske_paralete():
    """Niske sipke za sklekove."""
    for x in (6.3, 7.3):
        for y in (-3.4, -2.6):
            cijev((x, y, 0.0), (x, y, 0.32), 0.030, ZUTA, "Noga_paralete")
        cijev((x, -3.46, 0.32), (x, -2.54, 0.32), 0.026, ZUTA, "Sipka_paralete")


def niske_sipke():
    """Dvije niske sipke za australske zgibove i preskoke."""
    for x, visina in ((-6.2, 1.15), (-4.6, 0.85)):
        for y in (-3.6, -2.4):
            stup(x, y, visina)
        cijev((x, -3.66, visina), (x, -2.34, visina), 0.026, ZUTA, "Niska_sipka")


def napravi_sprave():
    okvir_za_zgibove()
    niske_sipke()
    majmunske_ljestve()
    paralelne_sipke()
    svedske_ljestve()
    okvir_s_karikama()
    klupa_za_trbusnjake()
    niske_paralete()


# ==========================================================================
# 6. COVJECULJCI
# --------------------------------------------------------------------------
# Svaki covjeculjak sastavljam od valjaka (ruke, noge, trup) i kugli
# (zglobovi, glava). Dijelove koje zelim animirati zakacim na zglobove.
# ==========================================================================

def ruka(rame, lakat, saka, majica, koza):
    """Crta jednu ruku: nadlakticu, podlakticu i kuglice na zglobovima."""
    return [cijev(rame, lakat, 0.052, koza, "Nadlaktica"),
            cijev(lakat, saka, 0.042, koza, "Podlaktica"),
            kugla(rame, 0.058, majica, "Zglob_rame"),
            kugla(lakat, 0.046, koza, "Zglob_lakat"),
            kugla(saka, 0.055, koza, "Saka")]


def noga(kuk, koljeno, gleznj, stopalo, koza):
    """Crta jednu nogu: bedro, potkoljenicu i cipelu."""
    return [cijev(kuk, koljeno, 0.072, HLACE, "Bedro"),
            cijev(koljeno, gleznj, 0.053, koza, "Potkoljenica"),
            cijev(gleznj, stopalo, 0.046, CIPELE, "Stopalo"),
            kugla(kuk, 0.070, HLACE, "Zglob_kuk"),
            kugla(koljeno, 0.060, koza, "Zglob_koljeno"),
            kugla(stopalo, 0.062, CIPELE, "Cipela")]


def trup_i_glava(rame_l, rame_d, kuk, vrat, glava, majica, koza):
    """Crta trup (suzava se prema struku), ramena, vrat i glavu."""
    rame_sredina = (Vector(rame_l) + Vector(rame_d)) / 2
    struk = rame_sredina.lerp(Vector(kuk), 0.60)

    glava_objekt = kugla(glava, 0.115, koza, "Glava")
    glava_objekt.scale = (0.95, 1.0, 1.08)

    return [konus(rame_sredina, struk, 0.140, 0.105, majica, "Prsa"),
            konus(struk, kuk, 0.105, 0.118, HLACE, "Struk"),
            kugla(rame_sredina, 0.135, majica, "Ramena_kugla"),
            kugla(kuk, 0.115, HLACE, "Zdjelica"),
            cijev(rame_l, rame_d, 0.080, majica, "Ramena"),
            cijev(vrat, glava, 0.045, koza, "Vrat"),
            kugla(rame_l, 0.058, majica, "Zglob_rame"),
            kugla(rame_d, 0.058, majica, "Zglob_rame"),
            glava_objekt]


# --------------------------------------------------------------------------
# COVJECULJAK 1 - ZGIBOVI
# --------------------------------------------------------------------------
# Ideja: ruke vise sa sipke, pa je prvi zglob gore na sipki (u saci),
# a drugi je u laktu. Kad zarotiram ta dva zgloba, ruka se savije i
# tijelo se digne - tocno kao pri pravom zgibu.
# Tijelo je zakaceno na kraj lijeve ruke. Desnu ruku rotiram jednako,
# pa obje sake ostaju na sipki i ramena se poklope.
# --------------------------------------------------------------------------

def covjeculjak_zgibovi():
    x = -5.0            # sipka je na x = -5.0
    z_sipka = 2.50      # visina sipke
    y_hvat = 0.30       # razmak saka od sredine

    zglobovi = {}

    for strana, y in (("L", -y_hvat), ("D", y_hvat)):
        saka = (x, y, z_sipka)
        lakat = (x, y, z_sipka - 0.29)
        rame = (x, y, z_sipka - 0.58)

        z_saka = zglob("Zgib_saka_" + strana, saka)
        z_lakat = zglob("Zgib_lakat_" + strana, lakat)
        zakaci(z_lakat, z_saka, saka)

        zakaci(cijev(saka, lakat, 0.042, KOZA, "Podlaktica"), z_saka, saka)
        zakaci(kugla(saka, 0.055, KOZA, "Saka"), z_saka, saka)
        zakaci(cijev(lakat, rame, 0.052, KOZA, "Nadlaktica"), z_lakat, lakat)
        zakaci(kugla(lakat, 0.046, KOZA, "Zglob_lakat"), z_lakat, lakat)

        zglobovi["saka_" + strana] = z_saka
        zglobovi["lakat_" + strana] = z_lakat

    # --- tijelo se kaci na lijevu ruku, u ramenu ---
    rame_l = (x, -y_hvat, z_sipka - 0.58)
    rame_d = (x,  y_hvat, z_sipka - 0.58)
    z_tijelo = zglob("Zgib_tijelo", rame_l)
    zakaci(z_tijelo, zglobovi["lakat_L"], (x, -y_hvat, z_sipka - 0.29))

    dijelovi = trup_i_glava(rame_l, rame_d, (x, 0.0, 1.26),
                            (x, 0.0, 2.00), (x, 0.02, 2.18), MAJICA_1, KOZA)
    for y in (-0.14, 0.14):
        dijelovi += noga((x, y * 0.93, 1.26),
                         (x - 0.08, y, 0.84),
                         (x - 0.32, y, 0.52),
                         (x - 0.44, y, 0.47), KOZA)

    for dio in dijelovi:
        zakaci(dio, z_tijelo, rame_l)

    zglobovi["tijelo"] = z_tijelo
    return zglobovi


# --------------------------------------------------------------------------
# COVJECULJAK 2 - AUSTRALSKI ZGIBOVI NA KARIKAMA
# --------------------------------------------------------------------------
# Isti trik kao kod zgibova: ruke vise s karika, tijelo je na kraju ruke.
# Kad se ruke saviju, tijelo se digne prema karikama. Tijelu sam dodao
# jos jedan zglob koji ga usput malo zakrene, tako da stopala ostanu
# na podu i izgleda kao da se tijelo okrece oko peta.
# --------------------------------------------------------------------------

def covjeculjak_karike():
    x_karika = -1.0
    z_karika = 1.05

    zglobovi = {}

    for strana, y in (("L", -3.25), ("D", -2.75)):
        karika = (x_karika, y, z_karika)
        lakat = (x_karika - 0.10, y, z_karika - 0.30)
        rame = (x_karika - 0.20, y, z_karika - 0.60)

        z_saka = zglob("Karike_saka_" + strana, karika)
        z_lakat = zglob("Karike_lakat_" + strana, lakat)
        zakaci(z_lakat, z_saka, karika)

        zakaci(cijev(karika, lakat, 0.042, KOZA_T, "Podlaktica"), z_saka, karika)
        zakaci(kugla(karika, 0.055, KOZA_T, "Saka"), z_saka, karika)
        zakaci(cijev(lakat, rame, 0.052, KOZA_T, "Nadlaktica"), z_lakat, lakat)
        zakaci(kugla(lakat, 0.046, KOZA_T, "Zglob_lakat"), z_lakat, lakat)

        zglobovi["saka_" + strana] = z_saka
        zglobovi["lakat_" + strana] = z_lakat

    # --- tijelo lezi koso, stopala su na podu ---
    rame_l = (x_karika - 0.20, -3.25, z_karika - 0.60)
    rame_d = (x_karika - 0.20, -2.75, z_karika - 0.60)
    z_tijelo = zglob("Karike_tijelo", rame_l)
    zakaci(z_tijelo, zglobovi["lakat_L"],
           (x_karika - 0.10, -3.25, z_karika - 0.30))

    kuk = (-2.20, -3.0, 0.34)
    dijelovi = trup_i_glava(rame_l, rame_d, kuk,
                            (-1.02, -3.0, 0.56), (-0.83, -3.0, 0.66),
                            MAJICA_2, KOZA_T)
    for y in (-3.14, -2.86):
        dijelovi += noga((-2.20, y, 0.34),
                         (-2.66, y, 0.26),
                         (-3.09, y, 0.16),
                         (-3.21, y, 0.08), KOZA_T)

    for dio in dijelovi:
        zakaci(dio, z_tijelo, rame_l)

    zglobovi["tijelo"] = z_tijelo
    return zglobovi


# --------------------------------------------------------------------------
# COVJECULJAK 3 - TRBUSNJACI NA KLUPI
# --------------------------------------------------------------------------
# Najjednostavniji od sve trojice: noge su nepomicne (zakvacene su pod
# valjke klupe), a gornji dio tijela je zakacen na zglob u kuku.
# Cijela animacija je jedna jedina rotacija tog zgloba.
# --------------------------------------------------------------------------

def covjeculjak_trbusnjaci():
    x = 4.0
    kuk = (x, -3.05, 0.66)

    # --- noge ostaju na klupi, njih uopce ne animiram ---
    for dy in (-0.14, 0.14):
        noga((x + dy, -3.05, 0.66),
             (x + dy, -2.56, 0.82),
             (x + dy, -2.30, 0.52),
             (x + dy, -2.14, 0.47), KOZA)

    # --- gornji dio tijela visi na zglobu u kuku ---
    z_kuk = zglob("Trbusnjaci_kuk", kuk)

    rame_l = (x - 0.20, -3.66, 0.54)
    rame_d = (x + 0.20, -3.66, 0.54)
    dijelovi = trup_i_glava(rame_l, rame_d, kuk,
                            (x, -3.77, 0.56), (x, -3.93, 0.60), MAJICA_3, KOZA)
    # ruke prekrizene na prsima
    dijelovi += ruka(rame_l, (x - 0.30, -3.44, 0.62), (x - 0.07, -3.34, 0.70),
                     MAJICA_3, KOZA)
    dijelovi += ruka(rame_d, (x + 0.30, -3.44, 0.62), (x + 0.07, -3.34, 0.70),
                     MAJICA_3, KOZA)

    for dio in dijelovi:
        zakaci(dio, z_kuk, kuk)

    return {"kuk": z_kuk}


# ==========================================================================
# 7. ANIMACIJA
# --------------------------------------------------------------------------
# Za svako ponavljanje vjezbe upisem samo dva kljucna kadra: polozaj
# "dolje" i polozaj "gore". Blender sam izracuna sve slicice izmedu njih.
# Kutove sam dobio tako da sam nacrtao trokut ruke na papiru i izmjerio
# koliko se lakat mora saviti da se rame digne na zeljenu visinu.
# ==========================================================================

def animiraj(zgib, karike, trbuh):
    ponavljanja = BROJ_SLICICA // SLICICA_PO_PONAVLJANJU + 1

    for i in range(ponavljanja):
        dolje = 1 + i * SLICICA_PO_PONAVLJANJU
        gore = dolje + SLICICA_PO_PONAVLJANJU // 2

        # --- ZGIBOVI ---
        # saka i lakat savijaju ruku, a tijelo se usput mora uspraviti
        # jer bi inace visjelo ukoso zajedno s nadlakticom
        for strana in ("L", "D"):
            kljucni_kadar(zgib["saka_" + strana], dolje, (0, 0, 0))
            kljucni_kadar(zgib["saka_" + strana], gore, (0, radians(-49), 0))
            kljucni_kadar(zgib["lakat_" + strana], dolje, (0, 0, 0))
            kljucni_kadar(zgib["lakat_" + strana], gore, (0, radians(117), 0))
        kljucni_kadar(zgib["tijelo"], dolje, (0, 0, 0))
        kljucni_kadar(zgib["tijelo"], gore, (0, radians(-76), 0))

        # --- KARIKE (australski zgibovi) ---
        # isto savijanje ruku, plus zakret tijela oko peta
        for strana in ("L", "D"):
            kljucni_kadar(karike["saka_" + strana], dolje, (0, 0, 0))
            kljucni_kadar(karike["saka_" + strana], gore, (0, radians(71), 0))
            kljucni_kadar(karike["lakat_" + strana], dolje, (0, 0, 0))
            kljucni_kadar(karike["lakat_" + strana], gore, (0, radians(-97), 0))
        kljucni_kadar(karike["tijelo"], dolje, (0, 0, 0))
        kljucni_kadar(karike["tijelo"], gore, (0, radians(18), 0))

        # --- TRBUSNJACI ---
        # jedna jedina rotacija kuka
        kljucni_kadar(trbuh["kuk"], dolje, (0, 0, 0))
        kljucni_kadar(trbuh["kuk"], gore, (radians(-58), 0, 0))


# ==========================================================================
# 8. SVJETLO, NEBO I KAMERA
# ==========================================================================

def napravi_svjetlo():
    """Sunce kao glavno svjetlo i vedro nebo kao pozadina."""
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 20))
    sunce = bpy.context.object
    sunce.name = "Sunce"
    sunce.data.energy = 3.2
    sunce.data.angle = radians(2.0)      # veci kut = mekse sjene
    sunce.rotation_euler = (radians(50), radians(5), radians(125))

    svijet = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = svijet
    svijet.use_nodes = True
    pozadina = svijet.node_tree.nodes["Background"]
    pozadina.inputs[0].default_value = (0.28, 0.45, 0.78, 1.0)
    pozadina.inputs[1].default_value = 0.60


def napravi_kameru(scena):
    """
    Kamera se polako okrece oko parka.

    Napravljeno na najjednostavniji nacin: kameru zakacim na prazan objekt
    u sredini parka i tom praznom objektu upisem dva kljucna kadra -
    0 stupnjeva na pocetku i 360 stupnjeva na kraju.
    """
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.0, -0.3, 1.5))
    meta = bpy.context.object
    meta.name = "Meta_kamere"

    bpy.ops.object.camera_add(location=(14.0, -15.0, 8.4))
    kamera = bpy.context.object
    kamera.name = "Kamera"
    kamera.data.lens = 30
    scena.camera = kamera

    prati = kamera.constraints.new(type='TRACK_TO')
    prati.target = meta
    prati.track_axis = 'TRACK_NEGATIVE_Z'
    prati.up_axis = 'UP_Y'

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.0, -0.3, 1.5))
    os_vrtnje = bpy.context.object
    os_vrtnje.name = "Os_vrtnje_kamere"
    kamera.parent = os_vrtnje

    os_vrtnje.rotation_euler = (0, 0, 0)
    os_vrtnje.keyframe_insert("rotation_euler", frame=1)
    os_vrtnje.rotation_euler = (0, 0, radians(360))
    os_vrtnje.keyframe_insert("rotation_euler", frame=BROJ_SLICICA)

    # dodatne nepomicne kamere za slike u prezentaciji
    dodatne = [("Kamera_zgibovi",     (-8.6, -3.2, 2.0), (-5.0, 0.0, 1.85), 50),
               ("Kamera_karike",      (-4.9, -6.2, 1.7), (-1.9, -3.0, 0.80), 45),
               ("Kamera_trbusnjaci",  (7.8, -6.0, 1.5),  (4.0, -3.0, 0.80), 50),
               ("Kamera_odozgo",      (0.0, -0.5, 19.0), (0.0, 0.0, 0.0), 28)]
    for ime, polozaj, cilj, zariste in dodatne:
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.2, location=cilj)
        tocka = bpy.context.object
        tocka.name = ime + "_meta"
        bpy.ops.object.camera_add(location=polozaj)
        k = bpy.context.object
        k.name = ime
        k.data.lens = zariste
        c = k.constraints.new(type='TRACK_TO')
        c.target = tocka
        c.track_axis = 'TRACK_NEGATIVE_Z'
        c.up_axis = 'UP_Y'


# ==========================================================================
# 9. POSTAVKE RENDERA
# ==========================================================================

def postavi_render(scena):
    scena.frame_start = 1
    scena.frame_end = BROJ_SLICICA
    scena.render.fps = 25
    scena.render.resolution_x = 1920
    scena.render.resolution_y = 1080

    if MOTOR == "CYCLES":
        try:
            scena.render.engine = 'CYCLES'
            scena.cycles.samples = UZORAKA
            scena.cycles.use_denoising = True
        except Exception:
            scena.render.engine = 'BLENDER_EEVEE'
    else:
        for ime in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
            try:
                scena.render.engine = ime
                break
            except Exception:
                continue

    try:
        scena.render.image_settings.file_format = 'FFMPEG'
        scena.render.ffmpeg.format = 'MPEG4'
        scena.render.ffmpeg.codec = 'H264'
    except Exception:
        scena.render.image_settings.file_format = 'PNG'
    scena.render.filepath = "//render/street_workout_"


# ==========================================================================
# 10. GLAVNI PROGRAM
# ==========================================================================

def main():
    print("=" * 60)
    print(" Gradim street workout park...")
    print("=" * 60)

    ocisti_scenu()
    scena = bpy.context.scene

    napravi_pod()
    print("  pod .................. gotovo")

    napravi_sprave()
    print("  sprave ............... gotovo")

    zgib = covjeculjak_zgibovi()
    karike = covjeculjak_karike()
    trbuh = covjeculjak_trbusnjaci()
    print("  tri covjeculjka ...... gotovo")

    animiraj(zgib, karike, trbuh)
    print("  animacija ............ gotovo")

    napravi_svjetlo()
    napravi_kameru(scena)
    postavi_render(scena)
    print("  svjetlo i kamera ..... gotovo")

    broj_objekata = len(bpy.data.objects)
    broj_poligona = sum(len(o.data.polygons) for o in bpy.data.objects
                        if o.type == 'MESH')
    print("-" * 60)
    print("  Objekata: %d    Poligona: %d" % (broj_objekata, broj_poligona))
    print("  Animacija: %d slicica (%.0f sekundi)"
          % (BROJ_SLICICA, BROJ_SLICICA / 25.0))
    print("  Razmaknica = pokreni animaciju,  F12 = render slike")
    print("=" * 60)


main()
