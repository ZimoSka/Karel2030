"""Stiahne vendor knižnice pre Karel 2030 frontend (offline Docker).
Spustenie:  python static/vendor/get_vendor.py
Overí, že stiahnuté súbory sú skutočný JS/CSS (nie HTML error stránka).
"""
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

FILES = {
    "three.min.js":
        "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js",
    "OrbitControls.js":
        "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js",
    "GLTFLoader.js":
        "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js",
    "codemirror.min.js":
        "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js",
    "codemirror.min.css":
        "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css",
    "simple.min.js":
        "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/simple.min.js",
}

MIN_SIZE = {  # sanity: minimálna očakávaná veľkosť v bajtoch
    "three.min.js": 500_000,
    "OrbitControls.js": 10_000,
    "GLTFLoader.js": 30_000,
    "codemirror.min.js": 150_000,
    "codemirror.min.css": 5_000,
    "simple.min.js": 2_000,
}


def main():
    ok = True
    for name, url in FILES.items():
        dest = os.path.join(HERE, name)
        print(f"-> {name} ... ", end="", flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "karel2030-vendor"})
        data = urllib.request.urlopen(req, timeout=60).read()
        head = data[:200].lstrip().lower()
        if head.startswith(b"<!doctype") or head.startswith(b"<html"):
            print("CHYBA: vyzerá ako HTML stránka, nie JS/CSS")
            ok = False
            continue
        if len(data) < MIN_SIZE[name]:
            print(f"CHYBA: podozrivo malý súbor ({len(data)} B)")
            ok = False
            continue
        with open(dest, "wb") as f:
            f.write(data)
        print(f"OK ({len(data)//1024} kB)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
