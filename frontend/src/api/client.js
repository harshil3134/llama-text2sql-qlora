export const API_BASE = "http://localhost:8000/api";

export async function submitQuery(question, schema_ddl) {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, schema_ddl, force_refresh: false })
  });
  return await res.json();
}

export async function pollTaskStatus(task_id) {
  const res = await fetch(`${API_BASE}/tasks/${task_id}`);
  if (!res.ok) {
      throw new Error(`Failed to fetch status: ${res.statusText}`);
  }
  return await res.json();
}

export function subscribeTaskEvents(taskId, onEvent, onError) {
  const eventSource = new EventSource(`${API_BASE}/tasks/${taskId}/events`);
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent(data);
      if (data.event === 'completed' || data.event === 'failed') {
        eventSource.close();
      }
    } catch (e) {
      console.error("Failed to parse SSE event data:", e);
    }
  };

  eventSource.onerror = (err) => {
    eventSource.close();
    if (onError) onError(err);
  };

  return () => {
    eventSource.close();
  };
}

export async function fetchSchemas() {
  const res = await fetch(`${API_BASE}/schemas`);
  if (!res.ok) throw new Error("Failed to fetch schemas");
  return await res.json();
}

