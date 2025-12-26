# Chapter 4: OPC Explorer - Real-Time Monitoring

**Sprint:** 1  
**Feature:** UAExpert-like OPC UA client  
**Tab:** 15 (OPC Explorer)

---

## Overview

The OPC Explorer provides a **professional-grade OPC UA client** interface for browsing, monitoring, and interacting with OPC UA servers in real-time. It mimics the functionality of industrial tools like Unified Automation's UAExpert.

### Key Capabilities
- ✅ Connect to any OPC UA server
- ✅ Browse hierarchical node tree
- ✅ Read/write node values
- ✅ Monitor live value changes
- ✅ Maintain watchlist of important nodes
- ✅ View node metadata (data type, access level, etc.)

---

## Getting Started

### Accessing OPC Explorer

1. Open Shopfloor Copilot: http://localhost:8010
2. Navigate to **Tab 15: OPC Explorer**
3. You'll see three main sections:
   - **Connection Panel** (top)
   - **Browse Tree** (left)
   - **Node Inspector & Watchlist** (right)

---

## Tutorial: Connecting to OPC Server

### Step 1: Enter Server URL

![Connection Panel](screenshots/opc-explorer-connection.png)

In the **Connection Panel**:
```
Server URL: opc.tcp://opc-demo:4850
```

**Default URLs:**
- **Demo Server:** `opc.tcp://opc-demo:4850` (built-in simulation)
- **External Server:** `opc.tcp://<ip-address>:<port>`

### Step 2: Click Connect

Click the **Connect** button. You should see:
- Status changes to: ✅ **Connected to opc.tcp://opc-demo:4850**
- Browse tree populates with root nodes
- Connection indicator turns green

---

### ✨ Connection Improvements (v0.3.1)

**What's New:** Enhanced connection reliability, better timeout handling, and helpful error messages.

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/opc-explorer-connection-error.png`
**Caption:** OPC Explorer showing improved error message with troubleshooting tips
**Instructions:**
1. Navigate to OPC Explorer tab
2. Stop OPC Demo container: `docker stop opc-demo`
3. Try to connect to show error message
4. Capture error notification with troubleshooting tips
5. Restart container: `docker start opc-demo`

**Improvements:**

#### 1. Extended Timeout (10s → 15s)
**Before:** Connection attempts timed out after 10 seconds  
**After:** Extended to 15 seconds to accommodate slower networks

**Why:** Some OPC servers take longer to respond, especially:
- During startup (first connection)
- On slow networks
- When server is under heavy load
- Virtual machines or containers

#### 2. Better Error Messages

**Before (v0.3.0):**
```
❌ Connection failed
```

**After (v0.3.1):**
```
❌ Connection Failed

Could not connect to OPC server within 15 seconds.

🔍 Troubleshooting Tips:
• Check that OPC Demo container is running: docker ps
• Verify endpoint URL is correct: opc.tcp://opc-demo:4850
• Check network connectivity between containers
• Ensure firewall allows port 4850
• Try increasing timeout if server is slow to respond

💡 Common Solutions:
• Restart OPC Demo: docker restart opc-demo
• Check Docker network: docker network inspect rag-suite_default
• Verify service health: docker logs opc-demo
```

#### 3. Specific Timeout Exception

**Technical Details:**

File: `apps/shopfloor_copilot/screens/opc_explorer.py`

```python
# Connection function with improved error handling
async def connect_to_server():
    try:
        client = Client(server_url, timeout=15)  # Increased from 10s
        await client.connect()
        
        # Success notification
        ui.notify(
            '✅ Connected successfully',
            type='positive',
            position='top',
            timeout=3000
        )
        
        connection_status.set_text('✅ Connected')
        connection_status.classes('text-green-600 font-bold')
        
    except asyncio.TimeoutError:
        # Specific timeout handling
        error_msg = (
            "❌ Connection Failed\n\n"
            "Could not connect to OPC server within 15 seconds.\n\n"
            "🔍 Troubleshooting Tips:\n"
            "• Check Docker services: docker ps | grep opc\n"
            "• Verify endpoint URL is correct\n"
            "• Check network connectivity\n"
            "• Try increasing timeout if server is slow\n\n"
            "💡 Quick Fix:\n"
            "docker restart opc-demo"
        )
        
        ui.notify(
            error_msg,
            type='negative',
            position='top-right',
            timeout=10000,  # Show for 10 seconds
            multi_line=True
        )
        
        connection_status.set_text('❌ Timeout (15s)')
        connection_status.classes('text-red-600 font-bold')
        
    except Exception as e:
        # Generic error handling
        error_msg = (
            f"❌ Connection Error\n\n"
            f"Error: {str(e)}\n\n"
            f"🔍 Check:\n"
            f"• Server URL format: opc.tcp://host:port\n"
            f"• Server is running and accessible\n"
            f"• Authentication if required\n\n"
            f"💡 Try: docker logs opc-demo"
        )
        
        ui.notify(
            error_msg,
            type='negative',
            position='top-right',
            timeout=10000,
            multi_line=True
        )
        
        connection_status.set_text(f'❌ Error: {type(e).__name__}')
        connection_status.classes('text-red-600 font-bold')
