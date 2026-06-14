/* Karel 2030 — Three.js renderer stavu sveta (state JSON §4).
 * Súradnice: x=0 vľavo, y=0 dole (core) → Three: X = x, Z = -y, Y = výška.
 * Kvader = 5 jednotiek výšky, malé tehly sa stohujú NA kvadri.
 */
'use strict';

const BRICK_H = 0.27;            // výška malej tehly — zhodné s Python desktopom
const BIG_H = 5 * BRICK_H;       // kvader = 5 malých (= 1.35)

/* Vzhľad Karla ("skin"). 'robot' = kvádrová postavička (žiadny model).
 * Ostatné skiny majú GLB model — renderer ho normalizuje (vycentruje, postaví
 * na podlahu, zmenší do políčka). Ak GLB chýba/zlyhá, padne späť na robota.
 *   yaw    — pootočenie (rad), aby model pozeral na +X (Karelovo "dopredu")
 *             GLB štandard = +Z dopredu → yaw = -π/2 otočí na +X
 *             Ak model pozerá opačne (+X), yaw = 0; ak -Z, yaw = +π/2.
 *   height — výška modelu v jednotkách políčka */
const KAREL_SKINS = {
  grogu_small: { label: 'Grogu',         url: 'models/grogu_small.glb', yaw: Math.PI / 2, height: 1.3 },
  grogu:       { label: 'Grogu HD',      url: 'models/grogu.glb',       yaw: Math.PI / 2, height: 1.3 },
  robot:       { label: 'Robot',         url: null },
  custom:      { label: 'Vlastný model', url: null, yaw: Math.PI / 2, height: 1.3 },
};

/* Načítaj custom skin config z localStorage (yaw + height) */
(function _initCustomSkin() {
  try {
    const c = localStorage.getItem('karel_custom_skin');
    if (c) { const p = JSON.parse(c); Object.assign(KAREL_SKINS.custom, p); }
  } catch (e) { /* ignore */ }
})();
const DEFAULT_SKIN = 'grogu_small';

function _currentSkinId() {
  const s = (typeof localStorage !== 'undefined') && localStorage.getItem('karel_skin');
  return (s && KAREL_SKINS[s]) ? s : DEFAULT_SKIN;
}

/* Predvolené vizuálne nastavenia sveta (farby/textúry/viditeľnosť).
 * brick/big_brick/mark nemajú 'visible' — sú vždy viditeľné. */
const VISUAL_DEFAULTS = {
  wall:      { visible: true, mode: 'color', color: '#dddd00', textureUrl: null },
  floor:     { visible: true, mode: 'color', color: '#0000bb', textureUrl: null },
  grid:      { visible: true, mode: 'color', color: '#3344dd', textureUrl: null },
  sky:       { visible: true, mode: 'color', color: '#060610', textureUrl: null },
  brick:     {                mode: 'color', color: '#44cc22', textureUrl: null },
  big_brick: {                mode: 'color', color: '#993311', textureUrl: null },
  mark:      {                mode: 'color', color: '#ffff44', textureUrl: null },
};

function _loadVisualSettings() {
  try {
    const s = (typeof localStorage !== 'undefined') && localStorage.getItem('karel_visual');
    if (s) {
      const saved = JSON.parse(s);
      // hlboké zlúčenie — nezmazať kľúče čo nie sú v localStorage
      const result = JSON.parse(JSON.stringify(VISUAL_DEFAULTS));
      Object.keys(result).forEach(k => { if (saved[k]) Object.assign(result[k], saved[k]); });
      return result;
    }
  } catch (e) { /* ignore */ }
  return JSON.parse(JSON.stringify(VISUAL_DEFAULTS));
}

function _saveVisualSettings(vs) {
  try {
    localStorage.setItem('karel_visual', JSON.stringify(vs));
  } catch (e) {
    // Quota prekročená — ulož bez textúr (farby zostanú)
    try {
      const safe = JSON.parse(JSON.stringify(vs));
      Object.values(safe).forEach(v => { if (v.textureUrl) v.textureUrl = null; });
      localStorage.setItem('karel_visual', JSON.stringify(safe));
    } catch (e2) { /* ignore */ }
  }
}

class KarelRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(window.devicePixelRatio || 1);
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x060610);

    this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 500);
    this.controls = new THREE.OrbitControls(this.camera, canvas);
    this.controls.enablePan = false;
    this.controls.maxPolarAngle = Math.PI / 2 - 0.02;
    this.controls.minDistance = 3;
    this.controls.maxDistance = 120;

    // svetlá
    const amb = new THREE.AmbientLight(0xffffff, 0.55);
    const sun = new THREE.DirectionalLight(0xffffff, 0.75);
    sun.position.set(8, 14, 6);
    this.scene.add(amb, sun);

    this._static = new THREE.Group();   // podlaha, mriežka, okraje (per-world)
    this._dynamic = new THREE.Group();  // tehly, značky, steny
    this.scene.add(this._static, this._dynamic);

    // Materiály udržiavané ako polia — applyVisualSettings ich mení za behu
    this._floorMat = new THREE.MeshBasicMaterial({ color: 0x0000bb });
    this._gridMat  = new THREE.LineBasicMaterial({ color: 0x3344dd });
    this._mats = {
      brick: new THREE.MeshLambertMaterial({ color: 0x44cc22 }),
      big:   new THREE.MeshLambertMaterial({ color: 0x993311 }),
      mark:  new THREE.MeshBasicMaterial({ color: 0xffff44 }),
      wall:  new THREE.MeshLambertMaterial({ color: 0xdddd00 }),
    };
    this._boxGeo  = new THREE.BoxGeometry(0.92, BRICK_H, 0.92);
    this._bigGeo  = new THREE.BoxGeometry(0.96, BIG_H, 0.96);
    this._markGeo = new THREE.CircleGeometry(0.32, 24);

    // Referencie na statické objekty (pre toggleovanie viditeľnosti)
    this._floorMesh = null;
    this._gridLines = null;
    this._outerWallGroup = null;

    this._size = null;
    this._camInit = false;

    this._karel = this._makeKarel();
    this.scene.add(this._karel);
    this._skin = _currentSkinId();
    this._applySkin(this._skin);

    // Vizuálne nastavenia z localStorage — aplikujú sa v _buildStatic
    this._vis = _loadVisualSettings();

    window.addEventListener('resize', () => this._resize());
    this._resize();
    this._animate();
  }

  _resize() {
    const el = this.canvas.parentElement;
    if (!el) return;
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  // Verejné API — zavolaj po zmene veľkosti kontajnera (napr. size buttony)
  resize() { this._resize(); }

  _animate() {
    requestAnimationFrame(() => this._animate());
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  /* Karel: béžová humanoidná postavička — port Python karel_faces().
   * Lokálne osi: +X = dopredu (čelo), +Y = hore, +Z = doprava.
   * Python box(fx0,ry0,z0,fx1,ry1,z1) → Three (fx, z, ry). */
  _makeKarel() {
    const g = new THREE.Group();
    const boxFig = new THREE.Group();   // kvádrová postavička v podskupine (vymeniteľná za model)
    g.add(boxFig);
    g._boxFig = boxFig;
    const tan      = new THREE.MeshLambertMaterial({ color: 0xc8a870 });
    const tanLight = new THREE.MeshLambertMaterial({ color: 0xd8b880 });
    const box = (fx0, ry0, z0, fx1, ry1, z1, mat) => {
      const m = new THREE.Mesh(
        new THREE.BoxGeometry(fx1 - fx0, z1 - z0, ry1 - ry0), mat || tan);
      m.position.set((fx0 + fx1) / 2, (z0 + z1) / 2, (ry0 + ry1) / 2);
      boxFig.add(m);
    };
    box(-0.12, -0.17, 0,    0.12, -0.03, 0.38);
    box(-0.12,  0.03, 0,    0.12,  0.17, 0.38);
    box(-0.16, -0.20, 0.38, 0.16,  0.20, 0.86, tanLight);
    box(-0.10, -0.25, 0.64, 0.10, -0.20, 0.82);
    box(-0.10,  0.20, 0.64, 0.10,  0.25, 0.82);
    box(-0.14, -0.16, 0.86, 0.14,  0.16, 1.26, tanLight);
    const white = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const pup   = new THREE.MeshBasicMaterial({ color: 0x003300 });
    [-0.08, 0.08].forEach(ry => {
      const e = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.08, 0.08), white);
      e.position.set(0.15, 1.10, ry); boxFig.add(e);
      const p = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.04, 0.04), pup);
      p.position.set(0.16, 1.10, ry); boxFig.add(p);
    });
    return g;
  }

  /* Prepne vzhľad Karla za behu (z nastavení). Uloží voľbu a prekreslí. */
  setSkin(id) {
    if (!KAREL_SKINS[id]) return;
    this._skin = id;
    try { localStorage.setItem('karel_skin', id); } catch (e) { /* ignore */ }
    this._applySkin(id);
  }

  /* Aplikuje skin: 'robot' = kvádre; inak načíta GLB model. Pri chybe → robot. */
  _applySkin(id) {
    const skin = KAREL_SKINS[id] || KAREL_SKINS[DEFAULT_SKIN];
    if (this._modelGroup) { this._karel.remove(this._modelGroup); this._modelGroup = null; }
    this._modelToken = (this._modelToken || 0) + 1;
    const token = this._modelToken;
    if (!skin.url || typeof THREE.GLTFLoader !== 'function') {
      if (this._karel._boxFig) this._karel._boxFig.visible = true;
      return;
    }
    new THREE.GLTFLoader().load(skin.url, (gltf) => {
      if (token !== this._modelToken) return;
      const model = gltf.scene || (gltf.scenes && gltf.scenes[0]);
      if (!model) return;
      const bbox = new THREE.Box3().setFromObject(model);
      const size = bbox.getSize(new THREE.Vector3());
      const center = bbox.getCenter(new THREE.Vector3());
      if (!(size.y > 0)) return;
      let scale = (skin.height || 1.25) / size.y;
      const horiz = Math.max(size.x, size.z) * scale;
      if (horiz > 0.9) scale *= 0.9 / horiz;
      model.scale.setScalar(scale);
      model.position.set(-center.x * scale, -bbox.min.y * scale, -center.z * scale);
      const wrap = new THREE.Group();
      wrap.rotation.y = skin.yaw || 0;
      wrap.add(model);
      if (this._karel._boxFig) this._karel._boxFig.visible = false;
      this._modelGroup = wrap;
      this._karel.add(wrap);
      if (this._lastState) this.render(this._lastState);
    }, undefined, () => {
      if (token !== this._modelToken) return;
      if (this._karel._boxFig) this._karel._boxFig.visible = true;
    });
  }

  /* Mapovanie core→Three (stred políčka) */
  _px(x) { return x + 0.5; }
  _pz(y) { return -(y + 0.5); }

  /* Aplikuje farbu alebo textúru na MeshLambertMaterial / MeshBasicMaterial.
   * 'grid' používa LineBasicMaterial — podporuje iba farbu. */
  _applyMat(mat, vs) {
    if (!mat || !vs) return;
    if (vs.mode === 'texture' && vs.textureUrl) {
      new THREE.TextureLoader().load(vs.textureUrl, (tex) => {
        tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
        mat.map = tex; mat.color.set(0xffffff); mat.needsUpdate = true;
      }, undefined, () => {
        // chyba → použij farbu
        mat.map = null; mat.color.set(vs.color || '#ffffff'); mat.needsUpdate = true;
      });
    } else {
      mat.map = null;
      mat.color.set(vs.color || '#ffffff');
      mat.needsUpdate = true;
    }
  }

  /* Aplikuje vizuálne nastavenia na renderer (farby, textúry, viditeľnosť).
   * Volá sa z nastavení aplikácie. Uloží aj do localStorage. */
  applyVisualSettings(vs) {
    this._vis = vs;
    _saveVisualSettings(vs);

    // Pozadie (sky)
    if (vs.sky && vs.sky.mode === 'texture' && vs.sky.textureUrl) {
      new THREE.TextureLoader().load(vs.sky.textureUrl, (tex) => {
        this.scene.background = tex;
      }, undefined, () => {
        this.scene.background = new THREE.Color(vs.sky.color || '#060610');
      });
    } else {
      this.scene.background = new THREE.Color((vs.sky && vs.sky.color) || '#060610');
    }

    // Podlaha
    if (this._floorMesh) {
      this._floorMesh.visible = vs.floor ? vs.floor.visible !== false : true;
      this._applyMat(this._floorMat, vs.floor);
    }

    // Mriežka
    if (this._gridLines) {
      this._gridLines.visible = vs.grid ? vs.grid.visible !== false : true;
      if (vs.grid && vs.grid.mode !== 'texture') {
        this._gridMat.color.set(vs.grid.color || '#3344dd');
        this._gridMat.needsUpdate = true;
      }
    }

    // Vonkajšie ohraničovacie steny
    if (this._outerWallGroup) {
      this._outerWallGroup.visible = vs.wall ? vs.wall.visible !== false : true;
    }

    // Murik (materiál zdieľaný s internými stenami aj vonkajšími)
    this._applyMat(this._mats.wall, vs.wall);

    // Tehly / kvader / značka
    this._applyMat(this._mats.brick, vs.brick);
    this._applyMat(this._mats.big, vs.big_brick);
    this._applyMat(this._mats.mark, vs.mark);
  }

  /* Statická časť: podlaha + mriežka + vonkajšie ohraničenie.
   * Referencie na objekty sa ukladajú pre applyVisualSettings. */
  _buildStatic(w, h) {
    this._static.clear();

    this._floorMesh = new THREE.Mesh(new THREE.PlaneGeometry(w, h), this._floorMat);
    this._floorMesh.rotation.x = -Math.PI / 2;
    this._floorMesh.position.set(w / 2, -0.005, -h / 2);
    this._static.add(this._floorMesh);

    const pts = [];
    for (let x = 0; x <= w; x++) pts.push(x, 0, 0, x, 0, -h);
    for (let y = 0; y <= h; y++) pts.push(0, 0, -y, w, 0, -y);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    this._gridLines = new THREE.LineSegments(geo, this._gridMat);
    this._static.add(this._gridLines);

    // Vonkajšie ohraničovacie steny — vlastná skupina pre toggle viditeľnosti
    this._outerWallGroup = new THREE.Group();
    const wallH = 0.5, t = 0.08;
    const mk = (sx, sz, px, pz) => {
      const m = new THREE.Mesh(new THREE.BoxGeometry(sx, wallH, sz), this._mats.wall);
      m.position.set(px, wallH / 2, pz);
      this._outerWallGroup.add(m);
    };
    mk(w + 2 * t, t, w / 2, t / 2);
    mk(w + 2 * t, t, w / 2, -h - t / 2);
    mk(t, h, -t / 2, -h / 2);
    mk(t, h, w + t / 2, -h / 2);
    this._static.add(this._outerWallGroup);

    this.controls.target.set(w / 2, 0, -h / 2);

    // Aplikuj uložené vizuálne nastavenia na nový statický obsah
    this.applyVisualSettings(this._vis);
  }

  /* Kamera zo settings.camera (az/el/dist — sférické okolo stredu sveta) */
  setCamera(cam, locked) {
    const t = this.controls.target;
    const az = -cam.az, el = cam.el, d = cam.dist;
    this.camera.position.set(
      t.x + d * Math.cos(el) * Math.cos(az),
      t.y + d * Math.sin(el),
      t.z + d * Math.cos(el) * Math.sin(az));
    this.camera.lookAt(t);
    this.controls.enableRotate = !locked;
    this.controls.enableZoom = !locked;
    this.controls.update();
  }

  /* Aktuálny pohľad kamery (az/el/dist) — inverzia setCamera, pre uloženie do sveta */
  getCamera() {
    const t = this.controls.target, p = this.camera.position;
    const dx = p.x - t.x, dy = p.y - t.y, dz = p.z - t.z;
    const d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 16;
    const el = Math.asin(Math.max(-1, Math.min(1, dy / d)));
    const az = -Math.atan2(dz, dx);
    return { az, el, dist: d };
  }

  /* Preset pohľadu (tlačidlá Def/Pred/Vrch/Bok) */
  setViewPreset(azDeg, elDeg) {
    const t = this.controls.target;
    const d = this.camera.position.distanceTo(t) || (Math.max(this._size[0], this._size[1]) * 2);
    this.setCamera({ az: azDeg * Math.PI / 180, el: elDeg * Math.PI / 180, dist: d },
                   !this.controls.enableRotate);
  }

  /* Hlavný vstup: vykresli state JSON */
  render(state) {
    this._lastState = state;
    const w = state.width, h = state.height;
    if (!this._size || this._size[0] !== w || this._size[1] !== h) {
      this._size = [w, h];
      this._buildStatic(w, h);
      this._camInit = false;
    }
    if (!this._camInit) {
      const cam = (state.settings && state.settings.camera) || { az: 3.93, el: 0.49, dist: Math.max(w, h) * 2 };
      this.setCamera(cam, !!(state.settings && state.settings.camera_locked));
      this._camInit = true;
    }

    this._dynamic.clear();

    // výška kvadrov pre stohovanie malých tehiel
    const bigAt = {};
    (state.big_bricks || []).forEach(([x, y]) => {
      bigAt[x + ',' + y] = 1;
      const m = new THREE.Mesh(this._bigGeo, this._mats.big);
      m.position.set(this._px(x), BIG_H / 2, this._pz(y));
      this._dynamic.add(m);
    });

    (state.bricks || []).forEach(([x, y, n]) => {
      const base = (bigAt[x + ',' + y] ? BIG_H : 0);
      for (let i = 0; i < n; i++) {
        const m = new THREE.Mesh(this._boxGeo, this._mats.brick);
        m.position.set(this._px(x), base + BRICK_H * (i + 0.5), this._pz(y));
        this._dynamic.add(m);
      }
    });

    const heightAt = {};
    (state.big_bricks || []).forEach(([x, y]) => { heightAt[x + ',' + y] = BIG_H; });
    (state.bricks || []).forEach(([x, y, n]) => { heightAt[x + ',' + y] = (heightAt[x + ',' + y] || 0) + n * BRICK_H; });

    (state.marks || []).forEach(([x, y]) => {
      const m = new THREE.Mesh(this._markGeo, this._mats.mark);
      m.rotation.x = -Math.PI / 2;
      m.position.set(this._px(x), (heightAt[x + ',' + y] || 0) + 0.02, this._pz(y));
      this._dynamic.add(m);
    });

    const wallH = 1.2, t = 0.08;
    const wallVisible = !this._vis || this._vis.wall === undefined || this._vis.wall.visible !== false;
    (state.walls || []).forEach(([x, y, side]) => {
      if ((side === 'S' && y === 0) || (side === 'N' && y === h - 1) ||
          (side === 'W' && x === 0) || (side === 'E' && x === w - 1)) return;
      let sx = 1 + t, sz = t, px = this._px(x), pz = this._pz(y);
      if (side === 'N') pz -= 0.5;
      else if (side === 'S') pz += 0.5;
      else { sx = t; sz = 1 + t; px += (side === 'E' ? 0.5 : -0.5); }
      const m = new THREE.Mesh(new THREE.BoxGeometry(sx, wallH, sz), this._mats.wall);
      m.position.set(px, wallH / 2, pz);
      m.visible = wallVisible;
      this._dynamic.add(m);
    });

    // Karel — na vrchu stohu, otočený podľa dir
    const k = state.karel;
    let base = 0;
    (state.big_bricks || []).forEach(([x, y]) => { if (x === k.x && y === k.y) base += BIG_H; });
    (state.bricks || []).forEach(([x, y, n]) => { if (x === k.x && y === k.y) base += n * BRICK_H; });
    this._karel.position.set(this._px(k.x), base, this._pz(k.y));
    // čelo postavy = +X lokálne; E(+worldX=+threeX):0  N(+worldY=−threeZ):π/2  W:π  S(+threeZ):−π/2
    const rot = { E: 0, N: Math.PI / 2, W: Math.PI, S: -Math.PI / 2 }[k.dir] || 0;
    this._karel.rotation.y = rot;
  }

  /* Načíta vlastný GLB model (admin). dataUrl = data: URL zo FileReadera.
   * Okamžite sa prepne na custom skin a aplikuje yaw/height. */
  setCustomSkin(dataUrl, yaw, height) {
    const s = KAREL_SKINS.custom;
    s.url = dataUrl;
    if (yaw !== undefined) s.yaw = yaw;
    if (height !== undefined) s.height = height;
    this._saveCustomConfig();
    this.setSkin('custom');
  }

  /* Živá úprava yaw vlastného modelu (bez reloadu GLB — iba rotácia wrap). */
  adjustCustomYaw(rad) {
    KAREL_SKINS.custom.yaw = rad;
    this._saveCustomConfig();
    if (this._skin === 'custom' && this._modelGroup) {
      this._modelGroup.rotation.y = rad;
    }
  }

  /* Živá úprava výšky vlastného modelu (reload GLB z cache — rýchle). */
  adjustCustomHeight(height) {
    KAREL_SKINS.custom.height = height;
    this._saveCustomConfig();
    if (this._skin === 'custom') this._applySkin('custom');
  }

  /* Vráti aktuálnu konfiguráciu custom skinu. */
  getCustomSkinConfig() {
    const s = KAREL_SKINS.custom;
    return { yaw: s.yaw, height: s.height, hasModel: !!s.url };
  }

  _saveCustomConfig() {
    try {
      const s = KAREL_SKINS.custom;
      localStorage.setItem('karel_custom_skin', JSON.stringify({ yaw: s.yaw, height: s.height }));
    } catch (e) { /* ignore */ }
  }

  /* Vráti zoznam skinov pre nastavenia (label + id).
   * Custom skin sa skryje kým nie je načítaný model. */
  static skinList(includeCustom) {
    return Object.entries(KAREL_SKINS)
      .filter(([id, s]) => id !== 'custom' || includeCustom)
      .map(([id, s]) => ({ id, label: s.label }));
  }

  /* Vráti aktuálne vizuálne nastavenia (kópia) */
  getVisualSettings() {
    return JSON.parse(JSON.stringify(this._vis));
  }
}
