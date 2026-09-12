# Street Workout Park — 3D scena u Blenderu

Projekt iz kolegija **3D računalna grafika**
Fakultet primijenjene matematike i informatike, Osijek
Autor: **Luka Barić**

![Pregled parka](renders/01_pregled.png)

---

## O čemu se radi

Napravio sam 3D model **street workout parka** — vanjskog vježbališta sa spravama za vježbanje vlastitom težinom. Park sadrži šipke za zgibove, majmunske ljestve, paralelne šipke za propadanja, švedske ljestve, karike na lancima, klupu za trbušnjake i niske parlete za sklekove.

U parku su **tri vježbača** i svaki radi svoju vježbu:

| Vježbač | Vježba | Sprava |
|---|---|---|
| Crvena majica | zgibovi | visoka šipka na 2.50 m |
| Plava majica | australski zgibovi | karike na lancima |
| Siva majica | trbušnjaci | kosa klupa s valjcima |

Cijela scena nastaje **pokretanjem jedne Python skripte** u Blenderu. Ništa nije modelirano ručno miševanjem po sučelju.

| Podatak | Vrijednost |
|---|---|
| Objekata u sceni | 210 |
| Poligona | ~8 700 |
| Sprava | 8 |
| Vježbača | 3 |
| Animacija | 250 sličica = 10 sekundi pri 25 fps |
| Testirano na | Blender 4.2 – 5.0 |

---

## Pokretanje

1. Otvori Blender i klikni na karticu **Scripting** gore
2. Klikni **New**, pa zalijepi sadržaj datoteke `street_workout_park.py`
3. Klikni **Run Script** (ili pritisni `Alt` + `P`)

Scena se izgradi za par sekundi.

| Tipka | Što radi |
|---|---|
| `Razmaknica` | pokreni / zaustavi animaciju |
| `Numpad 0` | pogledaj kroz kameru |
| `F12` | renderiraj jednu sliku |
| `Ctrl` + `F12` | renderiraj cijelu animaciju |

Ako render traje predugo, na vrhu skripte promijeni `MOTOR = "CYCLES"` u `MOTOR = "EEVEE"`. EEVEE je puno brži, samo malo lošije izgleda.

---

## Kako skripta radi

Ovo je dio koji je najvažniji za razumjeti, pa ga objašnjavam korak po korak.

### 1. Sve crtam s četiri funkcije

Cijeli park, uključujući ljude, sastavljen je od svega četiri vrste oblika:

```python
cijev(tocka_a, tocka_b, polumjer, materijal)   # valjak između dvije točke
kugla(sredina, polumjer, materijal)            # kugla
kvadar(sredina, dimenzije, materijal)          # kocka
konus(a, b, polumjer_a, polumjer_b, materijal) # valjak koji se sužava
```

Najviše koristim `cijev()`. Njome crtam stupove sprava, vodoravne šipke, lance, ali i ruke i noge vježbača. Funkcija dobije dvije točke u prostoru i sama okrene valjak u pravi smjer:

```python
smjer = b - a
objekt.rotation_quaternion = smjer.to_track_quat('Z', 'Y')
```

`to_track_quat()` je gotova Blenderova funkcija koja iz vektora napravi rotaciju. Zbog nje ne moram ručno računati kutove.

### 2. Sprave

Svaka sprava je zasebna funkcija, npr.:

```python
def okvir_za_zgibove():
    for x in (-5.0, -3.0):
        for y in (-1.0, 1.0):
            stup(x, y, 2.65)                    # četiri stupa
    cijev((-5.0, -1.06, 2.50), (-5.0, 1.06, 2.50), 0.025, ZUTA)  # šipka
```

Stupovi su žuti s crnom kapom na vrhu, kao na pravim spravama.

### 3. Vježbači

Svaki vježbač je hrpa valjaka (ruke, noge, trup) i kugli (zglobovi, glava). Trup crtam s `konus()` jer se sužava od prsa prema struku, pa izgleda prirodnije nego običan valjak.

### 4. Animacija — ovo je ključni dio

Za animaciju koristim **zglobove**. Zglob je obični prazan objekt (u Blenderu se zove Empty). On se u renderu **ne vidi** — služi samo kao os oko koje se nešto rotira.

Postupak je uvijek isti:

1. nacrtam dijelove tijela tamo gdje trebaju biti
2. napravim zglob na mjestu lakta / kuka / šake
3. **zakačim** dijelove tijela na zglob (u Blenderu: parentanje)
4. zarotiram zglob → svi zakačeni dijelovi se zarotiraju s njim

```python
def zakaci(dijete, roditelj, polozaj_roditelja):
    dijete.parent = roditelj
    dijete.matrix_parent_inverse = Matrix.Translation(-Vector(polozaj_roditelja))
```

