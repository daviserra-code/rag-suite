#!/bin/bash
# ============================================================================
# init-services.sh - Initialize Shopfloor Copilot Services
# ============================================================================
# Purpose: Configure OPC Studio and load semantic mappings after startup
# Usage: ./scripts/init-services.sh
# Run this after: docker compose up -d
# ============================================================================

set -e

OPC_STUDIO_URL="${OPC_STUDIO_URL:-http://localhost:8040}"
OPC_DEMO_ENDPOINT="opc.tcp://opc-demo:4850"
MAX_RETRIES=30
RETRY_DELAY=2

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}Shopfloor Copilot Service Initialization${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

wait_for_service() {
    local url=$1
    local service_name=$2
    local retries=0
    
    echo -e "${YELLOW}Waiting for $service_name to be ready...${NC}"
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name is ready${NC}"
            return 0
        fi
        
        retries=$((retries + 1))
        if [ $retries -lt $MAX_RETRIES ]; then
            echo -e "${GRAY}  Waiting... ($retries/$MAX_RETRIES)${NC}"
            sleep $RETRY_DELAY
        fi
    done
    
    echo -e "${RED}✗ $service_name failed to start after $MAX_RETRIES attempts${NC}"
    return 1
}

# ----------------------------------------------------------------------------
# Step 1: Wait for services to be ready
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Step 1] Waiting for services...${NC}"

if ! wait_for_service "$OPC_STUDIO_URL/health" "OPC Studio"; then
    echo -e "\n${RED}Failed to initialize: OPC Studio not available${NC}"
    exit 1
fi

# ----------------------------------------------------------------------------
# Step 2: Connect OPC Studio to Demo Server
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Step 2] Connecting OPC Studio to demo server...${NC}"

connect_response=$(curl -s -X POST "$OPC_STUDIO_URL/opc/connect" \
    -H "Content-Type: application/json" \
    -d "{\"endpoint\":\"$OPC_DEMO_ENDPOINT\"}" \
    2>/dev/null || echo '{"status":"failed"}')

if echo "$connect_response" | grep -q '"status":"connected"'; then
    echo -e "${GREEN}✓ Connected to OPC server: $OPC_DEMO_ENDPOINT${NC}"
    echo -e "${GRAY}  Status: connected${NC}"
else
    echo -e "${RED}✗ Failed to connect to OPC server${NC}"
    echo -e "${YELLOW}  This is OK if you're using a different OPC server${NC}"
fi

# ----------------------------------------------------------------------------
# Step 3: Load Semantic Mappings
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Step 3] Loading semantic mappings...${NC}"

mapping_response=$(curl -s -X POST "$OPC_STUDIO_URL/mapping/load" \
    -H "Content-Type: application/json" \
    -d '{"yaml_path":"config/semantic_mappings.yaml"}' \
    2>/dev/null || echo '{"status":"failed"}')

if echo "$mapping_response" | grep -q '"status":"success"'; then
    echo -e "${GREEN}✓ Semantic mappings loaded successfully${NC}"
    
    if command -v jq >/dev/null 2>&1; then
        lines_mapped=$(echo "$mapping_response" | jq -r '.lines_mapped // empty')
        stations_mapped=$(echo "$mapping_response" | jq -r '.stations_mapped // empty')
        [ -n "$lines_mapped" ] && echo -e "${GRAY}  Lines mapped: $lines_mapped${NC}"
        [ -n "$stations_mapped" ] && echo -e "${GRAY}  Stations mapped: $stations_mapped${NC}"
    fi
else
    echo -e "${RED}✗ Failed to load semantic mappings${NC}"
fi

# ----------------------------------------------------------------------------
# Step 4: Verify Semantic Snapshot
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Step 4] Verifying semantic snapshot...${NC}"

snapshot=$(curl -s "$OPC_STUDIO_URL/semantic/snapshot" 2>/dev/null || echo '{}')

if echo "$snapshot" | grep -q '"plant"'; then
    echo -e "${GREEN}✓ Semantic snapshot available${NC}"
    
    if command -v jq >/dev/null 2>&1; then
        plant_name=$(echo "$snapshot" | jq -r '.plant.name // empty')
        line_count=$(echo "$snapshot" | jq '.lines | length' 2>/dev/null || echo "0")
        [ -n "$plant_name" ] && echo -e "${GRAY}  Plant: $plant_name${NC}"
        [ "$line_count" -gt 0 ] && echo -e "${GRAY}  Lines: $line_count${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Semantic snapshot exists but no plant data${NC}"
fi

# ----------------------------------------------------------------------------
# Step 5: Test OPC Browse
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Step 5] Testing OPC browse...${NC}"

browse_response=$(curl -s "$OPC_STUDIO_URL/opc/browse?nodeId=ns=0;i=85" 2>/dev/null || echo '{}')

if echo "$browse_response" | grep -q '"children"'; then
    if command -v jq >/dev/null 2>&1; then
        node_count=$(echo "$browse_response" | jq '.children | length' 2>/dev/null || echo "0")
        if [ "$node_count" -gt 0 ]; then
            echo -e "${GREEN}✓ OPC browse working ($node_count nodes found)${NC}"
        else
            echo -e "${YELLOW}⚠ OPC browse returned no nodes (may not be connected)${NC}"
        fi
    else
        echo -e "${GREEN}✓ OPC browse working${NC}"
    fi
else
    echo -e "${RED}✗ OPC browse failed${NC}"
fi

# ----------------------------------------------------------------------------
# Step 6: Check Ollama Model
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Step 6] Checking Ollama model...${NC}"

if docker exec shopfloor-ollama ollama list >/dev/null 2>&1; then
    models=$(docker exec shopfloor-ollama ollama list 2>/dev/null | grep -i llama || echo "")
    if [ -n "$models" ]; then
        echo -e "${GREEN}✓ Ollama models installed:${NC}"
        echo "$models" | while read -r line; do
            echo -e "${GRAY}  $line${NC}"
        done
    else
        echo -e "${YELLOW}⚠ No Llama models found in Ollama${NC}"
        echo -e "${YELLOW}  Run: docker exec shopfloor-ollama ollama pull llama3.2:3b${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Could not check Ollama (container may not be running)${NC}"
fi

# ----------------------------------------------------------------------------
# Step 7: Check PostgreSQL Client (Optional)
# ----------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[Step 7] Checking PostgreSQL client...${NC}"

if command -v psql >/dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL client (psql) is installed${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL client (psql) not found${NC}"
    echo -e "${GRAY}  This is optional. Install with: sudo apt install postgresql-client${NC}"
    echo -e "${GRAY}  Or use Docker: docker exec shopfloor-postgres psql -U postgres -d ragdb${NC}"
fi

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo ""
echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}Initialization Complete!${NC}"
echo -e "${CYAN}======================================${NC}"
echo -e "\n${GREEN}Your Shopfloor Copilot system is ready.${NC}"
echo -e "${CYAN}Run smoke tests: ./scripts/SMOKE_TEST.sh${NC}\n"
