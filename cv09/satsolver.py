#! /bin/env python3
import sys

sys.setrecursionlimit(2048)

# helper function for 'nice' level dependent logging
logLevel = 0
def incLog():
    global logLevel
    logLevel += 1
def decLog():
    global logLevel
    logLevel -= 1
def log(s):
    return
    sys.stderr.write('%s %s\n' % ('='*logLevel, s))
    sys.stderr.flush()


class Var:
    """ A class that represents a variable.
        It automatically creates two literals (plain/True and negated/False) that
        reference this variable, access them via v.lit[True] and v.lit[False].
    """
    def __init__(self, n):
        self.n = n
        self.isSet = False
        self.val = None
        self.lit = {}
        self.lit[True] = Lit(self, True)
        self.lit[False] = Lit(self, False)
        self.lit[True].neg = self.lit[False]
        self.lit[False].neg = self.lit[True]

    def set(self, val):
        """ Sets the variable to val. """
        self.isSet = True
        self.val = val
    def unset(self):
        """ Unsets the variable. """
        self.isSet = False

    def __repr__(self):
        return str(self)
    def __str__(self):
        return 'V(%d:%s)' % (self.n, 'u' if not self.isSet else ( 'T' if self.val else 'F' ) )

class Lit:
    """ A class that represents a literal.
        Don't create these yourselves, create a Var-iable and use the ones from there.
    """
    def __init__(self, var, sgn):
        self.var = var
        self.sgn = sgn
        self.watchedIn = []

    def setTrue(self):
        """ Sets this literal to be true.
            This sets the literal's variable to the corresponding value.
        """
        self.var.set(self.sgn)
    def unset(self):
        """ Unsets this literal (and its variable). """
        self.var.unset()

    def isSet(self):
        return self.var.isSet
    def isTrue(self):
        return self.sgn == self.var.val

    def __repr__(self):
        return str(self)
    def __str__(self):
        return '%s%d:%s' % (
                '+' if self.sgn else '-',
                self.var.n,
                'u' if not self.isSet() else ('T' if self.isTrue() else 'F'),
                )

class Clause(list):
    ncls = 0 # just for debug output
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.n = Clause.ncls
        Clause.ncls += 1

        self.watched = [ None, None ]

    def __hash__(self):
        return id(self)
    def __str__(self):
        return 'C(%d,%s)' % (self.n,repr(self))

    def setWatch(self, wi, l):
        """ Sets the wi-th watched literal to l.
            l must be a literal from this clause.
        """
        if l is not None and l not in self:
            raise Exception('New watched literal %s not in clause %s!' % (l, self))
        if self.watched[wi] is not None:
            self.watched[wi].watchedIn.remove(self)
        self.watched[wi] = l
        if l is not None:
            l.watchedIn.append(self)

    def findNewWatch(self, old):
        """ Finds a new literal to watch if old became false.
        Returns True if it found a new lit (or if old is ok),
        False if there is no other acceptable literal (old won't be changed).
        """
        if self.watched[0] == old:
            wi = 0
            other = self.watched[1]
        elif self.watched[1]== old:
            wi = 1
            other = self.watched[0]
        else:
            raise Exception("Bit a watched literal %s" %old)

        for lit in self:
            if lit == other:
                continue #preskocime na druhy watched
            if not lit.isSet():
                self.setWatch(wi,lit)
                return True
            if lit.isTrue():
                self.setWatch(wi,lit)
                return True

        return False
            