Ta druga linija samo znači „ostani gdje jesi, ali od sada prati roditelja". Bez nje bi dio tijela odskočio na krivo mjesto.

Sama animacija je onda samo upisivanje dva ključna kadra po ponavljanju:

```python
kljucni_kadar(zgib["lakat_L"], dolje, (0, 0, 0))              # ruka ispružena
kljucni_kadar(zgib["lakat_L"], gore,  (0, radians(117), 0))   # ruka savijena
```

Blender sam izračuna sve sličice između ta dva položaja. Zbog toga se pokret ubrzava i usporava na krajevima, što izgleda prirodno.

---

## Kako je riješen svaki vježbač

### Zgibovi

Kod zgiba **šake ostaju na šipki, a tijelo se penje**. Zato sam lanac postavio naopako: prvi zglob je gore na šipki, drugi je u laktu, a tijelo visi na kraju nadlaktice.

```
zglob na šipki (šaka)
   └── podlaktica
        └── zglob u laktu
             └── nadlaktica
                  └── zglob tijela
                       └── trup, glava, noge
```

Kad zarotiram šaku i lakat, ruka se savije i tijelo se automatski digne. Ne moram računati gdje će tijelo završiti.

Tijelo ima još jedan zglob koji ga usput uspravi za −76°. Bez toga bi tijelo visjelo ukoso zajedno s nadlakticom i vježbač bi na vrhu zgiba bio gotovo vodoravan.

Desna ruka rotira se **istim kutovima** kao lijeva. Budući da je poza simetrična, obje šake ostaju na šipki i ramena se poklope.

| Dolje | Gore |
|---|---|
| ![](renders/03a_zgib_dolje.png) | ![](renders/03b_zgib_gore.png) |

### Australski zgibovi na karikama

Isti trik kao kod zgiba: ruke vise s karika, tijelo je na kraju ruke. Dodatno sam tijelu dao zakret od 18° tako da **stopala ostanu na podu** dok se prsa dižu prema karikama.

Provjerio sam to brojkama, ne na oko. Skripta koja ispisuje položaj cipele u sličici 1 i sličici 26 daje:

```
slicica  1:  cipela = [-3.210, -3.14, 0.080]
slicica 26:  cipela = [-3.214, -3.14, 0.087]
```

Stopalo se pomakne 4 milimetra. Znači da tijelo stvarno rotira oko peta, a ne lebdi.

| Dolje | Gore |
|---|---|
| ![](renders/04a_karike_dolje.png) | ![](renders/04b_karike_gore.png) |

### Trbušnjaci

Najjednostavniji od sve trojice. Noge su nepomične jer su zakvačene pod valjke klupe, a gornji dio tijela visi na jednom zglobu u kuku. Cijela animacija je **jedna jedina rotacija** od −58°.

| Dolje | Gore |
|---|---|
| ![](renders/05a_trbuh_dolje.png) | ![](renders/05b_trbuh_gore.png) |

---

## Kamera

Kamera se polako okreće oko parka. Napravljeno na najjednostavniji mogući način:

1. u sredinu parka stavim prazan objekt
2. kameru zakačim na njega
3. tom praznom objektu upišem 0° u prvoj sličici i 360° u zadnjoj

Kamera uvijek gleda u sredinu parka jer sam joj dodao **Track To** ograničenje.

Osim glavne, u sceni su i četiri nepomične kamere za slike u prezentaciji: `Kamera_zgibovi`, `Kamera_karike`, `Kamera_trbusnjaci` i `Kamera_odozgo`.

![Pogled odozgo](renders/02_odozgo.png)

---

## Postavke na vrhu skripte

```python
BROJ_SLICICA = 250              # trajanje animacije
SLICICA_PO_PONAVLJANJU = 50     # jedno ponavljanje vjezbe
MOTOR = "CYCLES"                # "CYCLES" ili "EEVEE"
UZORAKA = 128                   # kvaliteta rendera
```

Ako `SLICICA_PO_PONAVLJANJU` smanjiš na 30, vježbači rade brže. Ako povećaš na 80, rade sporije.

---

## Što bi se još moglo dodati

- vježbač koji radi propadanja na paralelnim šipkama
- prijelaz rukama po majmunskim ljestvama (traži pomicanje šaka s prečke na prečku)
- noćna verzija parka s uličnom rasvjetom
- stabla i klupe oko parka

---

## Sadržaj repozitorija

```
street_workout_park.py    glavna skripta
README.md                 ova datoteka
renders/                  renderirane slike
docs/                     seminarski rad i prezentacija
```

---

## Izvori

- Blender Python API — https://docs.blender.org/api/current/
- Blender Manual, poglavlja Parenting, Keyframes i Cycles
