#!/bin/bash
# ============================================================================
# SMOKE_TEST.sh - Shopfloor Copilot Smoke Test Suite (Linux/macOS)
# ============================================================================
# Purpose: Quick automated health checks for production deployment
# Usage: ./scripts/SMOKE_TEST.sh
# Requirements: curl, docker, docker-compose
# Optional: jq (for JSON parsing), psql (for database checks)
# ============================================================================

set -e

# Configuration from environment or defaults
SHOPFLOOR_API_URL="${SHOPFLOOR_API_URL:-http://localhost:8010}"
OPC_STUDIO_URL="${OPC_STUDIO_URL:-http://localhost:8040}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-ragdb}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Helper functions
log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASS_COUNT++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAIL_COUNT++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARN_COUNT++))
}

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Test HTTP endpoint
test_endpoint() {
    local url=$1
    local test_name=$2
    local expected_status=${3:-200}
    
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$http_code" = "$expected_status" ]; then
        log_pass "$test_name (HTTP $http_code)"
        return 0
    else
        log_fail "$test_name (HTTP $http_code, expected $expected_status)"
        return 1
    fi
}

# Test JSON endpoint with key validation
test_json_endpoint() {
    local url=$1
    local test_name=$2
    local expected_key=$3
    
    response=$(curl -s "$url" 2>/dev/null)
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$http_code" != "200" ]; then
        log_fail "$test_name (HTTP $http_code)"
        return 1
    fi
    
    if [ -n "$expected_key" ]; then
        if command -v jq >/dev/null 2>&1; then
            if echo "$response" | jq -e ".$expected_key" >/dev/null 2>&1; then
                log_pass "$test_name"
                return 0
            else
                log_fail "$test_name - Missing expected key: $expected_key"
                return 1
            fi
        else
            # Basic grep check if jq not available
            if echo "$response" | grep -q "\"$expected_key\""; then
                log_pass "$test_name"
                return 0
            else
                log_fail "$test_name - Missing expected key: $expected_key"
                return 1
            fi
        fi
    else
        log_pass "$test_name"
        return 0
    fi
}

# Test POST endpoint
test_post_endpoint() {
    local url=$1
    local test_name=$2
    local body=$3
    local expected_status=${4:-200}
    
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$body" \
        2>/dev/null || echo "000")
    
    if [ "$http_code" = "$expected_status" ]; then
        log_pass "$test_name (HTTP $http_code)"
        return 0
    else
        log_fail "$test_name (HTTP $http_code, expected $expected_status)"
        return 1
    fi
}

# ============================================================================
# Main Test Execution
# ============================================================================

echo ""
echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}Shopfloor Copilot Smoke Test Suite${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

log_info "Configuration:"
log_info "  Shopfloor API: $SHOPFLOOR_API_URL"
log_info "  OPC Studio:    $OPC_STUDIO_URL"
log_info "  Database:      ${POSTGRES_USER}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
echo ""

# ----------------------------------------------------------------------------
# Layer 0: Docker Services
# ----------------------------------------------------------------------------
echo -e "${YELLOW}[Layer 0] Docker Services${NC}"
echo "-----------------------------------"

if command -v docker >/dev/null 2>&1; then
    if docker compose ps >/dev/null 2>&1; then
        running_count=$(docker compose ps --filter "status=running" --format json 2>/dev/null | grep -c "Service" || echo "0")
        total_count=$(docker compose ps --format json 2>/dev/null | grep -c "Service" || echo "0")
        
        if [ "$running_count" = "$total_count" ] && [ "$total_count" -gt 0 ]; then
            log_pass "Docker Compose: $running_count/$total_count containers running"
        elif [ "$total_count" -gt 0 ]; then
            log_warn "Docker Compose: $running_count/$total_count containers running"
        else
            log_fail "Docker Compose: No containers found"
        fi
    else
        log_fail "Docker Compose: Unable to query status"
    fi
else
    log_warn "docker command not found - skipping container checks"
fi

# ----------------------------------------------------------------------------
# Layer 1: Health Endpoints
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Layer 1] Health Endpoints${NC}"
echo "-----------------------------------"

test_json_endpoint "$OPC_STUDIO_URL/health" "OPC Studio Health" "ok"
test_json_endpoint "$SHOPFLOOR_API_URL/health" "Shopfloor API Health" "status"
test_endpoint "$SHOPFLOOR_API_URL/" "Shopfloor UI Landing Page"

# ----------------------------------------------------------------------------
# Layer 2: OPC Explorer (Sprint 1)
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Layer 2] OPC Explorer${NC}"
echo "-----------------------------------"

response=$(curl -s "$OPC_STUDIO_URL/opc/browse?nodeId=ns=0;i=85" 2>/dev/null || echo "{}")
if command -v jq >/dev/null 2>&1; then
    child_count=$(echo "$response" | jq '.children | length' 2>/dev/null || echo "0")
    if [ "$child_count" -gt 0 ]; then
        log_pass "OPC Browse Root Node ($child_count children)"
    else
        log_warn "OPC Browse returned no children (may not be connected)"
    fi
else
    if echo "$response" | grep -q "children"; then
        log_pass "OPC Browse Root Node"
    else
        log_warn "OPC Browse - may not be connected (install jq for better validation)"
    fi
fi

# ----------------------------------------------------------------------------
# Layer 3: Semantic Mapping (Sprint 2)
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Layer 3] Semantic Mapping${NC}"
echo "-----------------------------------"