```

#### 4. Connection Status Indicators

**Visual Feedback:**

| Status | Indicator | Description |
|--------|-----------|-------------|
| **Not Connected** | ⚪ grey | Initial state, not attempted |
| **Connecting...** | 🔄 blue | Connection in progress |
| **Connected** | ✅ green | Successfully connected |
| **Timeout** | ⏱️ orange | Exceeded 15 second timeout |
| **Error** | ❌ red | Connection failed with error |
| **Disconnected** | 🔌 grey | Was connected, now disconnected |

#### 5. Notification Positioning

**Before:** Notifications appeared center screen (blocked content)  
**After:** Notifications appear top-right corner (non-intrusive)

```python
ui.notify(
    message='Connection status...',
    position='top-right',  # Changed from 'center'
    timeout=10000          # Show longer for errors (10s)
)
```

---

### Troubleshooting Connection Issues

#### Problem: "Connection timed out after 15 seconds"

**Possible Causes:**
1. OPC Demo container not running
2. Wrong endpoint URL
3. Network connectivity issue
4. Port 4850 blocked by firewall
5. Server overwhelmed with requests

**Solutions:**

**Step 1: Verify OPC Demo is Running**
```powershell
docker ps | findstr opc-demo
```

Expected output:
```
abc123def456   opc-demo:latest   "python server.py"   Up 2 hours   4850/tcp
```

If not running:
```powershell
docker start opc-demo
```

**Step 2: Check Endpoint URL**
```
Correct: opc.tcp://opc-demo:4850
Wrong:   opc.tcp://opc-demo:4850/demo/server  ❌ (old endpoint)
Wrong:   opc.tcp://localhost:4850              ❌ (use container name)
Wrong:   http://opc-demo:4850                  ❌ (not HTTP)
```

**Step 3: Test Network Connectivity**
```powershell
# From Shopfloor Copilot container
docker exec shopfloor ping opc-demo

# Expected:
# 64 bytes from opc-demo (172.20.0.5): icmp_seq=1 ttl=64 time=0.123 ms
```

**Step 4: Check Docker Network**
```powershell
docker network inspect rag-suite_default

# Look for:
# - opc-demo container in network
# - shopfloor container in network
# - Both on same subnet
```

**Step 5: View OPC Server Logs**
```powershell
docker logs opc-demo --tail 50

