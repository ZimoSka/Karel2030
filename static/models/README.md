# Vymeniteľné 3D modely Karla (skiny)

Vzhľad Karla sa vyberá v okne **⚙ Nastavenia → Vzhľad Karla**. Skiny sú
definované v `static/js/render3d.js` v objekte **`KAREL_SKINS`**:

```js
const KAREL_SKINS = {
  grogu: { label: 'Grogu', url: 'models/grogu.glb', yaw: 0, height: 1.3 },
  robot: { label: 'Robot', url: null },   // null = kvádrová postavička
};
const DEFAULT_SKIN = 'grogu';
```

GLB súbory dávaj sem do `static/models/`. Ak súbor chýba alebo sa nenačíta,
renderer ticho padne späť na kvádrového robota (žiadna chyba).

## Pridanie / ladenie skinu

1. Polož `*.glb` do `static/models/`.
2. Pridaj záznam do `KAREL_SKINS` (`url`, `yaw`, `height`) a do výberu v
   `static/js/app.js` (`btn-app-settings` → pole `skins`).
3. Ladenie:
   - `yaw` — pootočenie (rad), aby model pozeral na +X (Karelovo „dopredu"):
     skús `0`, `±Math.PI/2`, `Math.PI`.
   - `height` — výška v jednotkách políčka (~1.2–1.3).

Renderer model automaticky **vycentruje** (X/Z), **postaví na podlahu** a
**zmenší**, aby sa zmestil do políčka — netreba ho ručne mierkovať.

## Veľkosť / výkon

`grogu.glb` má ~20 MB (textúry + hi-poly). Funguje, ale na pomalej sieti sa
načítava dlho. Pre lepší výkon odporúčam zmenšiť:
```
npx @gltf-transform/cli optimize models/grogu.glb models/grogu.glb \
    --texture-size 1024 --compress draco
```

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
