"""Add missing translation keys to all language .ini files."""
import re, os

BASE = os.path.join(os.path.dirname(__file__), '..', 'lang')

TRANSLATIONS = {
    'sk': {
        'world_settings': {
            'cmds_intro': 'Zaškrtnuté príkazy sú pre žiaka viditeľné a povolené. Odškrtnuté = skryté/zakázané.',
            'enable_proc': 'Povoliť definovanie vlastných príkazov (prikaz … koniec)',
            'enable_graphic': 'Povoliť grafické ovládanie Karla (šípky + akčné tlačidlá)',
            'enable_command': 'Povoliť príkazové ovládanie Karla (textový riadok)',
        },
        'app_settings': {
            'title': 'Nastavenia',
            'language': 'Jazyk rozhrania',
            'skin': 'Vzhľad Karla',
            'visual_hdr': 'Vzhľad sveta',
            'custom_model_hdr': 'Vlastný 3D model (admin)',
            'vis_element': 'Prvok',
            'vis_visible': 'Vidieť',
            'vis_color': 'Farba',
            'vis_texture': 'Textúra',
            'vis_always': 'vždy',
            'glb_file': 'GLB súbor',
            'glb_choose': 'Vybrať...',
            'glb_yaw': 'Orientácia (yaw)',
            'glb_height': 'Výška modelu',
        },
        'admin_login': {
            'title': '🔒 Admin prihlásenie',
            'prompt': 'Zadaj admin heslo:',
            'btn_login': 'Prihlásiť',
            'btn_cancel': 'Zrušiť',
            'error': 'Chyba prihlásenia',
            'status_active': 'Admin režim aktívny',
            'status_login': 'Admin — prihlás sa',
            'logout_confirm': 'Odhlásiť sa z admin režimu?',
            'btn_logout': 'Odhlásiť',
        }
    },
    'en': {
        'world_settings': {
            'cmds_intro': 'Checked commands are visible and allowed for students. Unchecked = hidden/disabled.',
            'enable_proc': 'Allow defining custom commands (procedure … end)',
            'enable_graphic': 'Allow graphical control of Karel (arrows + action buttons)',
            'enable_command': 'Allow command-line control of Karel (text input)',
        },
        'app_settings': {
            'title': 'Settings',
            'language': 'Interface language',
            'skin': 'Karel appearance',
            'visual_hdr': 'World appearance',
            'custom_model_hdr': 'Custom 3D model (admin)',
            'vis_element': 'Element',
            'vis_visible': 'Visible',
            'vis_color': 'Color',
            'vis_texture': 'Texture',
            'vis_always': 'always',
            'glb_file': 'GLB file',
            'glb_choose': 'Choose...',
            'glb_yaw': 'Orientation (yaw)',
            'glb_height': 'Model height',
        },
        'admin_login': {
            'title': '🔒 Admin login',
            'prompt': 'Enter admin password:',
            'btn_login': 'Login',
            'btn_cancel': 'Cancel',
            'error': 'Login error',
            'status_active': 'Admin mode active',
            'status_login': 'Admin — log in',
            'logout_confirm': 'Log out of admin mode?',
            'btn_logout': 'Log out',
        }
    },
    'de': {
        'world_settings': {
            'cmds_intro': 'Markierte Befehle sind für Schüler sichtbar und erlaubt. Nicht markiert = ausgeblendet/gesperrt.',
            'enable_proc': 'Eigene Befehle definieren erlauben (prozedur … ende)',
            'enable_graphic': 'Grafische Steuerung von Karel erlauben (Pfeile + Aktionsschaltflächen)',
            'enable_command': 'Befehlszeilensteuerung von Karel erlauben (Texteingabe)',
        },
        'app_settings': {
            'title': 'Einstellungen',
            'language': 'Oberflächensprache',
            'skin': 'Karel-Aussehen',
            'visual_hdr': 'Weltaussehen',
            'custom_model_hdr': 'Eigenes 3D-Modell (Admin)',
            'vis_element': 'Element',
            'vis_visible': 'Sichtbar',
            'vis_color': 'Farbe',
            'vis_texture': 'Textur',
            'vis_always': 'immer',
            'glb_file': 'GLB-Datei',
            'glb_choose': 'Auswählen...',
            'glb_yaw': 'Ausrichtung (Yaw)',
            'glb_height': 'Modellhöhe',
        },
        'admin_login': {
            'title': '🔒 Admin-Anmeldung',
            'prompt': 'Admin-Passwort eingeben:',
            'btn_login': 'Anmelden',
            'btn_cancel': 'Abbrechen',
            'error': 'Anmeldefehler',
            'status_active': 'Admin-Modus aktiv',
            'status_login': 'Admin — anmelden',
            'logout_confirm': 'Vom Admin-Modus abmelden?',
            'btn_logout': 'Abmelden',
        }
    },
    'fr': {
        'world_settings': {
            'cmds_intro': "Les commandes cochées sont visibles et autorisées pour les élèves. Non cochées = masquées/désactivées.",
            'enable_proc': "Autoriser la définition de commandes personnalisées (procedure … fin)",
            'enable_graphic': "Autoriser le contrôle graphique de Karel (flèches + boutons)",
            'enable_command': "Autoriser le contrôle par ligne de commande (saisie texte)",
        },
        'app_settings': {
            'title': 'Paramètres',
            'language': "Langue de l'interface",
            'skin': 'Apparence de Karel',
            'visual_hdr': 'Apparence du monde',
            'custom_model_hdr': 'Modèle 3D personnalisé (admin)',
            'vis_element': 'Élément',
            'vis_visible': 'Visible',
            'vis_color': 'Couleur',
            'vis_texture': 'Texture',
            'vis_always': 'toujours',
            'glb_file': 'Fichier GLB',
            'glb_choose': 'Choisir...',
            'glb_yaw': 'Orientation (lacet)',
            'glb_height': 'Hauteur du modèle',
        },
        'admin_login': {
            'title': '🔒 Connexion admin',
            'prompt': 'Entrer le mot de passe admin :',
            'btn_login': 'Se connecter',
            'btn_cancel': 'Annuler',
            'error': 'Erreur de connexion',
            'status_active': 'Mode admin actif',
            'status_login': 'Admin — se connecter',
            'logout_confirm': 'Se déconnecter du mode admin ?',
            'btn_logout': 'Se déconnecter',
        }
    },
    'it': {
        'world_settings': {
            'cmds_intro': "I comandi selezionati sono visibili e consentiti per gli studenti. Non selezionati = nascosti/disabilitati.",
            'enable_proc': "Consentire la definizione di comandi personalizzati (procedura … fine)",
            'enable_graphic': "Consentire il controllo grafico di Karel (frecce + pulsanti)",
            'enable_command': "Consentire il controllo da riga di comando (input testo)",
        },
        'app_settings': {
            'title': 'Impostazioni',
            'language': "Lingua dell'interfaccia",
            'skin': 'Aspetto di Karel',
            'visual_hdr': 'Aspetto del mondo',
            'custom_model_hdr': 'Modello 3D personalizzato (admin)',
            'vis_element': 'Elemento',
            'vis_visible': 'Visibile',
            'vis_color': 'Colore',
            'vis_texture': 'Texture',
            'vis_always': 'sempre',
            'glb_file': 'File GLB',
            'glb_choose': 'Scegli...',
            'glb_yaw': 'Orientamento (imbardata)',
            'glb_height': 'Altezza modello',
        },
        'admin_login': {
            'title': '🔒 Accesso admin',
            'prompt': 'Inserisci la password admin:',
            'btn_login': 'Accedi',
            'btn_cancel': 'Annulla',
            'error': 'Errore di accesso',
            'status_active': 'Modalità admin attiva',
            'status_login': 'Admin — accedi',
            'logout_confirm': 'Uscire dalla modalità admin?',
            'btn_logout': 'Esci',
        }
    },
    'es': {
        'world_settings': {
            'cmds_intro': 'Los comandos marcados son visibles y permitidos para los alumnos. Sin marcar = ocultos/desactivados.',
            'enable_proc': 'Permitir definir comandos personalizados (procedimiento … fin)',
            'enable_graphic': 'Permitir control gráfico de Karel (flechas + botones)',
            'enable_command': 'Permitir control por línea de comandos (entrada de texto)',
        },
        'app_settings': {
            'title': 'Configuración',
            'language': 'Idioma de la interfaz',
            'skin': 'Apariencia de Karel',
            'visual_hdr': 'Apariencia del mundo',
            'custom_model_hdr': 'Modelo 3D personalizado (admin)',
            'vis_element': 'Elemento',
            'vis_visible': 'Visible',
            'vis_color': 'Color',
            'vis_texture': 'Textura',
            'vis_always': 'siempre',
            'glb_file': 'Archivo GLB',
            'glb_choose': 'Elegir...',
            'glb_yaw': 'Orientación (guiñada)',
            'glb_height': 'Altura del modelo',
        },
        'admin_login': {
            'title': '🔒 Inicio de sesión admin',
            'prompt': 'Introduce la contraseña de admin:',
            'btn_login': 'Iniciar sesión',
            'btn_cancel': 'Cancelar',
            'error': 'Error de inicio de sesión',
            'status_active': 'Modo admin activo',
            'status_login': 'Admin — inicia sesión',
            'logout_confirm': '¿Cerrar sesión del modo admin?',
            'btn_logout': 'Cerrar sesión',
        }
    },
}