# Look for:
# - "Server started on port 4850"
# - Any error messages
# - Connection attempts
```

---

#### Problem: "Authentication required"

**If Server Requires Credentials:**

1. Click **"Advanced Options"** in connection panel
2. Enter credentials:
   ```
   Username: operator
   Password: ********
   Security Policy: Basic256Sha256
   Security Mode: SignAndEncrypt
   ```

3. Click **Connect**

**Note:** Demo server does not require authentication (anonymous allowed)

---

#### Problem: "Certificate validation failed"

**If Using Secure Connection:**

**Option 1: Accept Certificate (Development)**
1. First connection attempt will fail
2. Server certificate is automatically saved to `~/.opcua/certificates/`
3. Click **Connect** again - should succeed

**Option 2: Install Certificate (Production)**
1. Export server certificate
2. Add to trusted certificates:
   ```powershell
   cp server-cert.pem ~/.opcua/certificates/trusted/
   ```
3. Restart Shopfloor Copilot
4. Connect should succeed

---

#### Problem: "Network unreachable"

**Docker Network Issues:**

1. **Check Shopfloor container network:**
   ```powershell
   docker inspect shopfloor | findstr NetworkMode
   ```

2. **Verify both containers on same network:**
   ```powershell
   docker network inspect rag-suite_default
   ```

3. **Recreate network if needed:**
   ```powershell
   docker-compose down
   docker-compose up -d
   ```

---

### Testing Connection Reliability

**Quick Test Procedure:**

1. **Normal Connection:**
   ```
   Server URL: opc.tcp://opc-demo:4850
   Expected: Connect in 2-5 seconds ✅
   ```

2. **Wrong Port (should fail gracefully):**
   ```
   Server URL: opc.tcp://opc-demo:4851
   Expected: Timeout after 15s with helpful error ❌
   ```

3. **Wrong Host (should fail gracefully):**
   ```
   Server URL: opc.tcp://invalid-host:4850
   Expected: DNS error with helpful message ❌
   ```

4. **Malformed URL (should validate):**
   ```
   Server URL: http://opc-demo:4850
   Expected: Validation error before attempting connection ❌
   ```

**All failures should provide:**
- ✅ Clear error message
- ✅ Troubleshooting tips
- ✅ Suggested solutions
- ✅ Relevant Docker commands

---

### Best Practices

**Connection Management:**

1. **Always test connection first:**
   - Use "Test Connection" button (if available)
   - Don't proceed with operations until connected

2. **Monitor connection status:**
   - Check indicator before reading values
   - Reconnect if status shows disconnected

3. **Use meaningful server URLs:**
   ```
   Good: opc.tcp://press-line-plc:4840
   Bad:  opc.tcp://192.168.1.100:4840  (hard to remember)
   ```

4. **Document custom servers:**
   - Keep list of server URLs
   - Note authentication requirements
   - Record certificate fingerprints

---

### Troubleshooting Checklist

Before requesting support, verify:

- [ ] OPC Demo container is running (`docker ps`)
- [ ] Endpoint URL is correct (`opc.tcp://opc-demo:4850`)
- [ ] Network connectivity works (`docker exec shopfloor ping opc-demo`)
- [ ] No firewall blocking port 4850
- [ ] Docker network is healthy (`docker network ls`)
- [ ] Logs show no errors (`docker logs opc-demo`)
- [ ] Browser console has no JavaScript errors (F12 → Console)
- [ ] Tried disconnecting and reconnecting
- [ ] Restarted containers if needed (`docker restart opc-demo shopfloor`)

---

### Step 3: Verify Connection

In the connection panel, you should see:
```
Status: Connected ✅
Server: opc.tcp://opc-demo:4850
Namespace: http://torino.mes/demo
```

---

## Tutorial: Browsing the Node Tree

### Understanding the Tree Structure

The OPC UA address space is hierarchical:

```
Root
├── Objects
│   ├── Server
│   └── TORINO Plant
│       ├── Line A01
│       │   ├── ST17 - Component Staging
│       │   ├── ST18 - Motor Assembly
│       │   └── ST19 - Inverter Integration
│       ├── Line A02
│       ├── Line B01
│       └── Line C01
└── Types
```

### Step 1: Expand Root Node

![Browse Tree](screenshots/opc-explorer-tree.png)

1. Click the **▶ arrow** next to **Root**
2. You'll see child nodes appear:
   - 📁 **Objects**
   - 📁 **Types**
   - 📁 **Views**

### Step 2: Navigate to Plant Data

1. Expand **Objects**
2. Expand **TORINO Plant**
3. Expand **Line A01**
4. You'll see stations:
   - 📁 **ST17 - Component Staging**
   - 📁 **ST18 - Motor Assembly**
   - 📁 **ST19 - Inverter Integration**

### Step 3: Explore Station Tags

1. Expand **ST18 - Motor Assembly**
2. You'll see OPC tags:
   - 🔢 **Status** (String)
   - 🔢 **Temperature** (Int)
   - 🔢 **Speed** (Int)
   - 🔢 **ProductCount** (Int)
   - 🔢 **CycleTime** (Int)

### Node Icons Legend

| Icon | Type | Description |
|------|------|-------------|
| 📁 | Object | Container node (has children) |
| 🔢 | Variable | Data node (has value) |
| ⚙️ | Method | Callable function |
| 📊 | Property | Metadata attribute |

---

## Tutorial: Reading Node Values

### Step 1: Select a Node

![Node Inspector](screenshots/opc-explorer-inspector.png)

1. In the browse tree, click on a variable node (e.g., **Status**)
2. The **Node Inspector** panel will show:

