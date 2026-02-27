#!/usr/bin/env python
import unittest
import sys
import os

# 🐊 Jaka Hardened Smoke Test Runner (Firenado Pattern)
# Provides modular test execution with strict isolation.

# Add current directory to sys.path to allow importing the 'tests' package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests import core_test, flow_test, security_test

def smoke_suite():
    """Build the explicit test suite following the Firenado pattern."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Explicitly load modules
    suite.addTests(loader.loadTestsFromModule(core_test))
    suite.addTests(loader.loadTestsFromModule(flow_test))
    suite.addTests(loader.loadTestsFromModule(security_test))
    
    return suite

def main():
    print("═══════════════════════════════════════════════════")
    print("  JAKA HARDENED SMOKE TEST SUITE (v1.4.0)")
    print("═══════════════════════════════════════════════════\n")
    
    # Run tests with high verbosity
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(smoke_suite())
    
    # Exit with non-zero if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()