def add_keys_to_file(lang, sections):
    path = os.path.join(BASE, f'{lang}.ini')
    with open(path, encoding='utf-8') as f:
        content = f.read()

    for section, keys in sections.items():
        # Update cmds_intro separately (replace existing)
        if section == 'world_settings' and 'cmds_intro' in keys:
            new_val = keys.pop('cmds_intro')
            content = re.sub(r'(cmds_intro\s*=\s*).*', r'\g<1>' + new_val, content)

        if not keys:
            continue

        if f'[{section}]' in content:
            # Find the section and insert keys before the next section
            sec_match = re.search(r'\[' + re.escape(section) + r'\]', content)
            next_sec = re.search(r'\n\[', content[sec_match.end():])
            insert_pos = (sec_match.end() + next_sec.start()) if next_sec else len(content)
            # Only add keys that don't already exist
            new_lines = []
            for k, v in keys.items():
                if not re.search(r'^' + re.escape(k) + r'\s*=', content, re.MULTILINE):
                    new_lines.append(f'{k:<16}= {v}')
            if new_lines:
                content = content[:insert_pos] + '\n' + '\n'.join(new_lines) + '\n' + content[insert_pos:]
        else:
            # New section
            new_sec = f'\n[{section}]\n'
            new_sec += '\n'.join(f'{k:<16}= {v}' for k, v in keys.items()) + '\n'
            content = content.rstrip('\n') + '\n' + new_sec

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'{lang}: done')


if __name__ == '__main__':
    for lang, sections in TRANSLATIONS.items():
        add_keys_to_file(lang, dict(sections))  # copy to avoid mutation
