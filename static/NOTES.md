# T3 frontend — poznámky ku kontraktu (docs/api.md v1)

## Diery / nejasnosti v kontrakte

1. **`session_id` učiteľskej WS** (`/ws/teacher/{session_id}`) — kontrakt nehovorí,
   kto session_id generuje. Frontend ho generuje sám (náhodný string, uložený
   v `sessionStorage` → prežije reload, nie nové okno). Server by mal session
   lazy-vytvoriť pri pripojení.
2. **`program_text` v state JSON** — §4 ho v State neuvádza, ale §2 hovorí, že
   `GET /api/worlds/{id}` vracia „state JSON + program_text“. Frontend číta
   `state.program_text` ak príde (učiteľský mód, reason=connect/load) — server
   nech ho pridá na vrch State pri svetoch s uloženým programom.
3. **Intro dialóg** — frontend zobrazuje `meta.intro_html` automaticky pri
   `state reason="connect"`. Kontrakt nedefinuje „už videl zadanie“ flag;
   zobrazuje sa pri každom pripojení (aj reconnecte nie — len prvom connect).
4. **`direct` cmd = slovo aliasu** — frontend posiela primárne slovo z
   `/api/langs/prog/{code}` (`primary[TOKEN]`). Kontrakt nehovorí, či server
   akceptuje aj TOKEN — frontend posiela vždy slovo.
5. **Mission/settings pre žiaka** — §4: server ich posiela žiakovi len pri
   `connect`. `step` správy ich teda nemusia obsahovať — frontend si settings
   drží z posledného plného `state`.
6. **UI jazyk** — frontend zatiaľ natvrdo `sk` (`/api/langs/ui/sk`); dropdown
   jazykov je TODO (kontrakt endpoint má).
7. **Chýba v kontrakte**: upload .karxml v učiteľskom móde (REST parse-karxml
   existuje, ale UI naň zatiaľ nie je — TODO tlačidlo Otvoriť svet),
   share-links UI, world settings dialóg — frontend v1 pokrýva žiacky beh
   + učiteľský základ (run/stop/reset/direct/speed/príklady).

## Vendor súbory (static/vendor/)

Prostredie agenta nemalo povolený shell (curl/python) — súbory NIE sú stiahnuté.
Stiahnutie: `python static/vendor/get_vendor.py` (overuje obsah aj veľkosť).
Potrebné súbory:
- three.min.js (r128, cdnjs)
- OrbitControls.js (three@0.128.0, jsdelivr UMD)
- codemirror.min.js + codemirror.min.css + simple.min.js (5.65.16, cdnjs)

`index.html` má dočasný **CDN fallback** — keď lokálny vendor súbor chýba,
načíta sa z CDN (funguje len online; pre offline Docker treba vendor stiahnuť
a fallback môže ostať ako poistka).

## Mock mód (?mock=1)

`static/js/mock.js` — MockApi + MockWS s rovnakým rozhraním ako Api/KarelWS.
Simuluje: pohyb (okrajové steny, kvader=stena, max_climb 1), poloz/zdvihni/
kvader/oznac/odznac, `opakuj N krat … *opakuj` (vnorené), parse_error,
started/step/finished, direct, speed, reset. Bez: kym/ak, procedúry, misie,
rozpočty — tie čakajú na reálny backend.