```
Node Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━
Node ID: ns=2;s=A01.ST18.Status
Browse Name: Status
Display Name: Status

Value Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━
Data Type: String
Current Value: RUNNING
Timestamp: 2025-12-16 08:15:32 UTC

Access Rights:
━━━━━━━━━━━━━━━━━━━━━━━━━━
Access Level: CurrentRead
User Access Level: CurrentRead
```

### Step 2: Read Value Manually

Click the **Read Value** button to refresh:
- Value updates instantly
- Timestamp shows last read time
- Quality indicator shows "Good" or error

### Node Inspector Fields Explained

| Field | Description | Example |
|-------|-------------|---------|
| **Node ID** | Unique identifier | `ns=2;s=A01.ST18.Status` |
| **Browse Name** | Programmatic name | `Status` |
| **Display Name** | Human-readable name | `Status` |
| **Data Type** | OPC UA data type | `String`, `Int32`, `Double` |
| **Current Value** | Last known value | `RUNNING`, `52`, `23.5` |
| **Timestamp** | Last update time | `2025-12-16 08:15:32 UTC` |
| **Access Level** | Read/write permissions | `CurrentRead`, `CurrentReadWrite` |

---

## Tutorial: Using the Watchlist

### What is a Watchlist?

A watchlist lets you monitor **multiple nodes simultaneously** with automatic refresh.

### Step 1: Add Node to Watchlist

![Watchlist](screenshots/opc-explorer-watchlist.png)

1. Select a node in the browse tree (e.g., **Temperature**)
2. In the Node Inspector, click **Add to Watchlist**
3. The node appears in the **Watchlist** section below

### Step 2: Monitor Live Values

The watchlist automatically updates **every 1 second**:

```
Watchlist (Auto-refresh: 1s)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Status (A01.ST18)
   Value: RUNNING
   Updated: 2025-12-16 08:15:45

📍 Temperature (A01.ST18)
   Value: 0 °C
   Updated: 2025-12-16 08:15:45

📍 Speed (A01.ST18)
   Value: 0 %
   Updated: 2025-12-16 08:15:45

📍 CycleTime (A01.ST18)
   Value: 52 s
   Updated: 2025-12-16 08:15:45
```

### Step 3: Remove from Watchlist

Click the **❌ Remove** button next to any watchlist item.

### Watchlist Best Practices

✅ **DO:**
- Add only critical nodes you need to monitor
- Group related nodes (e.g., all signals from one station)
- Use watchlist for troubleshooting

