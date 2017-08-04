from unittest import TestSuite
from .ExperimentTest import ExperimentTest
from .EvaluationTest import EvaluationTest
from .SolverTest import SolverTest
from .ReductionIndexTest import ReductionIndexTest
from .FormatTest import FormatTest
from .PrimalDualBoundHistoryTest import PrimalDualBoundHistoryTest
import logging



test_cases = (EvaluationTest, 
              ExperimentTest, 
              SolverTest,
              FormatTest,
              PrimalDualBoundHistoryTest,
              ReductionIndexTest
              )

def load_tests(loader, tests, pattern):
    logger=logging.getLogger()
    logger.setLevel(logging.ERROR)
    suite = TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
