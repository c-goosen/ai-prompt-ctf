#!/bin/bash

# CTF Agent Evaluation Runner Script
# This script runs all password query evaluations for the CTF agents

set -e

echo "🧪 CTF Agent Evaluation Suite"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "agent.py" ]; then
    echo "❌ Error: Please run this script from the ctf/agents directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected: .../ctf/agents"
    exit 1
fi

# Check if ADK is available
if ! command -v adk &> /dev/null; then
    echo "❌ Error: ADK CLI not found. Make sure it's installed and in PATH"
    exit 1
fi

echo "📁 Working directory: $(pwd)"
echo "🔍 Available evaluation files:"
ls -la evaluations/*.json evaluations/*.test.json 2>/dev/null || echo "   No evaluation files found"

echo ""
echo "🚀 Running comprehensive evaluation set..."
echo "----------------------------------------"

# Run the comprehensive evaluation set
if [ -f "evaluations/ctf_password_tests.evalset.json" ]; then
    echo "Running: adk eval . evaluations/ctf_password_tests.evalset.json --config_file_path=evaluations/test_config.json --print_detailed_results"
    
    uv run adk eval . evaluations/ctf_password_tests.evalset.json \
        --config_file_path=evaluations/test_config.json \
        --print_detailed_results
    
    echo "✅ Comprehensive evaluation completed!"
else
    echo "❌ Error: ctf_password_tests.evalset.json not found"
    exit 1
fi

echo ""
echo "🧪 Running pytest tests..."
echo "-------------------------"

# Run pytest tests
cd evaluations
if [ -f "test_password_queries.py" ]; then
    echo "Running: pytest test_password_queries.py -v"
    uv run pytest test_password_queries.py -v
    echo "✅ Pytest tests completed!"
else
    echo "❌ Error: test_password_queries.py not found"
    cd ..
    exit 1
fi

cd ..

echo ""
echo "📊 Evaluation Summary"
echo "===================="
echo "✅ All evaluations completed successfully!"
echo ""
echo "📋 What was tested:"
echo "   • Tool trajectory: Agents call rag_tool_func with correct parameters"
echo "   • Response quality: Agents provide appropriate security responses"
echo "   • All levels (0-10): Different security behaviors per level"
echo ""
echo "🔍 To view detailed results:"
echo "   • Web UI: uv run adk web (then navigate to Eval tab)"
echo "   • Individual tests: uv run adk eval . evaluations/level_X_password_test.test.json"
echo "   • Specific cases: uv run adk eval . evaluations/ctf_password_tests.evalset.json:level_X_password_test"
echo ""
echo "📖 For more information, see: evaluations/README.md"
