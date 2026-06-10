# Server — poznámky k dieram v API kontrakte (docs/api.md v1)

Rozhodnutia prijaté tam, kde kontrakt mlčí. Pri zmene kontraktu zosúladiť.

1. **`all_words` v `/api/langs/prog/{code}`** — vraciame celé `KW`
   (všetky jazyky naraz), lebo interpreter aj tak akceptuje každý jazyk
   súčasne; frontend tak highlightuje aj zmiešaný kód.

2. **`direct` pri vyčerpanom rozpočte** — kontrakt definuje typ `budget` len
   pri behu. Posielame `direct_result {ok:false, error:"budget"}` **a hneď za
   ním** `budget {kind}` — frontend zobrazí rovnaký dialóg ako pri behu.
   Príkaz sa nevykoná (správanie ako desktop `ControlPanel._do`).

3. **`direct` počas bežiaceho programu** — odmietnuté:
   `direct_result {ok:false, error:"running"}`.

4. **`state` po úspešnom `direct`** — posielame `step` správu (so sparse
   stavom) hneď za `direct_result`, plus prípadnú `mission` správu —
   frontend nemusí robiť `get_state`.

5. **Mission v state JSON** — `mission` je zoznam plochých dictov s poľami
   ako XML atribúty (`check`, `eval`, `when`, `op`, `negate`, `x`, `y`, `z`,
   `cell_*`); snapshot podmienka má navyše `snap` dict (riadky polí,
   `karel_dir` ako písmeno).

6. **`finished` vs `mission` poradie** — pri `on_finish` misii posielame
   najprv `finished {status:"done"}` a potom `mission`. Pri `on_step` misii
   posielame `mission` a beh zastavíme (`itp.stop()`) → nasleduje
   `finished {status:"stopped"}` (ako desktop).

7. **Učiteľská WS** — `session_id` v ceste sa zatiaľ nepoužíva na nič
   (žiadna autentifikácia v kontrakte v1); každé pripojenie = čerstvá session
   s builtin svetom. `apply_settings` patchuje `world` aj `base` (vzor pre
   reset), bez resetu Karela — ekvivalent desktop Apply.

8. **`parse-karxml`** — body je surové XML (nie JSON), podľa kontraktu.
   Limit 256 kB → 400 `too_large`.

9. **`disable_procedure`** — kontrakt nedefinuje správanie; program
   s definovanou procedúrou vráti `parse_error` (line 0) pred spustením.

10. **Chyba „program už beží"** — druhý `run` počas behu vráti `error`
    správu, beh pokračuje (1 bežiaci program na session, §6).

11. **`mission_reset_on_failure`** — server pri failure automaticky
    neresetuje; frontend dostane `mission {result:"failure"}` a pošle
    `reset` sám (rozhodnutie UI vrstvy). Flag je v `.karxml`, do state JSON
    ho kontrakt nezaradil.
