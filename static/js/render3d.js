/* Karel 2030 — Three.js renderer stavu sveta (state JSON §4).
 * Súradnice: x=0 vľavo, y=0 dole (core) → Three: X = x, Z = -y, Y = výška.
 * Kvader = 5 jednotiek výšky, malé tehly sa stohujú NA kvadri.
 */
'use strict';

const BRICK_H = 0.27;            // výška malej tehly — zhodné s Python desktopom
const BIG_H = 5 * BRICK_H;       // kvader = 5 malých (= 1.35)

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

    this._karel = this._makeKarel();
    this.scene.add(this._karel);

    // farby zhodné s Python paletou (FC)
    this._mats = {
      brick: new THREE.MeshLambertMaterial({ color: 0x44cc22 }),   // FC brick_top
      big:   new THREE.MeshLambertMaterial({ color: 0x993311 }),   // FC bbrick_top (hnedá)
      mark:  new THREE.MeshBasicMaterial({ color: 0xffff44 }),     // FC mark2 (žltá)
      wall:  new THREE.MeshLambertMaterial({ color: 0xdddd00 }),   // FC wall
    };
    this._boxGeo = new THREE.BoxGeometry(0.92, BRICK_H, 0.92);
    this._bigGeo = new THREE.BoxGeometry(0.96, BIG_H, 0.96);
    this._markGeo = new THREE.CircleGeometry(0.32, 24);

    this._size = null;     // [w,h] aktuálneho sveta
    this._camInit = false;

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
    const tan      = new THREE.MeshLambertMaterial({ color: 0xc8a870 });  // SK
    const tanLight = new THREE.MeshLambertMaterial({ color: 0xd8b880 });  // FC2 (čelo)
    const box = (fx0, ry0, z0, fx1, ry1, z1, mat) => {
      const m = new THREE.Mesh(
        new THREE.BoxGeometry(fx1 - fx0, z1 - z0, ry1 - ry0), mat || tan);
      m.position.set((fx0 + fx1) / 2, (z0 + z1) / 2, (ry0 + ry1) / 2);
      g.add(m);
    };
    box(-0.12, -0.17, 0,    0.12, -0.03, 0.38);             // noha L
    box(-0.12,  0.03, 0,    0.12,  0.17, 0.38);             // noha R
    box(-0.16, -0.20, 0.38, 0.16,  0.20, 0.86, tanLight);   // trup
    box(-0.10, -0.25, 0.64, 0.10, -0.20, 0.82);             // rameno L
    box(-0.10,  0.20, 0.64, 0.10,  0.25, 0.82);             // rameno R
    box(-0.14, -0.16, 0.86, 0.14,  0.16, 1.26, tanLight);   // hlava
    // oči — biele s tmavou zrenicou, na čele (+X)
    const white = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const pup   = new THREE.MeshBasicMaterial({ color: 0x003300 });
    [-0.08, 0.08].forEach(ry => {
      const e = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.08, 0.08), white);
      e.position.set(0.15, 1.10, ry); g.add(e);
      const p = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.04, 0.04), pup);
      p.position.set(0.16, 1.10, ry); g.add(p);
    });
    return g;
  }

  /* Mapovanie core→Three (stred políčka) */
  _px(x) { return x + 0.5; }
  _pz(y) { return -(y + 0.5); }

  /* Statická časť: podlaha (modrá mriežka ako desktop) + okrajové steny (žlté) */
  _buildStatic(w, h) {
    this._static.clear();
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(w, h),
      new THREE.MeshBasicMaterial({ color: 0x0000bb }));   // FC floor_a (modrá ako desktop)
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(w / 2, -0.005, -h / 2);
    this._static.add(floor);

    // mriežka — modré čiary (FC grid)
    const pts = [];
    for (let x = 0; x <= w; x++) pts.push(x, 0, 0, x, 0, -h);
    for (let y = 0; y <= h; y++) pts.push(0, 0, -y, w, 0, -y);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    this._static.add(new THREE.LineSegments(geo,
      new THREE.LineBasicMaterial({ color: 0x3344dd })));

    // okrajové steny — nízke žlté pásy okolo celej miestnosti
    const wallH = 0.5, t = 0.08;
    const mk = (sx, sz, px, pz) => {
      const m = new THREE.Mesh(new THREE.BoxGeometry(sx, wallH, sz), this._mats.wall);
      m.position.set(px, wallH / 2, pz);
      this._static.add(m);
    };
    mk(w + 2 * t, t, w / 2, t / 2);            // juh (y=0 → z=0)
    mk(w + 2 * t, t, w / 2, -h - t / 2);       // sever
    mk(t, h, -t / 2, -h / 2);                  // západ
    mk(t, h, w + t / 2, -h / 2);               // východ

    this.controls.target.set(w / 2, 0, -h / 2);
  }

  /* Kamera zo settings.camera (az/el/dist — sférické okolo stredu sveta) */
  setCamera(cam, locked) {
    const t = this.controls.target;
    // worldY → −threeZ (handedness-správne), preto azimut meriame opačne než
    // Python (negácia), aby uložené camera_az z .karxml dalo rovnaký pohľad.
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
    const az = -Math.atan2(dz, dx);   // setCamera používa az_three = -cam.az
    return { az, el, dist: d };
  }

  /* Preset pohľadu (tlačidlá Def/Pred/Vrch/Bok) — uhly v stupňoch,
   * zachová aktuálnu vzdialenosť kamery od cieľa. */
  setViewPreset(azDeg, elDeg) {
    const t = this.controls.target;
    const d = this.camera.position.distanceTo(t) || (Math.max(this._size[0], this._size[1]) * 2);
    this.setCamera({ az: azDeg * Math.PI / 180, el: elDeg * Math.PI / 180, dist: d },
                   !this.controls.enableRotate);
  }

  /* Hlavný vstup: vykresli state JSON */
  render(state) {
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

    // malé tehly — stohované, NA kvadri ak je
    (state.bricks || []).forEach(([x, y, n]) => {
      const base = (bigAt[x + ',' + y] ? BIG_H : 0);
      for (let i = 0; i < n; i++) {
        const m = new THREE.Mesh(this._boxGeo, this._mats.brick);
        m.position.set(this._px(x), base + BRICK_H * (i + 0.5), this._pz(y));
        this._dynamic.add(m);
      }
    });

    // výška stohu na políčku (kvader + malé tehly) — pre umiestnenie značky navrch
    const heightAt = {};
    (state.big_bricks || []).forEach(([x, y]) => { heightAt[x + ',' + y] = BIG_H; });
    (state.bricks || []).forEach(([x, y, n]) => { heightAt[x + ',' + y] = (heightAt[x + ',' + y] || 0) + n * BRICK_H; });

    // značky — žlté krúžky NA vrchu stohu (aby boli vidno aj na tehlách)
    (state.marks || []).forEach(([x, y]) => {
      const m = new THREE.Mesh(this._markGeo, this._mats.mark);
      m.rotation.x = -Math.PI / 2;
      m.position.set(this._px(x), (heightAt[x + ',' + y] || 0) + 0.02, this._pz(y));
      this._dynamic.add(m);
    });

    // interné steny — [x, y, side]; okraje už kreslí _buildStatic, ale
    // duplicitné okrajové steny zo state neprekážajú (rovnaké miesto)
    const wallH = 1.2, t = 0.08;   // Python WALL_H
    (state.walls || []).forEach(([x, y, side]) => {
      // preskoč steny na vonkajšom okraji (kreslí ich _buildStatic)
      if ((side === 'S' && y === 0) || (side === 'N' && y === h - 1) ||
          (side === 'W' && x === 0) || (side === 'E' && x === w - 1)) return;
      let sx = 1 + t, sz = t, px = this._px(x), pz = this._pz(y);
      if (side === 'N') pz -= 0.5;
      else if (side === 'S') pz += 0.5;
      else { sx = t; sz = 1 + t; px += (side === 'E' ? 0.5 : -0.5); }
      const m = new THREE.Mesh(new THREE.BoxGeometry(sx, wallH, sz), this._mats.wall);
      m.position.set(px, wallH / 2, pz);
      this._dynamic.add(m);
    });

    // Karel — na vrchu stohu, otočený podľa dir
    const k = state.karel;
    const kk = k.x + ',' + k.y;
    let base = 0;
    (state.big_bricks || []).forEach(([x, y]) => { if (x === k.x && y === k.y) base += BIG_H; });
    (state.bricks || []).forEach(([x, y, n]) => { if (x === k.x && y === k.y) base += n * BRICK_H; });
    this._karel.position.set(this._px(k.x), base, this._pz(k.y));
    // čelo postavy = +X lokálne; mapovanie worldY→−Z:
    //  E(+worldX=+threeX):0  N(+worldY=−threeZ):π/2  W:π  S(+threeZ):−π/2
    const rot = { E: 0, N: Math.PI / 2, W: Math.PI, S: -Math.PI / 2 }[k.dir] || 0;
    this._karel.rotation.y = rot;
  }
}
