"""Add vis_lbl_* translation keys to all language .ini files."""
import re, os

BASE = os.path.join(os.path.dirname(__file__), '..', 'lang')

KEYS = {
    'sk': {'vis_lbl_wall': 'Múrik', 'vis_lbl_floor': 'Podlaha', 'vis_lbl_grid': 'Grid podlahy',
           'vis_lbl_sky': 'Okolie', 'vis_lbl_brick': 'Tehla', 'vis_lbl_big_brick': 'Kvader', 'vis_lbl_mark': 'Značka'},
    'en': {'vis_lbl_wall': 'Wall', 'vis_lbl_floor': 'Floor', 'vis_lbl_grid': 'Floor grid',
           'vis_lbl_sky': 'Sky', 'vis_lbl_brick': 'Brick', 'vis_lbl_big_brick': 'Big brick', 'vis_lbl_mark': 'Mark'},
    'de': {'vis_lbl_wall': 'Mauer', 'vis_lbl_floor': 'Boden', 'vis_lbl_grid': 'Bodengitter',
           'vis_lbl_sky': 'Umgebung', 'vis_lbl_brick': 'Ziegel', 'vis_lbl_big_brick': 'Großer Ziegel', 'vis_lbl_mark': 'Markierung'},
    'fr': {'vis_lbl_wall': 'Mur', 'vis_lbl_floor': 'Sol', 'vis_lbl_grid': 'Grille au sol',
           'vis_lbl_sky': 'Environnement', 'vis_lbl_brick': 'Brique', 'vis_lbl_big_brick': 'Grande brique', 'vis_lbl_mark': 'Marqueur'},
    'it': {'vis_lbl_wall': 'Muro', 'vis_lbl_floor': 'Pavimento', 'vis_lbl_grid': 'Griglia pavimento',
           'vis_lbl_sky': 'Ambiente', 'vis_lbl_brick': 'Mattone', 'vis_lbl_big_brick': 'Mattone grande', 'vis_lbl_mark': 'Segno'},
    'es': {'vis_lbl_wall': 'Muro', 'vis_lbl_floor': 'Suelo', 'vis_lbl_grid': 'Cuadrícula del suelo',
           'vis_lbl_sky': 'Entorno', 'vis_lbl_brick': 'Ladrillo', 'vis_lbl_big_brick': 'Ladrillo grande', 'vis_lbl_mark': 'Marca'},
}

for lang, keys in KEYS.items():
    path = os.path.join(BASE, f'{lang}.ini')
    with open(path, encoding='utf-8') as f:
        content = f.read()
    sec_match = re.search(r'\[app_settings\]', content)
    next_sec = re.search(r'\n\[', content[sec_match.end():])
    insert_pos = (sec_match.end() + next_sec.start()) if next_sec else len(content)
    new_lines = []
    for k, v in keys.items():
        if not re.search(r'^' + re.escape(k) + r'\s*=', content, re.MULTILINE):
            new_lines.append(f'{k:<20}= {v}')
    if new_lines:
        content = content[:insert_pos] + '\n' + '\n'.join(new_lines) + '\n' + content[insert_pos:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'{lang}: added {len(new_lines)} keys')
