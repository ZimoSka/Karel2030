"""Add all remaining hardcoded string keys found during i18n audit."""
import re, os

BASE = os.path.join(os.path.dirname(__file__), '..', 'lang')

KEYS = {
    'sk': {
        'nav': {
            'steps': 'Kroky',
            'turns': 'Otočenia',
        },
        'status': {
            'line': 'Riadok',
        },
        'share': {
            'title':            'Zdieľanie žiakom',
            'preparing':        'Pripravujem zdieľanie…',
            'lbl_base_addr':    'Adresa pre žiakov',
            'tt_base_addr':     'Verejná IP/hostname a port, na ktorom je Karel dostupný pre žiakov',
            'intro':            'Žiaci tohto sveta — každý má vlastný trvalý link. Pridaj žiaka, sleduj pokrok, alebo zmaž.',
            'placeholder_name': 'Meno žiaka',
            'btn_add_student':  'Pridať žiaka',
            'no_students':      'Zatiaľ žiadni žiaci.',
            'status_solved':    'vyriešil',
            'status_not_started': 'nezačal',
            'tt_view_prog':     'Zobraziť program žiaka',
            'tt_delete_student':'Zmazať žiaka',
            'tt_copy_link':     'Kopíruj link',
            'confirm_delete':   'Zmazať žiaka „{name}" a jeho prácu?',
            'student_label':    'žiak',
            'prog_title':       'Program',
            'btn_back':         'Späť',
            'btn_load_editor':  'Načítať do editora',
        },
        'app_settings': {
            'glb_status_loaded': '(načítaný)',
            'glb_note_reload':  'Vlastný model sa reloaduje každú reláciu — uložte GLB súbor na rovnaké miesto.',
        },
        'world_settings': {
            'lbl_karel_x': 'Karel X:',
            'lbl_karel_y': 'Karel Y:',
        },
        'goal_condition': {
            'disp_cell':        'bunka',
            'disp_sign':        'značka pod Karlom',
            'disp_brick_ahead': 'tehla pred Karlom',
            'disp_wall_ahead':  'stena pred Karlom',
            'disp_snapshot':    'snímok miestnosti',
        },
    },
    'en': {
        'nav': {
            'steps': 'Steps',
            'turns': 'Turns',
        },
        'status': {
            'line': 'Line',
        },
        'share': {
            'title':            'Share with students',
            'preparing':        'Preparing sharing…',
            'lbl_base_addr':    'Student address',
            'tt_base_addr':     'Public IP/hostname and port where Karel is accessible to students',
            'intro':            'Students of this world — each has their own permanent link. Add a student, track progress, or delete.',
            'placeholder_name': 'Student name',
            'btn_add_student':  'Add student',
            'no_students':      'No students yet.',
            'status_solved':    'solved',
            'status_not_started': 'not started',
            'tt_view_prog':     'View student program',
            'tt_delete_student':'Delete student',
            'tt_copy_link':     'Copy link',
            'confirm_delete':   'Delete student "{name}" and their work?',
            'student_label':    'student',
            'prog_title':       'Program',
            'btn_back':         'Back',
            'btn_load_editor':  'Load into editor',
        },
        'app_settings': {
            'glb_status_loaded': '(loaded)',
            'glb_note_reload':  'Custom model reloads every session — keep the GLB file in the same location.',
        },
        'world_settings': {
            'lbl_karel_x': 'Karel X:',
            'lbl_karel_y': 'Karel Y:',
        },
        'goal_condition': {
            'disp_cell':        'cell',
            'disp_sign':        'mark under Karel',
            'disp_brick_ahead': 'brick ahead of Karel',
            'disp_wall_ahead':  'wall ahead of Karel',
            'disp_snapshot':    'room snapshot',
        },
    },
    'de': {
        'nav': {
            'steps': 'Schritte',
            'turns': 'Drehungen',
        },
        'status': {
            'line': 'Zeile',
        },
        'share': {
            'title':            'Mit Schülern teilen',
            'preparing':        'Teilen wird vorbereitet…',
            'lbl_base_addr':    'Schüleradresse',
            'tt_base_addr':     'Öffentliche IP/Hostname und Port, unter dem Karel für Schüler erreichbar ist',
            'intro':            'Schüler dieser Welt — jeder hat seinen eigenen dauerhaften Link. Füge Schüler hinzu, verfolge den Fortschritt oder lösche.',
            'placeholder_name': 'Schülername',
            'btn_add_student':  'Schüler hinzufügen',
            'no_students':      'Noch keine Schüler.',
            'status_solved':    'gelöst',
            'status_not_started': 'nicht begonnen',
            'tt_view_prog':     'Schülerprogramm anzeigen',
            'tt_delete_student':'Schüler löschen',
            'tt_copy_link':     'Link kopieren',
            'confirm_delete':   'Schüler „{name}" und seine Arbeit löschen?',
            'student_label':    'Schüler',
            'prog_title':       'Programm',
            'btn_back':         'Zurück',
            'btn_load_editor':  'In Editor laden',
        },
        'app_settings': {
            'glb_status_loaded': '(geladen)',
            'glb_note_reload':  'Das benutzerdefinierte Modell wird jede Sitzung neu geladen — bewahren Sie die GLB-Datei am gleichen Ort auf.',
        },
        'world_settings': {
            'lbl_karel_x': 'Karel X:',
            'lbl_karel_y': 'Karel Y:',
        },
        'goal_condition': {
            'disp_cell':        'Zelle',
            'disp_sign':        'Markierung unter Karel',
            'disp_brick_ahead': 'Ziegel vor Karel',
            'disp_wall_ahead':  'Wand vor Karel',
            'disp_snapshot':    'Raumschnappschuss',
        },
    },
    'fr': {
        'nav': {
            'steps': 'Pas',
            'turns': 'Tours',
        },
        'status': {
            'line': 'Ligne',
        },
        'share': {
            'title':            'Partager avec les élèves',
            'preparing':        'Préparation du partage…',
            'lbl_base_addr':    'Adresse élèves',
            'tt_base_addr':     'IP/nom d\'hôte public et port où Karel est accessible aux élèves',
            'intro':            'Élèves de ce monde — chacun a son propre lien permanent. Ajoutez un élève, suivez la progression ou supprimez.',
            'placeholder_name': 'Nom de l\'élève',
            'btn_add_student':  'Ajouter un élève',
            'no_students':      'Pas encore d\'élèves.',
            'status_solved':    'résolu',
            'status_not_started': 'pas commencé',
            'tt_view_prog':     'Voir le programme de l\'élève',
            'tt_delete_student':'Supprimer l\'élève',
            'tt_copy_link':     'Copier le lien',
            'confirm_delete':   'Supprimer l\'élève « {name} » et son travail ?',
            'student_label':    'élève',
            'prog_title':       'Programme',
            'btn_back':         'Retour',
            'btn_load_editor':  'Charger dans l\'éditeur',
        },
        'app_settings': {
            'glb_status_loaded': '(chargé)',
            'glb_note_reload':  'Le modèle personnalisé se recharge à chaque session — gardez le fichier GLB au même endroit.',
        },
        'world_settings': {
            'lbl_karel_x': 'Karel X :',
            'lbl_karel_y': 'Karel Y :',
        },
        'goal_condition': {
            'disp_cell':        'cellule',
            'disp_sign':        'marqueur sous Karel',
            'disp_brick_ahead': 'brique devant Karel',
            'disp_wall_ahead':  'mur devant Karel',
            'disp_snapshot':    'instantané de la salle',
        },
    },
    'it': {
        'nav': {
            'steps': 'Passi',
            'turns': 'Rotazioni',
        },
        'status': {
            'line': 'Riga',
        },
        'share': {
            'title':            'Condividi con gli studenti',
            'preparing':        'Preparazione condivisione…',
            'lbl_base_addr':    'Indirizzo studenti',
            'tt_base_addr':     'IP/hostname pubblico e porta dove Karel è accessibile agli studenti',
            'intro':            'Studenti di questo mondo — ognuno ha il proprio link permanente. Aggiungi uno studente, monitora i progressi o elimina.',
            'placeholder_name': 'Nome studente',
            'btn_add_student':  'Aggiungi studente',
            'no_students':      'Nessuno studente ancora.',
            'status_solved':    'risolto',
            'status_not_started': 'non iniziato',
            'tt_view_prog':     'Visualizza programma studente',
            'tt_delete_student':'Elimina studente',
            'tt_copy_link':     'Copia link',
            'confirm_delete':   'Eliminare lo studente „{name}" e il suo lavoro?',
            'student_label':    'studente',
            'prog_title':       'Programma',
            'btn_back':         'Indietro',
            'btn_load_editor':  'Carica nell\'editor',
        },
        'app_settings': {
            'glb_status_loaded': '(caricato)',
            'glb_note_reload':  'Il modello personalizzato viene ricaricato ogni sessione — mantenere il file GLB nella stessa posizione.',
        },
        'world_settings': {
            'lbl_karel_x': 'Karel X:',
            'lbl_karel_y': 'Karel Y:',
        },
        'goal_condition': {
            'disp_cell':        'cella',
            'disp_sign':        'segno sotto Karel',
            'disp_brick_ahead': 'mattone davanti a Karel',
            'disp_wall_ahead':  'muro davanti a Karel',
            'disp_snapshot':    'istantanea della stanza',
        },
    },
    'es': {
        'nav': {
            'steps': 'Pasos',
            'turns': 'Giros',
        },
        'status': {
            'line': 'Línea',
        },
        'share': {
            'title':            'Compartir con alumnos',
            'preparing':        'Preparando compartir…',
            'lbl_base_addr':    'Dirección alumnos',
            'tt_base_addr':     'IP/nombre de host público y puerto donde Karel es accesible para los alumnos',
            'intro':            'Alumnos de este mundo — cada uno tiene su propio enlace permanente. Añade un alumno, sigue el progreso o elimina.',
            'placeholder_name': 'Nombre del alumno',
            'btn_add_student':  'Añadir alumno',
            'no_students':      'Aún no hay alumnos.',
            'status_solved':    'resuelto',
            'status_not_started': 'no comenzado',
            'tt_view_prog':     'Ver programa del alumno',
            'tt_delete_student':'Eliminar alumno',
            'tt_copy_link':     'Copiar enlace',
            'confirm_delete':   '¿Eliminar al alumno „{name}" y su trabajo?',
            'student_label':    'alumno',
            'prog_title':       'Programa',
            'btn_back':         'Volver',
            'btn_load_editor':  'Cargar en el editor',
        },
        'app_settings': {
            'glb_status_loaded': '(cargado)',
            'glb_note_reload':  'El modelo personalizado se recarga cada sesión — guarde el archivo GLB en el mismo lugar.',
        },
        'world_settings': {
            'lbl_karel_x': 'Karel X:',
            'lbl_karel_y': 'Karel Y:',
        },
        'goal_condition': {
            'disp_cell':        'celda',
            'disp_sign':        'marca bajo Karel',
            'disp_brick_ahead': 'ladrillo delante de Karel',
            'disp_wall_ahead':  'muro delante de Karel',
            'disp_snapshot':    'instantánea de la sala',
        },
    },
}


def add_keys_to_file(lang, sections):
    path = os.path.join(BASE, f'{lang}.ini')
    with open(path, encoding='utf-8') as f:
        content = f.read()
    total = 0
    for section, keys in sections.items():
        sec_match = re.search(r'\[' + re.escape(section) + r'\]', content)
        if not sec_match:
            new_sec = f'\n[{section}]\n' + '\n'.join(f'{k:<24}= {v}' for k, v in keys.items()) + '\n'
            content = content.rstrip('\n') + '\n' + new_sec
            total += len(keys)
            continue
        next_sec = re.search(r'\n\[', content[sec_match.end():])
        insert_pos = (sec_match.end() + next_sec.start()) if next_sec else len(content)
        new_lines = []
        for k, v in keys.items():
            if not re.search(r'^' + re.escape(k) + r'\s*=', content, re.MULTILINE):
                new_lines.append(f'{k:<24}= {v}')
        if new_lines:
            content = content[:insert_pos] + '\n' + '\n'.join(new_lines) + '\n' + content[insert_pos:]
            total += len(new_lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'{lang}: added {total} keys')


if __name__ == '__main__':
    for lang, sections in KEYS.items():
        add_keys_to_file(lang, dict(sections))
