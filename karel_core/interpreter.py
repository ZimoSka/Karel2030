# -*- coding: utf-8 -*-
"""Karel core – lexer, parser, AST a interpreter."""
import sys, re, time, threading
from .base import KarelError, KarelStop, KarelBudget, KarelLimit
from .lang import KW

# Rekurzia: MAX_D=1000 úrovní Karel rekurzie (~3-4 Python rámce/úroveň).
sys.setrecursionlimit(12000)
try:
    threading.stack_size(64 * 1024 * 1024)
except (ValueError, RuntimeError):
    pass

CMD_T={'FORWARD','BACK','LEFT','RIGHT','DROP','PICK','DROP_BIG','MARK','CLEAR','SLOWLY','QUICKLY'}
COND_T={'WALL','BRICK','FREE','SIGN','TRUE','FALSE'}
CLOSE_T={'END','END_REPEAT','END_WHILE','END_IF'}

class Tok:
    __slots__=('t','v','ln')
    def __init__(self,t,v,ln=0): self.t=t;self.v=v;self.ln=ln

def tokenize(src):
    src=re.sub(r'//[^\n]*',' ',src); src=re.sub(r'#[^\n]*',' ',src)
    src=re.sub(r'\{[^}]*\}',' ',src)
    toks=[]; ln=1; i=0; n=len(src)
    while i<n:
        c=src[i]
        if c=='\n': ln+=1;i+=1;continue
        if c.isspace(): i+=1;continue
        if c=='(': toks.append(Tok('LPAREN','(',ln)); i+=1; continue
        if c==')': toks.append(Tok('RPAREN',')',ln)); i+=1; continue
        if c=='*':
            j=i+1
            while j<n and (src[j].isalpha() or src[j]=='_' or ord(src[j])>127): j+=1
            w=src[i:j].lower(); toks.append(Tok(KW.get(w,'UNK'),src[i:j],ln)); i=j;continue
        if c.isdigit():
            j=i
            while j<n and src[j].isdigit(): j+=1
            toks.append(Tok('NUM',src[i:j],ln)); i=j;continue
        if c.isalpha() or c=='_' or ord(c)>127:
            j=i
            while j<n and (src[j].isalnum() or src[j]=='_' or ord(src[j])>127): j+=1
            w=src[i:j]; toks.append(Tok(KW.get(w.lower(),'ID'),w,ln)); i=j;continue
        i+=1
    toks.append(Tok('EOF','',ln)); return toks

class AN: pass
class ProgN(AN):
    def __init__(self,p,m): self.procedures=p;self.main_stmts=m
class CmdN(AN):
    def __init__(self,c,ln=0): self.cmd=c;self.line=ln
class CallN(AN):
    def __init__(self,n,ln=0): self.name=n;self.line=ln
class RepN(AN):
    def __init__(self,n,b,ln=0): self.count=n;self.body=b;self.line=ln
class WhileN(AN):
    def __init__(self,c,b,ln=0): self.cond=c;self.body=b;self.line=ln
class IfN(AN):
    def __init__(self,c,t,e,ln=0): self.cond=c;self.then_body=t;self.else_body=e;self.line=ln
class CondN(AN):
    def __init__(self,ct,neg=False): self.cond_type=ct;self.negated=neg
class NotN(AN):
    def __init__(self,child): self.child=child
class AndN(AN):
    def __init__(self,l,r): self.left=l;self.right=r
class OrN(AN):
    def __init__(self,l,r): self.left=l;self.right=r

class ParseErr(Exception):
    def __init__(self,m,ln=0): super().__init__(f"Riadok {ln}: {m}");self.line=ln

MAX_PARSE_DEPTH = 400   # tvrdý limit zanorenia — bráni RecursionError/segfault

