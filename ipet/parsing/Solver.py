
import re
import os
from ipet.misc import misc
from ipet.Experiment import Experiment

class Solver():
    
    DEFAULT=None
    DEFAULT_SOLVERID="defaultSolver"
    
    def __init__(self, 
                 solverID=DEFAULT_SOLVERID, 
                 recognition_pattern=None, 
                 primalbound_pattern=None, 
                 primalbound_lineindices=None, 
                 dualbound_pattern=None, 
                 dualbound_lineindices=None, 
                 solvingtimer_pattern=None, 
                 solvingtime_lineindices=None,
                 version_pattern=None,
                 version_lininedices=None,
                 timelimitreached_pattern=None, 
                 timelimitreached_expression=None):
        self.solverId = solverID
        self.recognition_pattern = recognition_pattern
        self.primalbound_pattern = primalbound_pattern 
        self.primalbound_lineindices = primalbound_lineindices
        self.dualbound_pattern = dualbound_pattern
        self.dualbound_lineindices = dualbound_lineindices
        self.solvingtimer_pattern = solvingtimer_pattern
        self.solvingtime_lineindices = solvingtime_lineindices
        self.version_pattern = version_pattern
        self.version_lininedices = version_lininedices
        if not timelimitreached_pattern is None and not timelimitreached_expression is None:
            self.timelimitreached_pattern = re.compile(timelimitreached_pattern)
            self.timelimitreached_expression = re.compile(timelimitreached_expression)
        self.reset()
        
    def extractVersion(self, line):
        if re.search(self.version_pattern, line):
            self.addData(Experiment.Key_Version, line.split()[self.version_lininedices])
        
    def extractTimeLimitReached(self, line):
        '''
        reads if memory limit was hit
        '''
        if not self.timelimitreached_pattern is None and self.timelimitreached_pattern.match(line):
            match = self.timelimitreached_expression.search(line)
            if match is not None:
                stringexpression = match.groups()[0]
                limit = "".join((part.capitalize() for part in stringexpression.split()))
                self.addData(Experiment.Key_TimeLimitReached, limit)

    def extractSolvingTime(self, line):
        '''
        reads the overall solving time
        '''
        if re.search(self.solvingtimer_pattern, line):
            solvingtime = self.getWordAtIndex(line, self.solvingtime_lineindices)
            solvingtime = solvingtime.rstrip('s')
            self.addData(Experiment.Key_SolvingTime, float(solvingtime))
            
    def extractDualbound(self, line):
        '''
        returns the reported dual bound at the end of the solve
        '''
        if re.match(self.dualbound_pattern, line):
            index = self.dualbound_lineindices
            # FARI does this if belong here or in cplexsolver?
            if self == CplexSolver and re.search('^MIP - Integer optimal', line):
                index = -1
            db = self.getWordAtIndex(line, index)
            db = db.strip(',');
            try:
                db = float(db)
                if abs(db) != misc.FLOAT_INFINITY:
                    self.addData(Experiment.Key_DualBound, db)
            except ValueError:
                pass
     
    def extractPrimalbound(self, line):
        '''
        reads the primal bound at the end of the solve
        '''
        if re.search(self.primalbound_pattern, line):
            pb = self.getWordAtIndex(line, self.primalbound_lineindices)
            pb = pb.strip(',')
            if pb != '-':
                pb = float(pb)
                if abs(pb) < misc.FLOAT_INFINITY:
                    self.addData(Experiment.Key_PrimalBound, pb)
            
    def addData(self, key, data):
        # FARIDO is it okay to overwrite data?
        self.data[key] = data
    
    def readline(self, line):
        self.extractElementaryInformation(line)
        self.extractOptionalInformation(line)
        self.extractGeneralInformation(line)
        
    # should be overwritten
    def extractOptionalInformation(self, line):
        '''
        reads optional data
        '''
        pass
    
    def extractGeneralInformation(self, line):
        '''
        reads general data
        '''
        self.extractVersion(line)
    
    def extractElementaryInformation(self, line):
        '''
        reads Data that is needed for validation
        '''
#     # BestSolInfeasibleReader, 
#     # DualBoundReader, 
#     # PrimalBoundReader
#     # SolvingTimeReader, 
#     # LimitReachedReader,
#     # ErrorFileReader  
#     # primalboundhistory, dualboundhistory
#     # ObjsenseReader, 
#     # ObjlimitReader,   
        self.extractPrimalbound(line)
        self.extractDualbound(line)
        self.extractSolvingTime(line)
        self.extractVersion(line)
        self.extractTimeLimitReached(line)
    
    def reset(self):
        self.data = {}
        self.addData(Experiment.Key_Solver, self.solverId)
#         
    
###############################################################
##################### DERIVED Classes #########################
###############################################################
  