❌ **DON'T:**
- Add hundreds of nodes (performance impact)
- Leave watchlist open when not needed
- Add static configuration nodes (they don't change)

---

## Tutorial: Writing Node Values

### Step 1: Select Writable Node

1. Navigate to a writable node (e.g., **SetPoint**)
2. Check **Access Level** in Node Inspector:
   - ✅ **CurrentReadWrite** = Writable
   - ❌ **CurrentRead** = Read-only

### Step 2: Enter New Value

![Write Value](screenshots/opc-explorer-write.png)

1. In Node Inspector, find **Write Value** section
2. Enter new value in input field:
   ```
   New Value: 85.5
   ```
3. Click **Write Value** button

### Step 3: Verify Write Success

You should see:
- ✅ **Write successful** notification
- Value updates in Node Inspector
- Timestamp reflects write time

### Write Value Validation

The system validates writes:
- **Data Type:** Must match node's data type
- **Range:** Must be within min/max bounds (if defined)
- **Access:** User must have write permission

**Error Examples:**
- ❌ Writing "abc" to Int32 → **Type mismatch error**
- ❌ Writing 150 to 0-100 range → **Out of range error**
- ❌ Writing to read-only node → **Access denied error**

---

## Advanced Features

### Subscription to Value Changes

Instead of polling, you can **subscribe** to value changes:

1. Select a node
2. Click **Subscribe** button
3. Receive notifications only when value changes

**Benefits:**
- Lower network traffic
- Instant change notification
- More efficient than polling

### Connection Management

**Auto-Reconnect:**
- If connection drops, OPC Explorer attempts reconnect every 5 seconds
- You'll see: ⚠️ **Reconnecting...**
- When restored: ✅ **Connected**

**Manual Disconnect:**
- Click **Disconnect** button
- Browse tree clears
- Watchlist pauses (but keeps nodes)

**Switching Servers:**
- Disconnect from current server
- Enter new server URL
- Click Connect

---

## Common Use Cases

### Use Case 1: Monitoring Station Status

**Scenario:** You want to watch if Station ST18 goes into fault.

**Steps:**
1. Navigate to: `Objects → TORINO Plant → Line A01 → ST18`
2. Add **Status** to watchlist
3. Keep watchlist open
4. When status changes to **FAULTED**, you'll see it instantly

### Use Case 2: Checking Cycle Time Trends

**Scenario:** Cycle times are increasing, need to monitor.

**Steps:**
1. Add **CycleTime** from multiple stations to watchlist
2. Watch values over time
3. Note which stations have increasing cycle times
4. Use AI Diagnostics to investigate (Sprint 3)

### Use Case 3: Verifying Setpoint Changes

**Scenario:** Maintenance adjusted a setpoint, verify it applied.

**Steps:**
1. Navigate to the setpoint node
2. Read current value
3. Compare to expected value
4. If incorrect, write correct value

### Use Case 4: Troubleshooting Communication

**Scenario:** Wondering if OPC server is responding.

**Steps:**
1. Connect to server
2. Browse to any variable node
3. Click **Read Value** repeatedly
4. If timestamp updates → server is alive
5. If stale/error → check network/server

---

## Performance Tips

### Optimizing Browse Performance

**Slow Tree Expansion?**
- Server may have thousands of nodes
- Expand only branches you need
- Use search (if available) instead of browsing

### Optimizing Watchlist Performance

**UI Lagging?**
- Reduce watchlist size (max 20 nodes recommended)
- Increase refresh interval (change from 1s to 5s)
- Remove nodes you're not actively watching

### Network Considerations

**High Latency Network?**
- Increase connection timeout
- Use subscription instead of polling
- Consider local OPC proxy/gateway

---

## Troubleshooting

### Problem: Cannot Connect to Server

**Symptoms:**
- ❌ Connection timeout
- ❌ Connection refused

**Solutions:**
1. **Verify server URL:**
   ```bash
   ping opc-demo
   telnet opc-demo 4850
   ```

2. **Check Docker network:**
   ```bash
   docker-compose ps
   # Ensure opc-demo and opc-studio are "Up"
   ```

3. **Check firewall:** Port 4850 must be open

4. **Verify server is running:**
   ```bash
   docker-compose logs opc-demo
   # Look for "OPC UA Server started"
   ```

### Problem: Browse Tree Not Loading

**Symptoms:**
- Connected but tree is empty
- ⏳ Loading indicator stuck

**Solutions:**
1. **Disconnect and reconnect**
2. **Check server logs:**
   ```bash
   docker-compose logs opc-studio
   # Look for browse errors
   ```
3. **Try browsing root manually:** Click on Root node

### Problem: Watchlist Not Updating

**Symptoms:**
- Values frozen in watchlist
- Timestamps not changing

**Solutions:**
1. **Check connection status:** May have disconnected
2. **Remove and re-add node:** Resets subscription
3. **Restart OPC Studio:**
   ```bash
   docker-compose restart opc-studio
   ```

### Problem: Cannot Write Value

**Symptoms:**
- ❌ Write failed error
- ❌ Access denied

**Solutions:**
1. **Verify node is writable:** Check Access Level = `CurrentReadWrite`
2. **Check data type:** Must match exactly
3. **Verify range:** Value must be within min/max
4. **Check authentication:** May need login credentials

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + R` | Refresh current node value |
| `Ctrl + W` | Add to watchlist |
| `Ctrl + D` | Disconnect |
| `↑ ↓` | Navigate tree |
| `→` | Expand node |
| `←` | Collapse node |

---

## Best Practices

### DO ✅
- Always disconnect when done
- Use watchlist for active monitoring
- Keep node paths organized
- Validate write values before submitting
- Use subscription for critical alarms

### DON'T ❌
- Leave 100+ nodes in watchlist
- Write values without understanding impact
- Browse entire tree unnecessarily
- Keep unused connections open
- Ignore connection errors

---

## Related Features

- **Semantic Signals** (Tab 16): See OPC tags transformed into semantic signals
- **AI Diagnostics** (Tab 17): Get AI explanations for OPC data
- **Live Monitoring** (Tab 1): High-level plant overview

---

**Next Chapter:** [Semantic Mapping Engine →](05-semantic-mapping.md)

**Previous Chapter:** [← Quick Start Guide](03-quick-start.md)
