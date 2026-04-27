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

export type AgentType = "traffic-manager" | "social-media" | "ceo" | "content-strategist" | "image-creator";

const CONTENT_AGENTS: AgentType[] = ["content-strategist", "image-creator"];

export async function chatWithAgent(
  agent: AgentType,
  message: string,
  sessionId?: string
): Promise<ChatResponse> {
  const prefix = CONTENT_AGENTS.includes(agent) ? "content" : "agents";
  const res = await fetch(`${API_URL}/${prefix}/${agent}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function clearAgentSession(sessionId: string): Promise<void> {
  await fetch(`${API_URL}/agents/session/${sessionId}`, { method: "DELETE" });
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch("http://localhost:8000/health");
    return res.ok;
  } catch {
    return false;
  }
}

export interface AdAccount {
  id: string;
  name: string;
  status: string;
  currency: string;
  amount_spent: string;
  balance: string;
}

export async function listAdAccounts(): Promise<AdAccount[]> {
  const res = await fetch(`${API_URL}/meta/accounts`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = await res.json();
  return data.accounts;
}

export interface MetaCampaign {
  id: string;
  name: string;
  status: string;
  objective: string;
  daily_budget: string;
  created_time: string;
}

export async function listCampaigns(adAccountId: string): Promise<MetaCampaign[]> {
  const res = await fetch(`${API_URL}/meta/accounts/${adAccountId}/campaigns`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = await res.json();
  return data.campaigns;
}

export interface CopyBrief {
  product: string;
  audience: string;
  objective: string;
  tone: string;
  differentials: string;
  cta_hint: string;
}

export async function generateCopy(brief: CopyBrief): Promise<{ raw_response: string }> {
  const res = await fetch(`${API_URL}/copy/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(brief),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function uploadCreative(file: File): Promise<{ public_url: string; path: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/creatives/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload error: ${res.status}`);
  return res.json();
}