class SCIPSolver(Solver):
      
    def __init__(self):
        super(Solver, self).__init__(solverID="SCIP", 
                                     recognition_pattern="SCIP version ", 
                                     primalbound_pattern='^Primal Bound       :', 
                                     primalbound_lineindices=3, 
                                     dualbound_pattern="^Dual Bound         :", 
                                     dualbound_lineindices=-1, 
                                     solvingtimer_pattern="^Solving Time \(sec\) :", 
                                     solvingtime_lineindices=-1,
                                     version_pattern='SCIP version',
                                     version_lininedices=2,
                                     timelimitreached_pattern=re.compile(r'\[(.*) (reached|interrupt)\]'), 
                                     timelimitreached_expression=re.compile(r'^SCIP Status        :'))
    
    def extractOptionalInformation(self, line):
        self.extractPath(line)
        
    def extractVersion(self, line):
        '''
        handles more than just the version

        SCIP version 3.1.0.1 [precision: 8 byte] [memory: block] [mode: debug] [LP solver: SoPlex 2.0.0.1] [GitHash: 825e268-dirty]
        '''
        if re.search(self.version_pattern, line):
            version = line.split()[2]
            self.addData(Experiment.Key_Version, version)
            for keyword in ["mode", "LP solver", "GitHash"]:
                data = re.search(r"\[%s: ([\w .-]+)\]" % keyword, line)
                if data:
                    self.addData(keyword if keyword != "LP solver" else "LPSolver", data.groups()[0])

    def extractPath(self, line):
        if line.startswith('loaded parameter file'):
                absolutesettingspath = line[len('loaded parameter file '):].strip('<>')
                self.addData(Experiment.Key_SettingsPathAbsolute, absolutesettingspath)
                settings = os.path.basename(absolutesettingspath)
                settings = os.path.splitext(settings)[0]

class GurobiSolver(Solver):
      
    def __init__(self):
        super(Solver, self).__init__(solverID="GUROBI", 
                                     recognition_pattern="Gurobi Optimizer version", 
                                     primalbound_pattern='^Best objective ', 
                                     primalbound_lineindices=2, 
                                     dualbound_pattern='^Best objective', 
                                     dualbound_lineindices=5, 
                                     solvingtimer_pattern="Explored ", 
                                     solvingtime_lineindices=-2,
                                     version_pattern="Gurobi Optimizer version",
                                     version_lininedices=3,
                                     timelimitreached_pattern=re.compile(r'^(Time limit) reached'), 
                                     timelimitreached_expression=re.compile(r'^Time limit reached'))
          
class CplexSolver(Solver):
      
    def __init__(self):
        super(Solver, self).__init__(solverID="CPLEX", 
                                     recognition_pattern="Welcome to IBM(R) ILOG(R) CPLEX(R) Interactive Optimizer", 
                                     primalbound_pattern='^MIP -.*Objective = ', 
                                     primalbound_lineindices=-1, 
                                     dualbound_pattern='(^Current MIP best bound =|^MIP - Integer optimal)', 
                                     dualbound_lineindices=5, 
                                     solvingtimer_pattern="Solution time =", 
                                     solvingtime_lineindices=3,
                                     version_pattern="Welcome to IBM(R) ILOG(R) CPLEX(R)",
                                     version_lininedices=-1)
          
    def extractOptionalInformation(self, line):
        self.extractSettings(line)
        
    def extractSettings(self, line):
        if "CPLEX> Non-default parameters written to file" in line:
                self.addData(Experiment.Key_Settings, line.split('.')[-3])
    
class CbcSolver(Solver):
      
    def __init__(self):
        # TODO primal and dual bound, version?
        super(Solver, self).__init__(solverID="CBC", 
                                     recognition_pattern="FICO Xpress-Optimizer", 
                                     solvingtimer_pattern="Coin:Total time \(CPU seconds\):", 
                                     solvingtime_lineindices=4,
                                     version_pattern="Version:",
                                     version_lininedices=-1)
          
class XpressSolver(Solver):
      
    def __init__(self):
        super(Solver, self).__init__(solverID="XPRESS", 
                                     recognition_pattern="Welcome to the CBC MILP Solver",
                                     primalbound_pattern="Best integer solution found is", 
                                     primalbound_lineindices=-1,
                                     dualbound_pattern="Best bound is", 
                                     dualbound_lineindices=-1, 
                                     solvingtimer_pattern=" \*\*\* Search ", 
                                     solvingtime_lineindices=5,
                                     version_pattern="FICO Xpress Optimizer",
                                     version_lininedices=4)
          
class CouenneSolver(Solver):
      
    def __init__(self):
        super(Solver, self).__init__(solverID="Couenne", 
                                     recognition_pattern=" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization", 
                                     primalbound_pattern="^Upper bound:", 
                                     primalbound_lineindices=2,
                                     dualbound_pattern='^Lower Bound:', 
                                     dualbound_lineindices=2,
                                     solvingtimer_pattern="^Total time:", 
                                     solvingtime_lineindices=2,
                                     version_pattern=" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization",
                                     version_lininedices=-1)