class Parser:
    def __init__(self,toks): self.toks=toks;self.pos=0;self.depth=0
    def _descend(self,ln):
        self.depth+=1
        if self.depth>MAX_PARSE_DEPTH:
            raise ParseErr("Program je príliš hlboko zanorený",ln)
    def pk(self): return self.toks[self.pos]
    def eat(self,exp=None):
        t=self.toks[self.pos]
        if exp and t.t!=exp: raise ParseErr(f"Čakal som '{exp}', dostal '{t.t}'('{t.v}')",t.ln)
        self.pos+=1; return t
    def parse(self):
        ps={}; main=None
        while self.pk().t!='EOF':
            t=self.pk()
            if t.t=='PROCEDURE': n,b=self._proc(); ps[n.lower()]=b
            elif t.t=='BEGIN': self.eat(); main=self._stmts()
            if self.pk().t in CLOSE_T: self.eat()
            elif t.t not in ('PROCEDURE','BEGIN'): self.pos+=1
        return ProgN(ps,main or [])
    def _proc(self):
        self.eat('PROCEDURE'); t=self.pk()
        if t.t in ('ID','NUM'): name=self.eat().v
        else: raise ParseErr(f"Čakám meno príkazu",t.ln)
        if self.pk().t=='BEGIN': self.eat()
        body=self._stmts()
        if self.pk().t in CLOSE_T: self.eat()
        return name,body
    def _stmts(self):
        self._descend(self.pk().ln)
        s=[]
        while self.pk().t not in CLOSE_T and self.pk().t not in ('ELSE','EOF'):
            n=self._stmt()
            if n: s.append(n)
        self.depth-=1
        return s
    def _stmt(self):
        t=self.pk()
        if t.t in CMD_T: self.eat(); return CmdN(t.t,t.ln)
        if t.t=='REPEAT': return self._rep()
        if t.t=='WHILE':  return self._whl()
        if t.t=='IF':     return self._if()
        if t.t in ('ID','NUM'): self.eat(); return CallN(t.v,t.ln)
        if t.t=='BEGIN': self.eat(); return None
        self.pos+=1; return None
    def _rep(self):
        t=self.eat('REPEAT'); n=int(self.eat('NUM').v)
        if self.pk().t=='TIMES': self.eat()
        b=self._stmts()
        if self.pk().t in CLOSE_T: self.eat()
        return RepN(n,b,t.ln)
    def _whl(self):
        t=self.eat('WHILE'); c=self._cond()
        if self.pk().t=='DO': self.eat()
        b=self._stmts()
        if self.pk().t in CLOSE_T: self.eat()
        return WhileN(c,b,t.ln)
    def _if(self):
        t=self.eat('IF'); c=self._cond()
        if self.pk().t in ('THEN','BEGIN'): self.eat()
        tb=self._stmts(); eb=[]
        if self.pk().t=='ELSE': self.eat(); eb=self._stmts()
        if self.pk().t in CLOSE_T: self.eat()
        return IfN(c,tb,eb,t.ln)
    def _cond(self):
        # Rekurzívny zostup: priorita NOT > AND > OR
        return self._or_expr()
    def _or_expr(self):
        left=self._and_expr()
        while self.pk().t=='OR':
            self.eat(); right=self._and_expr(); left=OrN(left,right)
        return left
    def _and_expr(self):
        left=self._not_expr()
        while self.pk().t=='AND':
            self.eat(); right=self._not_expr(); left=AndN(left,right)
        return left
    def _not_expr(self):
        if self.pk().t=='NOT':
            self.eat(); self._descend(self.pk().ln)
            inner=self._not_expr(); self.depth-=1; return NotN(inner)
        return self._atom()
    def _atom(self):
        t=self.pk()
        if t.t=='LPAREN':
            self.eat(); self._descend(t.ln); e=self._or_expr(); self.depth-=1
            if self.pk().t=='RPAREN': self.eat()
            else: raise ParseErr("Chýba pravá zátvorka ')'",self.pk().ln)
            return e
        if t.t in COND_T: self.eat(); return CondN(t.t)
        raise ParseErr(f"Podmienka očakávaná, dostal '{t.v}'",t.ln)

def parse(src): return Parser(tokenize(src)).parse()

class StopEx(Exception): pass

