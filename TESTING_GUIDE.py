#!/usr/bin/env python3
"""
Complete testing guide for BMI MCP Server
This script demonstrates all testing methods
"""


def print_testing_guide():
    """Print comprehensive testing instructions"""
    print("🧪 BMI MCP Server Testing Guide")
    print("=" * 50)

    print("\n✅ RECOMMENDED: Test with MCP Client (stdio mode)")
    print("-" * 40)
    print("This is the standard way to test MCP servers:")
    print()
    print("1. Run the test script:")
    print("   ./venv/bin/python test_bmi_server.py")
    print()
    print("2. Or manually with individual commands:")
    print("   # List tools")
    print(
        "   echo '{\"method\": \"tools/list\", \"params\": {}}' | ./venv/bin/python bmi_server.py")
    print()

    print("\n🔧 Test Individual Functions")
    print("-" * 40)
    print("Test the BMI calculation directly:")
    print()
    print("python3 -c \"")
    print("from bmi_server import calculate_bmi")
    print("print(f'BMI for 70kg, 1.75m: {calculate_bmi(70.0, 1.75):.2f}')")
    print("print(f'BMI for 85kg, 1.80m: {calculate_bmi(85.0, 1.80):.2f}')")
    print("\"")

    print("\n🌐 Test Web/SSE Mode (Advanced)")
    print("-" * 40)
    print("Note: SSE mode is mainly for web integrations")
    print()
    print("1. Start server in SSE mode:")
    print("   ./venv/bin/python bmi_server.py --sse")
    print()
    print("2. In another terminal, test endpoints:")
    print("   curl http://127.0.0.1:8000/sse")
    print("   # or")
    print("   python test_web_server.py")

    print("\n📋 Manual Testing Examples")
    print("-" * 40)
    print("BMI Categories:")
    examples = [
        (50, 1.60, "Underweight", "< 18.5"),
        (70, 1.75, "Normal", "18.5-24.9"),
        (85, 1.70, "Overweight", "25-29.9"),
        (100, 1.75, "Obese", "> 30")
    ]

    for weight, height, category, range_text in examples:
        bmi = weight / (height ** 2)
        print(
            f"   {weight}kg, {height}m → BMI: {bmi:.1f} ({category}) {range_text}")

    print("\n🔍 Troubleshooting")
    print("-" * 40)
    print("• If 'pyodbc' error: Install unixODBC → brew install unixodbc")
    print("• If 'mcp not found': Install in venv → pip install 'mcp[cli]'")
    print("• If paths don't work: Use full paths to venv/bin/python")
    print("• For SQL testing: Update connection string in query_sql_server()")

    print("\n🎯 Quick Test Command")
    print("-" * 40)
    print("Run this for a quick verification:")
    print("./venv/bin/python test_bmi_server.py")


def quick_test():
    """Run a quick test if imported as module"""
    print("\n🚀 Running Quick Test...")
    try:
        # Test importing the server
        import sys
        sys.path.append(
            '/Users/balachandarramalingam/Projects/TestMCPServer-SSEinPython/TestMCPServer-SSEinPython')
        from bmi_server import calculate_bmi

        # Test BMI calculation
        bmi = calculate_bmi(70.0, 1.75)
        print(f"✅ BMI calculation works: {bmi:.2f}")

        # Test pyodbc import
        import pyodbc
        print("✅ pyodbc import successful")

        print("✅ All basic tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    print_testing_guide()

    # Ask if user wants to run quick test
    try:
        response = input("\n🤔 Run quick test now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            quick_test()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
