"use client";

import { useState, useEffect, useRef } from "react";
import { Megaphone, ChevronDown, Circle, RefreshCw } from "lucide-react";
import { AgentChat } from "@/components/agents/agent-chat";
import { CampaignTemplate } from "@/components/agents/campaign-template";
import { listAdAccounts, type AdAccount } from "@/lib/api";

const suggestions = [
  "Liste todas as minhas contas de anúncio",
  "Crie uma campanha de leads para a Gotrix, R$50/dia",
  "Mostre as campanhas ativas da Gotrix",
  "Analise a performance da conta Gotrix",
];

export default function TrafficManagerPage() {
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [selected, setSelected] = useState<AdAccount | null>(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const sendRef = useRef<((msg: string) => void) | null>(null);

  useEffect(() => {
    listAdAccounts()
      .then((data) => {
        const active = data.filter((a) => a.status === "Ativo");
        setAccounts(active);
        const gotrix = active.find((a) => a.name.toLowerCase().includes("gotrix"));
        setSelected(gotrix || active[0] || null);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const accountContext = selected
    ? `\n\n[Conta ativa: ${selected.name} | ID: ${selected.id}]`
    : "";

  return (
    <div className="flex flex-col h-screen">
      {/* Top bar */}
      <div className="px-6 py-3 border-b border-border/50 bg-background flex items-center gap-3 flex-wrap">
        <span className="text-xs text-muted-foreground font-medium">Conta Meta Ads:</span>

        {loading ? (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <RefreshCw className="w-3 h-3 animate-spin" />
            Carregando contas...
          </div>
        ) : (
          <div className="relative">
            <button
              onClick={() => setOpen(!open)}
              className="flex items-center gap-2 bg-secondary border border-border/50 rounded-lg px-3 py-1.5 text-sm hover:border-violet-500/50 transition-colors"
            >
              <Circle className="w-2 h-2 fill-emerald-400 text-emerald-400" />
              <span className="font-medium">{selected?.name || "Selecionar conta"}</span>
              {selected && <span className="text-xs text-muted-foreground">{selected.id}</span>}
              <ChevronDown className="w-3 h-3 text-muted-foreground ml-1" />
            </button>

            {open && (
              <div className="absolute top-full left-0 mt-1 w-80 bg-popover border border-border rounded-xl shadow-xl z-50 overflow-hidden">
                <div className="px-3 py-2 border-b border-border">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    Contas ativas ({accounts.length})
                  </p>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {accounts.map((acc) => (
                    <button key={acc.id} onClick={() => { setSelected(acc); setOpen(false); }}
                      className={`w-full text-left px-3 py-2.5 hover:bg-accent transition-colors flex items-center justify-between ${selected?.id === acc.id ? "bg-violet-500/10" : ""}`}>
                      <div>
                        <p className={`text-sm font-medium ${selected?.id === acc.id ? "text-violet-400" : ""}`}>{acc.name}</p>
                        <p className="text-xs text-muted-foreground">{acc.id}</p>
                      </div>
                      <span className="text-xs text-muted-foreground">{acc.currency}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Template button */}
        <div className="ml-auto">
          <CampaignTemplate onSend={(msg) => sendRef.current?.(msg)} />
        </div>
      </div>

      {/* Chat */}
      <div className="flex-1 overflow-hidden">
        <AgentChat
          agentType="traffic-manager"
          agentName="Gestor de Tráfego"
          agentDescription={`Meta Ads${selected ? ` · ${selected.name}` : ""} · Google Ads`}
          agentIcon={<Megaphone className="w-5 h-5 text-white" />}
          gradientClass="from-blue-600 to-cyan-700"
          suggestions={suggestions}
          systemContext={accountContext}
          sendRef={sendRef}
        />
      </div>
    </div>
  );
}
