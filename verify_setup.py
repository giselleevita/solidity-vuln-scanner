#!/usr/bin/env python3
"""
Quick verification script to check if setup is correct
Run this after installation to verify everything works
"""

import sys
import os

def check_imports():
    """Check if all required modules can be imported"""
    print("🔍 Checking imports...")
    try:
        from static_analyzer import StaticAnalyzer
        from app_config import get_config
        print("  ✅ Core modules imported successfully")
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def check_config():
    """Check configuration"""
    print("\n⚙️  Checking configuration...")
    try:
        config = get_config()
        print(f"  ✅ Config loaded")
        print(f"     - LLM enabled: {config.use_llm}")
        print(f"     - API port: {config.api_port}")
        return True
    except Exception as e:
        print(f"  ❌ Config error: {e}")
        return False

def test_static_analyzer():
    """Test static analyzer with a simple contract"""
    print("\n🧪 Testing static analyzer...")
    try:
        from static_analyzer import StaticAnalyzer
        
        test_code = """
        pragma solidity ^0.8.0;
        contract Test {
            function withdraw(uint256 amount) public {
                (bool success, ) = msg.sender.call{value: amount}("");
                require(success);
            }
        }
        """
        
        analyzer = StaticAnalyzer()
        result = analyzer.analyze(test_code, "Test")
        
        print(f"  ✅ Analyzer works")
        print(f"     - Found {len(result.vulnerabilities)} vulnerabilities")
        print(f"     - Risk score: {result.risk_score}")
        return True
    except Exception as e:
        print(f"  ❌ Analyzer error: {e}")
        return False

def check_env_file():
    """Check if .env file exists"""
    print("\n📄 Checking environment file...")
    if os.path.exists(".env"):
        print("  ✅ .env file exists")
        return True
    else:
        print("  ⚠️  .env file not found (using defaults)")
        print("     Tip: Copy env_example.txt to .env and configure")
        return True  # Not critical

def main():
    """Run all checks"""
    print("=" * 60)
    print("Solidity Vuln Scanner - Setup Verification")
    print("=" * 60)
    
    checks = [
        check_imports(),
        check_config(),
        test_static_analyzer(),
        check_env_file()
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All checks passed! Setup is complete.")
        print("\nNext steps:")
        print("  1. Run 'make api' to start the API server")
        print("  2. Run 'make ui' (in another terminal) to start the UI")
        print("  3. Visit http://localhost:8501 in your browser")
        return 0
    else:
        print("❌ Some checks failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

