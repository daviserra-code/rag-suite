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

**Troubleshooting:**
- ❌ **Connection Failed:** Check server URL and port
- ❌ **Timeout:** Verify network connectivity
- ❌ **Authentication Error:** Check username/password (if required)

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