class Solver:
    class InputError(Exception):
        pass

    def __init__(self):
        self.clauses = []
        self.vars = {}
        self.maxVar = 0
        self.nVars = 0
        self.nCls = 0

    def read(self, ifName):
        """ Reads cnf from input file ifName.
            ifName can be '-' for stdin.
            Loads clauses into self.clauses and vars into self.vars.
            Sets self.maxVar, self.nVars (=len(vars)), self.nCls (=len(clauses)).
        """
        self.clauses = []
        self.vars = {}
        maxVar = 0
        headerVar = 0
        headerCls = 0
        cls = Clause()

        if ifName == '-':
            ifile = sys.stdin
        else:
            ifile = open(ifName, 'r')
        with ifile:
            for line in ifile:
                line = line.strip()
                if line[0] == 'c':
                    continue
                if line[0] == 'p':
                    h = line.split()
                    if h[0] != 'p' or h[1] != 'cnf':
                        raise self.InputError('bad header')
                    try:
                        headerVar = int(h[2])
                        headerCls = int(h[3])
                    except ValueError:
                        raise self.InputError('bad header')
                    continue
                try:
                    # clause / literals
                    for lit in (int(x) for x in line.split()):
                        if lit == 0:
                            self.clauses.append(cls)
                            cls = Clause()
                        else:
                            absLit = abs(lit)
                            if absLit not in self.vars:
                                self.vars[absLit] = Var(absLit)
                            cls.append(self.vars[absLit].lit[lit>0])
                            if absLit > maxVar:
                                maxVar = absLit
                except ValueError:
                    raise self.InputError('Error reading input %s' % repr(line))

        if headerVar and headerVar != maxVar:
            sys.stderr.write('Wrong number of variables in header: %d %d\n' % (headerVar, maxVar))
        if headerCls and headerCls != len(self.clauses):
            sys.stderr.write('Wrong number of clauses in header: %d %d\n' % (headerCls, len(self.clauses)))
        if cls:
            raise self.InputError('Unfinished clause in input: %s' % repr(cls))

        self.maxVar = maxVar
        self.nVars = len(self.vars)
        self.nCls = len(self.clauses)

    def write(self, ofName, sat):
        """ Writes the solution into ofName.
            ofName can be '-' for stdout.
        """
        if ofName == '-':
            of = sys.stdout
        else:
            of = open(ofName, "w")
        with of:
            if sat:
                log('SAT')
                of.write('SAT\n')
                for n in range(1,self.maxVar+1):
                    isTrue = False
                    if n in self.vars:
                        isTrue = self.vars[n].val
                    of.write( ('%d ' if isTrue else '-%s ') % n )
                of.write('0\n')
            else:
                log('UNSAT')
                of.write('UNSAT\n')

    def chooseBranchLit(self):
        for var in self.vars.values():
            if not var.isSet:
                return var.lit[True]
        raise Exception("All vars are set already")

    def initWatched(self):
        self.unitLiterals = []
        for c in self.clauses:
            if len(c) == 0 :
                return False 
            elif len(c) == 1:
                c.setWatch(0,c[0])
                c.setWatch(1,c[0])
                self.unitLiterals.append(c[0])
            else:
                c.setWatch(0,c[0])
                c.setWatch(1,c[1])
                if not c.findNewWatch(c[1]):
                    self.unitLiterals.append(c[0])
                    
                    
        return True
    
    def setLiteral(self,lit):

        ''' nastavi lit na true, poriesi ak je lit
        niekde watched....vrati false,ak sme nieco spravili nesplnitelnym'''
        if lit.isSet():
            return lit.isTrue()
        
        lit.setTrue()
        self.assignedLits.append(lit)
        
        negLit = lit.neg
        for c in negLit.watchedIn[:]:
            if not c.findNewWatch(negLit):
                if c.watched[0] == negLit:
                    other = c.watched[1]
                elif c.watched[1] == negLit:
                    other = c.watched[0]
                else:
                    raise Exception("Bad watched literal")


                if other.isSet() and not other.isTrue():
                    #conflict
                    return False

                if not other.isSet():
                    self.unitLiterals.append(other)

        
        return True

                
    def unitPropagate(self):
        while self.unitLiterals:
             lit = self.unitLiterals.pop()
             if not self.setLiteral(lit):
                 return False
        return True

    def backtrack(self,where):
        while len(self.assignedLits)> where:
            lit = self.assignedLits.pop()
            lit.unset()
            
             

    def dpll(self):
        if len(self.assignedLits) == self.nVars:
            return True

        branchLiteral = self.chooseBranchLit()
        for l in [ branchLiteral, branchLiteral.neg] :
            assigned = len(self.assignedLits)
            self.unitLiterals = []
            sat = False
            if self.setLiteral(l):
                if self.unitPropagate():
                    if self.dpll():
                        return True
            self.backtrack(assigned)

        return False
            

        

    def solve(self, ifName, ofName):
        self.read(ifName)
        sat = False
        self.assignedLits = []
        if self.initWatched():
            if self.unitPropagate():
                sat = self.dpll()            
            
        self.write(ofName, sat)



if __name__ == "__main__":
    import sys
    s = Solver()
    ifName = 'testData/normal/sat/300-flat100-22.cnf '
    ofName = '-'
    if len(sys.argv) >= 2:
        ifName = sys.argv[1]
    if len(sys.argv) >= 3:
        ofName = sys.argv[2]
    s.solve(ifName, ofName)

# vim: set sw=4 ts=4 sts=4 et :
