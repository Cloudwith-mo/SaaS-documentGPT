#!/bin/bash

# DocumentsGPT v5 Complete Test Suite Runner
# Runs backend, frontend, and integration tests in sequence

set -e  # Exit on any error

echo "🚀 DocumentsGPT v5 Complete Test Suite"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
BACKEND_PASSED=0
FRONTEND_PASSED=0
INTEGRATION_PASSED=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ $message${NC}"
    elif [ "$status" = "INFO" ]; then
        echo -e "${BLUE}ℹ️  $message${NC}"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    fi
}

# Check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        print_status "INFO" "Python3 found: $(python3 --version)"
        return 0
    else
        print_status "FAIL" "Python3 not found. Please install Python 3.7+"
        return 1
    fi
}

# Check if Node.js is available
check_node() {
    if command -v node &> /dev/null; then
        print_status "INFO" "Node.js found: $(node --version)"
        return 0
    else
        print_status "WARN" "Node.js not found. Frontend tests will be limited."
        return 1
    fi
}

# Install Python dependencies
install_python_deps() {
    print_status "INFO" "Installing Python dependencies..."
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_status "INFO" "Using virtual environment"
    fi
    
    # Check if requirements exist
    if [ -f "requirements-flask.txt" ]; then
        pip install -r requirements-flask.txt > /dev/null 2>&1 || {
            print_status "WARN" "Some Python packages failed to install"
        }
    fi
    
    # Install test-specific packages
    pip install requests sseclient-py > /dev/null 2>&1 || {
        print_status "WARN" "Test dependencies installation failed"
    }
    
    print_status "PASS" "Python dependencies ready"
}

# Start backend server
start_backend() {
    print_status "INFO" "Starting backend server..."
    
    # Check if Flask backend exists
    if [ -f "app.py" ]; then
        # Activate virtual environment if it exists
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        
        # Start Flask server in background
        python app.py > backend.log 2>&1 &
        BACKEND_PID=$!
        
        # Wait for server to start
        sleep 3
        
        # Check if server is running
        if curl -s http://localhost:5000/health > /dev/null 2>&1; then
            print_status "PASS" "Backend server started (PID: $BACKEND_PID)"
            return 0
        else
            print_status "FAIL" "Backend server failed to start"
            return 1
        fi
    else
        print_status "WARN" "Backend server file not found"
        return 1
    fi
}

# Run backend tests
run_backend_tests() {
    print_status "INFO" "Running backend API tests..."
    
    if [ -f "test_suite_v5.py" ]; then
        if python3 test_suite_v5.py; then
            BACKEND_PASSED=1
            print_status "PASS" "Backend tests completed"
        else
            print_status "FAIL" "Backend tests failed"
        fi
    else
        print_status "WARN" "Backend test file not found"
    fi
}

# Run frontend tests
run_frontend_tests() {
    print_status "INFO" "Running frontend tests..."
    
    if [ -f "frontend_test_v5.js" ]; then
        if command -v node &> /dev/null; then
            if node frontend_test_v5.js; then
                FRONTEND_PASSED=1
                print_status "PASS" "Frontend tests completed"
            else
                print_status "FAIL" "Frontend tests failed"
            fi
        else
            print_status "WARN" "Node.js not available, skipping frontend tests"
        fi
    else
        print_status "WARN" "Frontend test file not found"
    fi
}

# Run integration tests
run_integration_tests() {
    print_status "INFO" "Running integration tests..."
    
    if [ -f "integration_test_v5.py" ]; then
        if python3 integration_test_v5.py; then
            INTEGRATION_PASSED=1
            print_status "PASS" "Integration tests completed"
        else
            print_status "FAIL" "Integration tests failed"
        fi
    else
        print_status "WARN" "Integration test file not found"
    fi
}

# Stop backend server
stop_backend() {
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "INFO" "Stopping backend server..."
        kill $BACKEND_PID > /dev/null 2>&1 || true
        wait $BACKEND_PID > /dev/null 2>&1 || true
        print_status "PASS" "Backend server stopped"
    fi
}

