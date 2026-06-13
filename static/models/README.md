# Vymeniteľný 3D model Karla (skin)

Sem vlož súbor **`karel.glb`** a renderer ho použije namiesto predvolenej
kvádrovej postavičky. Ak súbor chýba, ostáva default robot (žiadna chyba).

```
static/models/karel.glb     ← tu
```

## Ladenie vzhľadu

V `static/js/render3d.js` (hore) sú tri konštanty:

| Konštanta | Význam |
|-----------|--------|
| `KAREL_MODEL_URL` | cesta k modelu (default `models/karel.glb`) |
| `KAREL_MODEL_YAW` | pootočenie, aby model pozeral na +X (Karelovo „dopredu"). Skús `0`, `±Math.PI/2`, `Math.PI` |
| `KAREL_MODEL_HEIGHT` | výška modelu v jednotkách políčka (default `1.25`) |

Renderer model automaticky **vycentruje** (X/Z), **postaví na podlahu** a
**zmenší**, aby sa zmestil do políčka — netreba ho ručne mierkovať.

## Export z Blenderu (`.blend` → `.glb`)

1. Otvor `.blend` v Blenderi.
2. (Odporúčané) zníž počet polygónov: označ model → modifier **Decimate**
   (Ratio ~0.05–0.2) → Apply. Sochárske modely majú státisíce trojuholníkov,
   pre web stačí pár tisíc.
3. Zmenši textúry na ~512–1024 px (UV/Image editor → Resize), inak je `.glb`
   zbytočne veľký (cieľ: celé `.glb` ideálne < 2–3 MB).
4. **File → Export → glTF 2.0 (.glb)**:
   - Format: **glTF Binary (.glb)** (textúry sa vložia dovnútra)
   - Include: Selected Objects (ak chceš len model)
   - Transform: +Y Up (default)
5. Výsledný `karel.glb` polož do tohto priečinka, obnov stránku.

## Licencia

Pozor na autorské práva modelu. Napr. **Grogu / Baby Yoda je IP Disney** —
pre použitie v triede OK, ale **nevkladaj ho do verejného repozitára ani do
distribuovaného Docker image**. Tento priečinok je preto v repe prázdny (model
si dodáš lokálne, prípadne cez data volume).
