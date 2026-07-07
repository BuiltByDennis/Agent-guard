# Using Vigilance Operations Effectively

Vigilance Operations is a guardrail proxy for autonomous AI agents. It sits between your agent and upstream LLM providers so you can control cost, reduce compliance risk, inspect behavior, and stop agents when they drift outside policy.

This guide shows you how to install, configure, connect your applications, operate, and get value from the platform in a practical way.

---

## 1. What this application is for

Use this platform when you want to:

- keep AI agents from leaking sensitive data
- cap runaway spend and unexpected usage spikes
- monitor agent behavior in real time
- suspend or block agents quickly when thresholds are exceeded
- give admins a central control plane for security and operations

In short, it is not just a chat UI. It is an operational safety layer for agent-based systems.

---

## 2. Before you start

You should have:

- Docker and Docker Compose, or
- Python 3.11+, Node.js 20+, and a running PostgreSQL/Redis setup
- access to an OpenAI API key (or another compatible upstream provider if you adapt the configuration)

The repository includes Docker support, a FastAPI backend, and a Next.js dashboard. The easiest path is to run everything with Docker Compose.

---

## 3. Quick start

### Option A: Docker Compose (recommended)

From the repository root:

```bash
docker compose up -d --build
```

After startup:

- Backend API: http://localhost:8000
- Frontend dashboard: http://localhost:3000

If you need to stop everything:

```bash
docker compose down
```

### Option B: Manual startup

If you prefer running services directly:

```bash
cp .env.example .env
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then start the backend:

```bash
set -a && source ../.env && set +a
uvicorn main:app --reload --port 8000
```

In a second terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

---

## 4. Create your first admin account

The backend includes a helper script to create an admin user.

```bash
cd backend
python create_admin.py
```

When prompted, enter:

- an admin email
- a strong password

This account is what you will use to sign in to the dashboard and manage the system.

> If you are using a fresh database, create the admin account before trying to log in.

---

## 5. Log in and understand the dashboard

Open the frontend in your browser:

```text
http://localhost:3000
```

Sign in with the admin account you just created.

The main dashboard is your operations control center. Use it to:

- review overview metrics
- inspect agent activity
- investigate suspicious or costly requests
- manage users and API keys
- adjust security settings

The main sections you will use most often are:

- **Dashboard**: a high-level view of system health and agent activity
- **Agents**: list agents and inspect their performance and recent logs
- **Telemetry**: view request latency, cost, and other operational signals
- **Admin > Users**: manage access for other administrators
- **Admin > Keys**: manage API keys for agents or privileged services
- **Settings**: configure platform behavior and policies

---

## 6. How to connect your application to the proxy

This is the core integration step. Vigilance sits between your application and OpenAI. Your application must never call OpenAI directly — it calls the Vigilance proxy instead, and the proxy forwards the request on your behalf after applying all safety checks.

### Step 1 — Register your agent

Every application or service that uses the proxy must be registered as an agent. You can do this from the dashboard under **Admin > Keys**, or via the API directly.

First, obtain a JWT by logging in:

```bash
curl -X POST https://your-proxy.com/v1/auth/token \
  -d "username=admin@email.com&password=yourpassword"
```

Then create the agent using the JWT:

```bash
curl -X POST https://your-proxy.com/v1/admin/agents \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "my-customer-agent", "name": "Customer Support Bot"}'
```

The response returns a **one-time `api_key`** in the format `sk-...`. Copy and store it in a secret manager or environment variable immediately — it is not retrievable again.

```json
{
  "message": "Agent created",
  "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "agent_id": "my-customer-agent"
}
```

### Step 2 — Point your application at the proxy endpoint

Instead of calling:

```
https://api.openai.com/v1/chat/completions
```

Your application calls:

```
POST https://your-proxy.com/v1/chat/completions
```

Every request must include these three required headers:

| Header | Value | Purpose |
| :--- | :--- | :--- |
| `X-API-Key` | `sk-...` from Step 1 | Authenticates the agent |
| `X-Agent-ID` | `my-customer-agent` | Identifies which agent this is |
| `X-Agent-Type` | `support` / `qa` / `general` | Labels the agent type for telemetry |

The **request body is identical to OpenAI's format** — no changes are needed to your existing prompts or message structures.

```json
{
  "model": "gpt-4o",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}
```

### Step 3 — Example integrations

**Python (httpx)**

```python
import httpx

PROXY_URL = "https://your-proxy.com/v1/chat/completions"
AGENT_API_KEY = "sk-your-agent-key"
AGENT_ID = "my-customer-agent"

