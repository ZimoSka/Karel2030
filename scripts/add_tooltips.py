"""Add toolbar tooltip and texture button translation keys to all language .ini files."""
import re, os

BASE = os.path.join(os.path.dirname(__file__), '..', 'lang')

KEYS = {
    'sk': {
        'toolbar': {
            'tt_world_open':    'Otvoriť svet zo súboru (.karxml)',
            'tt_world_save':    'Uložiť svet do súboru (.karxml)',
            'tt_world_pub':     'Publikovať / uložiť zdieľaný svet (admin)',
            'tt_world_del':     'Zmazať vybraný publikovaný svet (admin)',
            'tt_share':         'Zdieľať svet žiakom — pridaj žiaka, link a pokrok v jednom okne',
            'tt_admin':         'Admin režim — prihlásenie heslom',
            'tt_app_settings':  'Nastavenia (jazyk, vzhľad Karla)',
            'tt_conn_offline':  'offline',
            'tt_fwd':           'dopredu',
            'tt_left':          'vlavo',
            'tt_right':         'vpravo',
            'tt_back':          'dozadu',
            'tt_prog_open':     'Otvoriť program zo súboru',
            'tt_prog_save':     'Uložiť program do súboru',
        },
        'app_settings': {
            'tt_tex_choose':    'Vybrať textúru zo súboru',
            'tt_tex_remove':    'Odstrániť textúru',
        },
    },
    'en': {
        'toolbar': {
            'tt_world_open':    'Open world from file (.karxml)',
            'tt_world_save':    'Save world to file (.karxml)',
            'tt_world_pub':     'Publish / save shared world (admin)',
            'tt_world_del':     'Delete selected published world (admin)',
            'tt_share':         'Share world with students — add student, link and progress in one window',
            'tt_admin':         'Admin mode — login with password',
            'tt_app_settings':  'Settings (language, Karel appearance)',
            'tt_conn_offline':  'offline',
            'tt_fwd':           'forward',
            'tt_left':          'turn left',
            'tt_right':         'turn right',
            'tt_back':          'back',
            'tt_prog_open':     'Open program from file',
            'tt_prog_save':     'Save program to file',
        },
        'app_settings': {
            'tt_tex_choose':    'Choose texture from file',
            'tt_tex_remove':    'Remove texture',
        },
    },
    'de': {
        'toolbar': {
            'tt_world_open':    'Welt aus Datei öffnen (.karxml)',
            'tt_world_save':    'Welt in Datei speichern (.karxml)',
            'tt_world_pub':     'Geteilte Welt veröffentlichen / speichern (Admin)',
            'tt_world_del':     'Ausgewählte veröffentlichte Welt löschen (Admin)',
            'tt_share':         'Welt mit Schülern teilen — Schüler, Link und Fortschritt in einem Fenster',
            'tt_admin':         'Admin-Modus — Anmeldung mit Passwort',
            'tt_app_settings':  'Einstellungen (Sprache, Karel-Aussehen)',
            'tt_conn_offline':  'offline',
            'tt_fwd':           'vorwärts',
            'tt_left':          'links drehen',
            'tt_right':         'rechts drehen',
            'tt_back':          'zurück',
            'tt_prog_open':     'Programm aus Datei öffnen',
            'tt_prog_save':     'Programm in Datei speichern',
        },
        'app_settings': {
            'tt_tex_choose':    'Textur aus Datei auswählen',
            'tt_tex_remove':    'Textur entfernen',
        },
    },
    'fr': {
        'toolbar': {
            'tt_world_open':    'Ouvrir le monde depuis un fichier (.karxml)',
            'tt_world_save':    'Enregistrer le monde dans un fichier (.karxml)',
            'tt_world_pub':     'Publier / enregistrer le monde partagé (admin)',
            'tt_world_del':     'Supprimer le monde publié sélectionné (admin)',
            'tt_share':         'Partager le monde avec les élèves — ajoutez un élève, un lien et la progression en une fenêtre',
            'tt_admin':         'Mode admin — connexion avec mot de passe',
            'tt_app_settings':  'Paramètres (langue, apparence de Karel)',
            'tt_conn_offline':  'hors ligne',
            'tt_fwd':           'avancer',
            'tt_left':          'tourner à gauche',
            'tt_right':         'tourner à droite',
            'tt_back':          'reculer',
            'tt_prog_open':     'Ouvrir le programme depuis un fichier',
            'tt_prog_save':     'Enregistrer le programme dans un fichier',
        },
        'app_settings': {
            'tt_tex_choose':    'Choisir une texture depuis un fichier',
            'tt_tex_remove':    'Supprimer la texture',
        },
    },
    'it': {
        'toolbar': {
            'tt_world_open':    'Apri mondo da file (.karxml)',
            'tt_world_save':    'Salva mondo su file (.karxml)',
            'tt_world_pub':     'Pubblica / salva mondo condiviso (admin)',
            'tt_world_del':     'Elimina mondo pubblicato selezionato (admin)',
            'tt_share':         'Condividi mondo con gli studenti — aggiungi studente, link e progresso in una finestra',
            'tt_admin':         'Modalità admin — accesso con password',
            'tt_app_settings':  'Impostazioni (lingua, aspetto di Karel)',
            'tt_conn_offline':  'offline',
            'tt_fwd':           'avanti',
            'tt_left':          'gira a sinistra',
            'tt_right':         'gira a destra',
            'tt_back':          'indietro',
            'tt_prog_open':     'Apri programma da file',
            'tt_prog_save':     'Salva programma su file',
        },
        'app_settings': {
            'tt_tex_choose':    'Scegli texture da file',
            'tt_tex_remove':    'Rimuovi texture',
        },
    },
    'es': {
        'toolbar': {
            'tt_world_open':    'Abrir mundo desde archivo (.karxml)',
            'tt_world_save':    'Guardar mundo en archivo (.karxml)',
            'tt_world_pub':     'Publicar / guardar mundo compartido (admin)',
            'tt_world_del':     'Eliminar mundo publicado seleccionado (admin)',
            'tt_share':         'Compartir mundo con alumnos — añade alumno, enlace y progreso en una ventana',
            'tt_admin':         'Modo admin — inicio de sesión con contraseña',
            'tt_app_settings':  'Configuración (idioma, apariencia de Karel)',
            'tt_conn_offline':  'sin conexión',
            'tt_fwd':           'adelante',
            'tt_left':          'girar a la izquierda',
            'tt_right':         'girar a la derecha',
            'tt_back':          'atrás',
            'tt_prog_open':     'Abrir programa desde archivo',
            'tt_prog_save':     'Guardar programa en archivo',
        },
        'app_settings': {
            'tt_tex_choose':    'Elegir textura desde archivo',
            'tt_tex_remove':    'Eliminar textura',
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
            new_sec = f'\n[{section}]\n' + '\n'.join(f'{k:<20}= {v}' for k, v in keys.items()) + '\n'
            content = content.rstrip('\n') + '\n' + new_sec
            total += len(keys)
            continue
        next_sec = re.search(r'\n\[', content[sec_match.end():])
        insert_pos = (sec_match.end() + next_sec.start()) if next_sec else len(content)
        new_lines = []
        for k, v in keys.items():
            if not re.search(r'^' + re.escape(k) + r'\s*=', content, re.MULTILINE):
                new_lines.append(f'{k:<20}= {v}')
        if new_lines:
            content = content[:insert_pos] + '\n' + '\n'.join(new_lines) + '\n' + content[insert_pos:]
            total += len(new_lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'{lang}: added {total} keys')


if __name__ == '__main__':
    for lang, sections in KEYS.items():
        add_keys_to_file(lang, sections)
