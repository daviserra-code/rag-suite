# Jira MCP Integration

This integration connects the Shopfloor Copilot to Atlassian Jira using the Model Context Protocol (MCP).

## Features

### Ticket Insights Dashboard
- **Sprint Overview**: Real-time sprint metrics with visual progress tracking
- **Issue Tracking**: List of sprint issues with status, priority, and assignees
- **AI-Powered Insights**: Pattern detection, blocker alerts, and trend analysis
- **Export Options**: CSV and PDF reports for sprint data
- **Historical Analytics**: PostgreSQL tables for tracking metrics over time

## Setup

### 1. Get Jira API Credentials

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Shopfloor Copilot")
4. Copy the generated token

### 2. Configure Environment Variables

Add these to your `.env` file:

```bash
# Jira Configuration
ATLASSIAN_HOST=https://your-company.atlassian.net
ATLASSIAN_EMAIL=your-email@company.com
ATLASSIAN_TOKEN=your-api-token-here
JIRA_MCP_URL=http://jira-mcp:3000/mcp
```

### 3. Start the Services

```bash
docker-compose up -d
```

The Jira MCP server will be available at http://localhost:3000

### 4. Configure Project Key

1. Open Shopfloor Copilot: http://localhost:8010
2. Navigate to "Ticket Insights" tab
3. Enter your Jira project key (e.g., "SHOP", "PROD", "MFG")
4. Click "Refresh" to load data

## Usage

### Viewing Sprint Data

The dashboard automatically loads your active sprint with:
- Total issues, To Do, In Progress, Done, Blocked counts
- Visual progress bar showing completion percentage
- List of all sprint issues with details

### AI Insights

The system analyzes your tickets to identify:
- **Issue Type Trends**: Which types of issues are most common
- **Priority Alerts**: When high-priority issues exceed normal thresholds
- **Blocker Tracking**: Issues stuck in blocked state with age

### Exporting Reports

- **CSV Export**: Issue list with all details for spreadsheet analysis
- **PDF Export**: Professional report with metrics, progress, and top issues

### Historical Analytics

The system stores daily snapshots of ticket metrics in PostgreSQL:
- `ticket_snapshots`: Daily metrics per project/sprint
- `issue_events`: Status changes, assignments, blocks
- `ticket_patterns`: AI-identified recurring patterns
- `sprint_velocity`: Team velocity across sprints

## Database Schema

### Main Tables

```sql
ticket_snapshots     -- Daily metric snapshots
issue_events         -- Event log for state changes
downtime_tickets     -- Link tickets to production downtime
ticket_patterns      -- AI pattern detection results
sprint_velocity      -- Sprint completion metrics
```

### Useful Views

```sql
recent_ticket_metrics  -- Last 30 days of metrics
active_patterns        -- Current patterns requiring attention
```

## API Reference

The Jira MCP client (`packages/jira_integration/jira_client.py`) provides:

### Issue Management
- `get_issue(issue_key)` - Get issue details
- `search_issues(jql)` - Search with JQL
- `create_issue(...)` - Create new issue
- `update_issue(...)` - Update existing issue
- `transition_issue(...)` - Change status

### Sprint Management
- `list_sprints(...)` - List active/future sprints
- `get_sprint(sprint_id)` - Get sprint details
- `get_active_sprint(...)` - Get current sprint

### Comments & Worklogs
- `add_comment(...)` - Add comment to issue
- `get_comments(issue_key)` - Get all comments
- `add_worklog(...)` - Log time spent

### Development Info
- `get_development_info(issue_key)` - Get linked PRs, commits, branches

## Integration with Production Lines

Link Jira tickets to production downtime events:

```python
from packages.jira_integration.jira_client import get_jira_client
from sqlalchemy import create_engine, text

jira = get_jira_client()
engine = create_engine(DATABASE_URL)

# Search for issues related to Line M10
result = await jira.search_issues(
    jql="project = SHOP AND text ~ 'Line M10'",
    max_results=10
)

# Link to downtime event
with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO downtime_tickets (
            downtime_event_line, downtime_event_time,
            issue_key, issue_type, issue_status, issue_priority
        ) VALUES (
            :line, :event_time, :issue_key, :issue_type, :status, :priority
        )
    """), {
        "line": "M10",
        "event_time": datetime.now(),
        "issue_key": "SHOP-123",
        "issue_type": "Bug",
        "status": "In Progress",
        "priority": "High"
    })
    conn.commit()
```

## Troubleshooting

### Connection Issues

Check if Jira MCP is running:
```bash
docker logs rag-suite-jira-mcp-1
```

### Authentication Errors

Verify your credentials:
```bash
docker exec rag-suite-jira-mcp-1 env | grep ATLASSIAN
```

### No Sprint Data

1. Verify project key is correct
2. Check if project has an active sprint
3. Ensure your Jira user has permission to view the project

### Database Connection

Check PostgreSQL connection:
```bash
docker exec -it rag-suite-postgres-1 psql -U postgres -d ragdb -c "\dt ticket_*"
```

## MCP Server Details

The Jira MCP server is based on: https://github.com/nguyenvanduocit/jira-mcp

Features:
- 20+ Jira API tools
- HTTP mode for easy integration
- Docker deployment
- Real-time data access

## Future Enhancements

- [ ] Webhook integration for real-time updates
- [ ] Predictive analytics from ticket patterns
- [ ] Auto-create tickets from downtime events
- [ ] Sprint planning tools
- [ ] Team workload balancing
- [ ] Custom dashboards per production line
