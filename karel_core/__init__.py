# -*- coding: utf-8 -*-
"""karel_core – jadro Karel simulátora bez GUI závislostí.

Extrahované z karel2010.py (desktop tkinter verzia). Zdieľané medzi
desktop appkou a web backendom (Karel 2030)."""

from .base import Direction, KarelError, KarelStop, KarelBudget, KarelLimit
from .missions import GoalCondition, evaluate_goals
from .world import World, WorldSettings, BUILTIN_WORLD
from .interpreter import (CMD_T, COND_T, CLOSE_T, Tok, tokenize,
    AN, ProgN, CmdN, CallN, RepN, WhileN, IfN, CondN, NotN, AndN, OrN,
    ParseErr, Parser, parse, StopEx, KarelInterpreter)
from .samples import EXAMPLES
from .lang import (KW, _LANG_PRIMARY, _LANG_DISABLED, _LANG_NAME,
    _INTERP_LANG_DIR, _LANG_DIR, _KW_REVERSE,
    _load_all_interpreter_langs, _primary_kw,
    _cmds_list, _cmds_structs, _cmds_conds,
    _available_ui_langs, _available_prog_langs,
    _load_ui_lang, _T, _switch_prog_lang, _prog_btn, current_prog_lang)