response = httpx.post(
    PROXY_URL,
    headers={
        "X-API-Key": AGENT_API_KEY,
        "X-Agent-ID": AGENT_ID,
        "X-Agent-Type": "support",
        "Content-Type": "application/json",
    },
    json={
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Summarize this ticket..."}],
        "stream": False,
    }
)
print(response.json())
```

**Python (OpenAI SDK — drop-in override)**

If you are already using the OpenAI Python SDK, you only need to override `base_url` and set default headers. No other code changes are required.

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-agent-key",          # Your Vigilance agent key, not your OpenAI key
    base_url="https://your-proxy.com/v1",
    default_headers={
        "X-Agent-ID": "my-customer-agent",
        "X-Agent-Type": "support",
    }
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Summarize this ticket..."}]
)
print(response.choices[0].message.content)
```

**Node.js / TypeScript (fetch)**

```typescript
const response = await fetch("https://your-proxy.com/v1/chat/completions", {
  method: "POST",
  headers: {
    "X-API-Key": process.env.AGENT_API_KEY!,
    "X-Agent-ID": "my-customer-agent",
    "X-Agent-Type": "support",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "gpt-4o",
    messages: [{ role: "user", content: "Hello" }],
    stream: false,
  }),
});

const data = await response.json();
console.log(data);
```

### Step 4 — What happens to every request

When your application calls the proxy, each request is automatically processed through this pipeline:

```
Your App
   │
   ▼
[1] Auth: X-API-Key + X-Agent-ID validated
   │
   ▼
[2] Suspend check: is this agent currently blocked?
   │
   ▼
[3] Request forwarded to OpenAI
   │
   ▼
[4] Firewall scan: response checked for SSNs, API keys, PII
   │  ├─ BLOCK mode  → stream/response is stopped immediately
   │  └─ SANITIZE mode → sensitive strings are redacted
   ▼
[5] Cost velocity check: has this agent breached its budget?
   │  └─ If yes → agent is auto-suspended (kill switch)
   ▼
[6] Telemetry saved asynchronously (cost, latency, tokens, status)
   │
   ▼
Your App receives the response
```

All six steps happen transparently. Your application code does not need to handle any of this — it just sends requests and reads responses exactly as it would with OpenAI directly.

### Step 5 — Monitor your application in the dashboard

After your application is sending traffic through the proxy:

- **Dashboard** — see cost, latency, and blocked requests at a glance across all agents
- **Agents → your agent name** — inspect per-agent logs, performance score, and suspension status
- **Telemetry** — drill into specific requests including payloads, latency in ms, and token counts
- **Admin → Agents** — manually suspend or unsuspend an agent at any time

### Production integration checklist

| Item | Notes |
| :--- | :--- |
| Each service gets its own `agent_id` | Enables per-agent monitoring and kill switches |
| Store `X-API-Key` in env vars or a secret manager | Never hardcode or commit it |
| Use descriptive agent names and types | Makes telemetry and incident response much easier |
| Set `FIREWALL_MODE=BLOCK` for sensitive data | Or `SANITIZE` for lower-risk workloads |
| Start with conservative cost/velocity limits | Loosen after reviewing actual traffic patterns |
| Rotate agent keys regularly | Via Admin > Keys in the dashboard |
| Revoke keys for decommissioned services | Inactive keys are an unnecessary risk surface |

---

## 7. How to register and use agents

This application works by acting as a policy layer for agent traffic. In practice, your agents should send requests through the proxy instead of calling the upstream provider directly.

When an agent calls the proxy:

1. the request is validated
2. the firewall checks for risky content
3. cost and velocity checks are applied
4. telemetry is recorded
5. the request is sent onward or blocked

### What this means for you

- Configure your agent to use the proxy endpoint for LLM requests.
- Make sure each agent has a stable identity so the system can track it correctly.
- Use agent-specific monitoring instead of looking only at aggregate traffic.

### Good practice

Give each agent a clear name and a consistent purpose. This makes telemetry, logs, and incident response much easier.

---

## 8. Use the dashboard effectively

### A. Review the dashboard first

When something seems off, start with the main dashboard:

- look for spikes in cost
- check latency changes
- identify agents that are noisy or failing often
- spot unusual traffic patterns

### B. Drill into individual agents

Open the Agents section and choose an agent. From there you can:

- inspect recent interactions
- review logs
- see whether the agent was suspended
- identify if the agent is repeatedly hitting limits or producing failures

This is the fastest way to understand the root cause of an issue.

### C. Use logs to find problems

Logs are your best source of truth when debugging. Look for:

- repeated errors
- blocked responses
- high latency
- suspicious payloads
- policy violations

If a response was blocked by the firewall, treat it as a signal that your prompts or data handling flow need review.

---

## 9. Understand the security controls

The application includes several layers of protection.

### Firewall modes

The firewall can be configured to:

