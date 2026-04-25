const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  agent: string;
  response: string;
  session_id?: string;
}

export type AgentType = "traffic-manager" | "social-media" | "ceo";

export async function chatWithAgent(
  agent: AgentType,
  message: string,
  sessionId?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/agents/${agent}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch("http://localhost:8000/health");
    return res.ok;
  } catch {
    return false;
  }
}
