# Testing agents in Vigilance Operations

This guide shows the quickest way to register an agent and exercise it through the proxy for testing.

## 1. Start the application

Make sure the backend and frontend are running.

```bash
docker compose up -d --build
```

Or use the manual startup flow from the main guide.

## 2. Create an admin account

If the database is new, create an admin user first.

```bash
cd backend
python create_admin.py
```

Enter an email and a strong password.

## 3. Log in as an admin

The admin login endpoint accepts form data and sets auth cookies.

```bash
curl -sS -c cookies.txt -X POST http://localhost:8000/v1/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'username=you@example.com&password=YourStrongPassword123!'
```

If the login succeeds, the response will include the auth cookies in `cookies.txt`.

## 4. Register an agent

Create an agent through the admin endpoint. This requires the admin session cookie.

```bash
curl -sS -b cookies.txt -X POST http://localhost:8000/v1/admin/agents \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Test Agent",
    "agent_id": "test-agent-1"
  }'
```

The response includes:

- `agent_id`
- `api_key`

Save the returned API key. You will use it in the next step.

Example response:

```json
{
  "message": "Agent created",
  "api_key": "sk-...",
  "agent_id": "test-agent-1"
}
```

## 5. Send a test request through the proxy

Call the proxy endpoint with the agent headers.

```bash
curl -sS -X POST http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'X-Agent-ID: test-agent-1' \
  -H 'X-API-Key: sk-YOUR_GENERATED_KEY' \
  -H 'X-Agent-Type: test' \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Say hello from the test agent."}
    ],
    "stream": false
  }'
```

If the proxy is configured correctly and the upstream API key is available, you should receive a normal chat completion response.

## 6. Try a streaming request

You can also test streaming mode.

```bash
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'X-Agent-ID: test-agent-1' \
  -H 'X-API-Key: sk-YOUR_GENERATED_KEY' \
  -H 'X-Agent-Type: test' \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Stream a short greeting."}
    ],
    "stream": true
  }'
```

## 7. Verify that telemetry was recorded

After sending requests, you can inspect the agent logs or telemetry from the API.

### List agent metrics

```bash
curl -sS -b cookies.txt http://localhost:8000/v1/agents/metrics
```

### View agent logs

```bash
curl -sS -b cookies.txt http://localhost:8000/v1/agents/test-agent-1/logs?limit=10
```

You can also open the dashboard and check the Agents or Telemetry sections.

## 8. Suspend the agent for testing

To test the kill-switch behavior, suspend the agent from the admin endpoint.

```bash
curl -sS -b cookies.txt -X PATCH http://localhost:8000/v1/admin/agents/test-agent-1/status \
  -H 'Content-Type: application/json' \
  -d '{"status": "suspended"}'
```

After that, any request using that agent ID and API key should return a 403 error.

## 9. Common issues

- 401 Unauthorized: the API key is wrong, the agent ID is wrong, or the agent is inactive.
- 403 Forbidden: the agent was suspended or the admin session is missing.
- 500 or upstream errors: check the backend logs and confirm that the environment variable for the upstream API key is set.

## 10. Recommended test flow

For a simple smoke test, use this sequence:

1. create an admin account
2. log in
3. register one agent
4. call the proxy once with the generated API key
5. verify logs and telemetry
6. suspend the agent and confirm the block