- **BLOCK**: stop the stream or request immediately when sensitive content is detected
- **SANITIZE**: redact sensitive strings instead of blocking everything

Use BLOCK when you want strict compliance enforcement. Use SANITIZE when you want to preserve operation while reducing leakage risk.

### Kill switch behavior

If an agent exceeds configured budget or velocity thresholds, the system can suspend it. That is a powerful safety feature, but it should be treated as an operational control, not a substitute for good prompt and workflow design.

### Recommended policy

- Start with conservative limits
- Review violations before relaxing thresholds
- Use BLOCK for highly sensitive environments
- Use SANITIZE for lower-risk but still regulated use cases

---

## 10. Set up monitoring for real value

The application becomes much more useful when you use the telemetry data actively.

### Watch these signals

- request volume
- latency
- token usage
- cost per request
- blocked interactions
- success vs. failure rate

### How to use them

- If latency rises, inspect upstream provider issues or agent prompt complexity.
- If cost rises quickly, check prompts, loops, retries, and agent behavior.
- If a specific agent has a high block rate, review its prompts and data handling.

Telemetry is most useful when you compare trends over time rather than only looking at isolated events.

---

## 11. Manage access and permissions

Use the admin pages to manage who can operate the platform.

### Admin users

Create admin accounts only for trusted operators. Avoid sharing passwords or leaving broad access enabled for inactive users.

### Agent API keys

If your agents or internal services need to call the proxy, create and manage their keys carefully.

Good practices:

- rotate keys regularly
- revoke keys that are no longer used
- avoid embedding secrets in client-side code
- store secrets in environment variables or a secret manager

---

## 12. A practical workflow for daily use

Here is a reliable workflow for operating the platform effectively.

### Daily checklist

1. Open the dashboard and review the latest traffic and cost trends.
2. Check for any agents that were suspended or blocked.
3. Open the logs for any suspicious agent.
4. Review firewall violations and decide whether the policy should be tightened or relaxed.
5. Confirm that budgets and velocity thresholds are still appropriate for current workload.
6. If something changed, update the policy and communicate the change to the team.

### Weekly checklist

- audit admin accounts
- review API key usage
- inspect recurring incidents or repeated violations
- adjust budgets or thresholds if your workload has changed

---

## 13. Common mistakes to avoid

- Calling OpenAI directly instead of routing through the proxy
- Using the same `agent_id` for multiple distinct services
- Hardcoding the agent `api_key` in source code
- Using the system only after a problem has already occurred
- Relying on one-off logs instead of telemetry trends
- Giving every agent the same policy without considering risk
- Setting limits that are too loose and then being surprised by cost spikes
- Failing to revoke old API keys
- Treating the firewall as a replacement for application-level validation

---

## 14. Troubleshooting

### The dashboard will not load

- confirm the frontend is running on port 3000
- confirm the backend is running on port 8000
- check the browser console and backend logs for errors

### Login fails

- verify that the admin account was created successfully
- confirm the database is available
- check that the backend environment variables are valid

### My application gets a 401 Unauthorized

- confirm the `X-API-Key` header is present and correct
- confirm the `X-Agent-ID` header matches the registered agent
- verify the agent is marked as active and has not been soft-deleted

### My application gets a 403 Forbidden

- the agent may be suspended — check the dashboard under Admin > Agents
- if using a POST/PATCH/DELETE request from a browser-based client, confirm the `X-CSRF-Token` header is set correctly
- note: CSRF checks are skipped for the proxy endpoint when using `X-API-Key` auth

### Requests are being blocked unexpectedly

- inspect firewall logs
- review whether the content contains sensitive patterns
- decide whether BLOCK or SANITIZE is the better mode for your use case

### Costs are rising unexpectedly

- inspect agent prompts and loops
- look for repeated retries or excessive output length
- review the agent's recent logs and usage patterns

---

## 15. Best practices for long-term success

To use the application effectively over time:

- start with clear guardrails and review them often
- keep policies specific to each agent's risk profile
- use telemetry as a daily operational tool, not a retrospective report
- document incidents and how your team responded
- treat this platform as part of your production runtime, not just a deployment step

The more consistently you use the dashboard and logs, the more value you will get from the system.

---

## 16. Summary

If you want this application to be truly useful, use it as a real control plane for your agents:

- **Connect** your applications by registering agents and routing all LLM calls through the proxy
- **Protect** sensitive data with the firewall
- **Manage** cost and velocity with budgets and kill switches
- **Monitor** behavior in real time through the dashboard and telemetry
- **Suspend** risky agents quickly when thresholds are exceeded
- **Review** failures and learn from them

With consistent use, Vigilance Operations becomes an essential safety layer for any serious agent deployment.