# Generate test report
generate_report() {
    echo ""
    echo "📊 Test Suite Summary"
    echo "===================="
    
    local total_tests=3
    local passed_tests=$((BACKEND_PASSED + FRONTEND_PASSED + INTEGRATION_PASSED))
    local success_rate=$((passed_tests * 100 / total_tests))
    
    echo "Backend Tests:     $([ $BACKEND_PASSED -eq 1 ] && echo "✅ PASSED" || echo "❌ FAILED")"
    echo "Frontend Tests:    $([ $FRONTEND_PASSED -eq 1 ] && echo "✅ PASSED" || echo "❌ FAILED")"
    echo "Integration Tests: $([ $INTEGRATION_PASSED -eq 1 ] && echo "✅ PASSED" || echo "❌ FAILED")"
    echo ""
    echo "Overall Success Rate: $success_rate% ($passed_tests/$total_tests)"
    echo ""
    
    # Recommendations
    if [ $success_rate -eq 100 ]; then
        print_status "PASS" "All tests passed! System is ready for production."
        echo ""
        echo "🎯 Next Steps:"
        echo "  • Deploy to staging environment"
        echo "  • Run load tests with real traffic"
        echo "  • Set up monitoring and alerts"
        echo "  • Prepare production deployment"
    elif [ $success_rate -ge 67 ]; then
        print_status "WARN" "Most tests passed. Fix failing components before deployment."
        echo ""
        echo "🔧 Action Items:"
        echo "  • Review failed test logs"
        echo "  • Fix identified issues"
        echo "  • Re-run test suite"
    else
        print_status "FAIL" "Multiple test failures. System needs significant fixes."
        echo ""
        echo "🚨 Critical Actions:"
        echo "  • Review all test failures"
        echo "  • Fix core functionality issues"
        echo "  • Consider architecture review"
        echo "  • Re-test thoroughly before proceeding"
    fi
    
    # Log file locations
    echo ""
    echo "📋 Log Files:"
    echo "  • Backend logs: backend.log"
    echo "  • Test outputs: Check console above"
    
    return $((3 - passed_tests))  # Return number of failed test suites
}

# Cleanup function
cleanup() {
    print_status "INFO" "Cleaning up..."
    stop_backend
    
    # Remove log files if they exist
    [ -f "backend.log" ] && rm -f backend.log
    
    print_status "PASS" "Cleanup completed"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    # Pre-flight checks
    check_python || exit 1
    check_node  # Non-fatal
    
    # Setup
    install_python_deps
    
    # Start services
    if start_backend; then
        # Run test suites
        run_backend_tests
        run_frontend_tests
        run_integration_tests
        
        # Generate report
        generate_report
        exit_code=$?
        
        exit $exit_code
    else
        print_status "FAIL" "Cannot start backend server. Check configuration."
        exit 1
    fi
}

# Help function
show_help() {
    echo "DocumentsGPT v5 Test Suite Runner"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -b, --backend  Run only backend tests"
    echo "  -f, --frontend Run only frontend tests"
    echo "  -i, --integration Run only integration tests"
    echo ""
    echo "Examples:"
    echo "  $0                 # Run all tests"
    echo "  $0 --backend       # Run only backend tests"
    echo "  $0 -f -i          # Run frontend and integration tests"
    echo ""
}

# Parse command line arguments
BACKEND_ONLY=0
FRONTEND_ONLY=0
INTEGRATION_ONLY=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -b|--backend)
            BACKEND_ONLY=1
            shift
            ;;
        -f|--frontend)
            FRONTEND_ONLY=1
            shift
            ;;
        -i|--integration)
            INTEGRATION_ONLY=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run specific test suites if requested
if [ $BACKEND_ONLY -eq 1 ] || [ $FRONTEND_ONLY -eq 1 ] || [ $INTEGRATION_ONLY -eq 1 ]; then
    check_python || exit 1
    install_python_deps
    
    if [ $BACKEND_ONLY -eq 1 ]; then
        start_backend && run_backend_tests
    fi
    
    if [ $FRONTEND_ONLY -eq 1 ]; then
        run_frontend_tests
    fi
    
    if [ $INTEGRATION_ONLY -eq 1 ]; then
        start_backend && run_integration_tests
    fi
    
    generate_report
    exit $?
else
    # Run all tests
    main
fi