class KarelInterpreter:
    MAX_D=1000          # max hĺbka rekurzie (úrovní volania procedúr)
    MAX_OPS=100_000     # bezpečnostný strop proti nekonečnému cyklu
    def __init__(self,world):
        self.world=world; self.delay=0.25
        self._stop=False; self._d=0; self._ops=0; self.procedures={}
        self.on_step=self.on_error=self.on_finish=self.on_budget=self.on_limit=None
    def stop(self): self._stop=True
    def _tick(self):
        """Počíta vykonané kroky interpretera; chráni pred nekonečným cyklom."""
        self._ops += 1
        if self._ops > self.MAX_OPS: raise KarelLimit('loop')
    def run(self,prog):
        self._stop=False; self._d=0; self._ops=0; self.procedures=prog.procedures
        try:
            self._ex(prog.main_stmts)
            if self.on_finish: self.on_finish(None)
        except StopEx:
            if self.on_finish: self.on_finish("Zastavené.")
        except KarelStop:
            if self.on_finish: self.on_finish(None)   # tiché zastavenie pri stene
        except KarelBudget as e:
            if self.on_budget: self.on_budget(e.kind)
            else: raise                                # priame ovládanie zachytí samo
        except KarelLimit as e:
            if self.on_limit: self.on_limit(e.kind)
            else: raise                                # priame ovládanie zachytí samo
        except RecursionError:
            # poistka ak by Python limit udrel skôr ako MAX_D
            if self.on_limit: self.on_limit('recursion')
            elif self.on_error: self.on_error("Príliš hlboká rekurzia!")
        except KarelError as e:
            if self.on_error: self.on_error(str(e))
        except Exception as e:
            if self.on_error: self.on_error(f"Chyba: {e}")
    def _ex(self,stmts):
        for s in stmts:
            if self._stop: raise StopEx()
            self._rs(s)
    def _rs(self,s):
        self._tick()
        if isinstance(s,CmdN): self._cmd(s)
        elif isinstance(s,CallN): self._call(s.name)
        elif isinstance(s,RepN):
            for _ in range(s.count):
                if self._stop: raise StopEx()
                self._tick()
                self._ex(s.body)
        elif isinstance(s,WhileN):
            while self._ev(s.cond):
                if self._stop: raise StopEx()
                self._tick()
                self._ex(s.body)
        elif isinstance(s,IfN):
            self._ex(s.then_body if self._ev(s.cond) else s.else_body)
    def _call(self,name):
        self._d+=1
        if self._d>self.MAX_D: raise KarelLimit('recursion')
        try:
            nl=name.lower()
            if nl not in self.procedures: raise KarelError(f"Neznámy príkaz '{name}'")
            self._ex(self.procedures[nl])
        finally: self._d-=1
    def _cmd(self,node):
        w=self.world; c=node.cmd
        if c in w.settings.disabled_cmds:
            raise KarelError(f"Príkaz je zakázaný v tomto svete!")
        if   c=='FORWARD':  w.move_forward()
        elif c=='BACK':     w.move_back()
        elif c=='LEFT':     w.turn_left()
        elif c=='RIGHT':    w.turn_right()
        elif c=='DROP':     w.drop_brick()
        elif c=='PICK':     w.pick_brick()
        elif c=='DROP_BIG': w.drop_big_brick()
        elif c=='MARK':     w.mark()
        elif c=='CLEAR':    w.clear()
        elif c=='SLOWLY':   self.delay=min(self.delay*2,3.0)
        elif c=='QUICKLY':  self.delay=max(self.delay/2,0.02)
        if self.on_step: self.on_step()
        if self.delay>0: time.sleep(self.delay)
    def _ev(self,node):
        if isinstance(node,NotN): return not self._ev(node.child)
        if isinstance(node,AndN): return self._ev(node.left) and self._ev(node.right)
        if isinstance(node,OrN):  return self._ev(node.left) or  self._ev(node.right)
        # CondN — atóm
        w=self.world; ct=node.cond_type
        r=(w.check_wall() if ct=='WALL' else w.check_brick() if ct=='BRICK'
           else w.check_free() if ct=='FREE' else w.check_sign() if ct=='SIGN'
           else True if ct=='TRUE' else False)
        return (not r) if node.negated else r


