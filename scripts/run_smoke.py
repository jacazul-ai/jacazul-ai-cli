#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import unittest
import sys
import os

# 🐊 Jacazul Hardened Smoke Test Runner (Firenado Pattern)
# Provides modular test execution with strict isolation.

# Add project root to sys.path to allow importing 'jacazul' and 'tests'
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.insert(0, project_root)

from tests import core_test, flow_test, security_test, test_hatch, test_switch

def smoke_suite():
    """Build the explicit test suite following the Firenado pattern."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Explicitly load modules
    suite.addTests(loader.loadTestsFromModule(core_test))
    suite.addTests(loader.loadTestsFromModule(flow_test))
    suite.addTests(loader.loadTestsFromModule(security_test))
    suite.addTests(loader.loadTestsFromModule(test_hatch))
    suite.addTests(loader.loadTestsFromModule(test_switch))
    
    return suite

def main():
    print("═══════════════════════════════════════════════════")
    print("  JACAZUL HARDENED SMOKE TEST SUITE (v1.4.0)")
    print("═══════════════════════════════════════════════════\n")
    
    # Run tests with high verbosity
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(smoke_suite())
    
    # Exit with non-zero if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()
