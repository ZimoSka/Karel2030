/* Karel 2030 — Three.js renderer stavu sveta (state JSON §4).
 * Súradnice: x=0 vľavo, y=0 dole (core) → Three: X = x, Z = -y, Y = výška.
 * Kvader = 5 jednotiek výšky, malé tehly sa stohujú NA kvadri.
 */
'use strict';

const BRICK_H = 0.30;            // výška malej tehly (world unit = 1 políčko)
const BIG_H = 5 * BRICK_H;       // kvader = 5 malých

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

    this._mats = {
      brick: new THREE.MeshLambertMaterial({ color: 0x44cc66 }),
      big:   new THREE.MeshLambertMaterial({ color: 0x8b5a2b }),
      mark:  new THREE.MeshBasicMaterial({ color: 0xffdd44 }),
      wall:  new THREE.MeshLambertMaterial({ color: 0xddaa22 }),
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

  /* Karel: valec (telo) + kužeľ (smer) — jednoduchá postavička */
  _makeKarel() {
    const g = new THREE.Group();
    const body = new THREE.Mesh(
      new THREE.CylinderGeometry(0.28, 0.34, 0.7, 20),
      new THREE.MeshLambertMaterial({ color: 0x44ff88 }));
    body.position.y = 0.35;
    const head = new THREE.Mesh(
      new THREE.SphereGeometry(0.2, 16, 12),
      new THREE.MeshLambertMaterial({ color: 0x77ffaa }));
    head.position.y = 0.82;
    const nose = new THREE.Mesh(
      new THREE.ConeGeometry(0.13, 0.36, 14),
      new THREE.MeshLambertMaterial({ color: 0xff5566 }));
    nose.rotation.x = Math.PI / 2;          // kužeľ smeruje po +Z lokálne
    nose.position.set(0, 0.55, 0.38);
    g.add(body, head, nose);
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
      new THREE.MeshLambertMaterial({ color: 0x101038 }));
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(w / 2, -0.005, -h / 2);
    this._static.add(floor);

    // mriežka — modré čiary
    const pts = [];
    for (let x = 0; x <= w; x++) pts.push(x, 0, 0, x, 0, -h);
    for (let y = 0; y <= h; y++) pts.push(0, 0, -y, w, 0, -y);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    this._static.add(new THREE.LineSegments(geo,
      new THREE.LineBasicMaterial({ color: 0x3355cc })));

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
    const az = cam.az, el = cam.el, d = cam.dist;
    this.camera.position.set(
      t.x + d * Math.cos(el) * Math.cos(az),
      t.y + d * Math.sin(el),
      t.z + d * Math.cos(el) * Math.sin(az));
    this.camera.lookAt(t);
    this.controls.enableRotate = !locked;
    this.controls.enableZoom = !locked;
    this.controls.update();
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

    // značky — žlté krúžky na podlahe
    (state.marks || []).forEach(([x, y]) => {
      const m = new THREE.Mesh(this._markGeo, this._mats.mark);
      m.rotation.x = -Math.PI / 2;
      m.position.set(this._px(x), 0.01, this._pz(y));
      this._dynamic.add(m);
    });

    // interné steny — [x, y, side]; okraje už kreslí _buildStatic, ale
    // duplicitné okrajové steny zo state neprekážajú (rovnaké miesto)
    const wallH = 1.0, t = 0.08;
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
    // dir: N=+y → -Z; postavička má "nos" po +Z pri rotácii 0… otoč:
    const rot = { S: 0, E: Math.PI / 2, N: Math.PI, W: -Math.PI / 2 }[k.dir] || 0;
    this._karel.rotation.y = rot;
  }
}