snapshot=$(curl -s "$OPC_STUDIO_URL/semantic/snapshot" 2>/dev/null || echo "{}")
if command -v jq >/dev/null 2>&1; then
    plant=$(echo "$snapshot" | jq '.plant' 2>/dev/null)
    if [ "$plant" != "null" ] && [ -n "$plant" ]; then
        log_pass "Semantic Snapshot Available"
        
        line_count=$(echo "$snapshot" | jq '.lines | length' 2>/dev/null || echo "0")
        if [ "$line_count" -gt 0 ]; then
            log_pass "  - Found $line_count mapped lines"
        else
            log_warn "Semantic Snapshot has no mapped lines"
        fi
    else
        log_fail "Semantic Snapshot missing plant data"
    fi
else
    if echo "$snapshot" | grep -q "plant"; then
        log_pass "Semantic Snapshot Available (install jq for detailed validation)"
    else
        log_warn "Semantic Snapshot - may not be configured"
    fi
fi

# ----------------------------------------------------------------------------
# Layer 4: Database Views (Phase B)
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Layer 4] Database Runtime Views${NC}"
echo "-----------------------------------"

if command -v psql >/dev/null 2>&1; then
    export PGPASSWORD="$POSTGRES_PASSWORD"
    
    # Test connection
    if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" >/dev/null 2>&1; then
        log_pass "Database Connection"
        
        # Check runtime views
        view_count=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
            -t -A -c "SELECT count(*) FROM information_schema.views WHERE table_schema='public' AND table_name LIKE 'v_runtime%';" \
            2>/dev/null || echo "0")
        
        if [ "$view_count" -ge 3 ]; then
            log_pass "Runtime Views Exist (count: $view_count)"
        else
            log_warn "Runtime Views: Expected 3+, found $view_count"
        fi
        
        # Check recent data
        data_count=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
            -t -A -c "SELECT count(*) FROM oee_line_shift WHERE date >= CURRENT_DATE - INTERVAL '1 day';" \
            2>/dev/null || echo "0")
        
        if [ "$data_count" -gt 50 ]; then
            log_pass "Recent OEE Data ($data_count rows in last 24h)"
        else
            log_warn "Recent OEE Data: Only $data_count rows in last 24h (expected >50)"
        fi
    else
        log_fail "Database Connection Failed"
    fi
    
    unset PGPASSWORD
else
    log_warn "psql not found - skipping database tests (install PostgreSQL client)"
fi

# ----------------------------------------------------------------------------
# Layer 5: Diagnostics (Sprint 3)
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Layer 5] Diagnostics Explainability${NC}"
echo "-----------------------------------"

diag_body='{"scope":"line","id":"A01"}'
diag_response=$(curl -s -X POST "$SHOPFLOOR_API_URL/api/diagnostics/explain" \
    -H "Content-Type: application/json" \
    -d "$diag_body" \
    2>/dev/null || echo "{}")

http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$SHOPFLOOR_API_URL/api/diagnostics/explain" \
    -H "Content-Type: application/json" \
    -d "$diag_body" \
    2>/dev/null || echo "000")

if [ "$http_code" = "200" ]; then
    required_fields=("what" "why" "what_to_do" "checklist" "citations")
    all_present=true
    
    for field in "${required_fields[@]}"; do
        if ! echo "$diag_response" | grep -q "\"$field\""; then
            all_present=false
            break
        fi
    done
    
    if [ "$all_present" = true ]; then
        log_pass "Diagnostics Response Structure Complete"
        
        if command -v jq >/dev/null 2>&1; then
            citation_count=$(echo "$diag_response" | jq '.citations | length' 2>/dev/null || echo "0")
            if [ "$citation_count" -gt 0 ]; then
                log_pass "  - Citations Present ($citation_count sources)"
            else
                log_warn "  - No Citations (grounding may be weak)"
            fi
            
            runtime_available=$(echo "$diag_response" | jq '.runtime_available' 2>/dev/null || echo "null")
            if [ "$runtime_available" != "null" ]; then
                log_pass "  - Runtime Status: $runtime_available"
            fi
        else
            log_pass "  - Structure validated (install jq for detailed checks)"
        fi
    else
        log_fail "Diagnostics Response Missing Required Fields"
    fi
elif [ "$http_code" = "500" ] || [ "$http_code" = "503" ]; then
    # Check if error is due to Ollama being unavailable
    if echo "$diag_response" | grep -qi "ollama"; then
        log_warn "Diagnostics Endpoint - Ollama LLM not available (service may be starting or disabled)"
    else
        log_fail "Diagnostics Endpoint (HTTP $http_code)"
    fi
else
    log_fail "Diagnostics Endpoint (HTTP $http_code)"
fi

# ----------------------------------------------------------------------------
# Layer 6: Regression - Key Endpoints
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Layer 6] Regression Tests${NC}"
echo "-----------------------------------"

test_endpoint "$SHOPFLOOR_API_URL/analytics/kpi" "KPI Dashboard Page"
test_endpoint "$SHOPFLOOR_API_URL/operations/live" "Live Monitoring Page"
test_endpoint "$SHOPFLOOR_API_URL/connectivity/opc-explorer" "OPC Explorer Page"
test_endpoint "$SHOPFLOOR_API_URL/maintenance/diagnostics" "Diagnostics Hub Page"

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo ""
echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}Test Summary${NC}"
echo -e "${CYAN}======================================${NC}"
echo -e "${GREEN}PASS: $PASS_COUNT${NC}"
echo -e "${RED}FAIL: $FAIL_COUNT${NC}"
echo -e "${YELLOW}WARN: $WARN_COUNT${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

# Exit with failure code if any tests failed
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}SMOKE TEST FAILED - $FAIL_COUNT critical failures${NC}"
    exit 1
elif [ $WARN_COUNT -gt 0 ]; then
    echo -e "${YELLOW}SMOKE TEST PASSED WITH WARNINGS - $WARN_COUNT warnings${NC}"
    exit 0
else
    echo -e "${GREEN}SMOKE TEST PASSED - All checks successful!${NC}"
    exit 0
fi
