"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { TrendingUp, Plus, Play, Pause, RefreshCw, DollarSign, MousePointerClick, Users, Eye, Circle, ChevronDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { listAdAccounts, listCampaigns, type AdAccount, type MetaCampaign } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const STATUS_LABEL: Record<string, { label: string; color: string }> = {
  ACTIVE:   { label: "Ativo",   color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
  PAUSED:   { label: "Pausado", color: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
  DELETED:  { label: "Deletado", color: "bg-red-500/10 text-red-400 border-red-500/20" },
  ARCHIVED: { label: "Arquivado", color: "bg-secondary text-muted-foreground" },
};

interface CampaignWithInsights extends MetaCampaign {
  daily_budget_brl?: number;
  insights?: {
    impressions: number;
    clicks: number;
    spend_brl: number;
    ctr: number;
    cpc_brl: number;
    reach: number;
    leads: number;
    cpl_brl: number | null;
  };
}

export default function CampaignsPage() {
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [selected, setSelected] = useState<AdAccount | null>(null);
  const [campaigns, setCampaigns] = useState<CampaignWithInsights[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [days, setDays] = useState(30);
  const [totals, setTotals] = useState({ spend: 0, leads: 0, active: 0 });
  const [toggling, setToggling] = useState<string | null>(null);

  useEffect(() => {
    listAdAccounts().then(data => {
      const active = data.filter(a => a.status === "Ativo");
      setAccounts(active);
      const gotrix = active.find(a => a.name.toLowerCase().includes("gotrix"));
      setSelected(gotrix || active[0] || null);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selected) return;
    fetchCampaigns(selected.id);
  }, [selected, days]);

  async function fetchCampaigns(accountId: string) {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/meta/accounts/${accountId}/campaigns?days=${days}`);
      const data = await res.json();
      setCampaigns(data.campaigns || []);
      setTotals({ spend: data.total_spend_brl || 0, leads: data.total_leads || 0, active: data.active_count || 0 });
    } catch { setCampaigns([]); }
    finally { setLoading(false); }
  }

  async function toggleStatus(campaign: CampaignWithInsights) {
    setToggling(campaign.id);
    const endpoint = campaign.status === "ACTIVE" ? "pause" : "activate";
    try {
      await fetch(`${API_URL}/meta/campaigns/${campaign.id}/${endpoint}`, { method: "PATCH" });
      if (selected) fetchCampaigns(selected.id);
    } catch {} finally { setToggling(null); }
  }

  const kpis = [
    { label: "Campanhas Ativas", value: totals.active, icon: Circle, color: "text-emerald-400", bg: "bg-emerald-500/10" },
    { label: `Investido (${days}d)`, value: `R$ ${totals.spend.toFixed(2)}`, icon: DollarSign, color: "text-violet-400", bg: "bg-violet-500/10" },
    { label: `Leads (${days}d)`, value: totals.leads, icon: Users, color: "text-blue-400", bg: "bg-blue-500/10" },
    { label: "CPL Médio", value: totals.leads > 0 ? `R$ ${(totals.spend / totals.leads).toFixed(2)}` : "—", icon: TrendingUp, color: "text-amber-400", bg: "bg-amber-500/10" },
  ];

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Campanhas</h1>
          <p className="text-muted-foreground text-sm mt-1">Métricas reais do Meta Ads</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Period selector */}
          <div className="flex gap-1 bg-secondary rounded-lg p-1">
            {[7, 14, 30].map(d => (
              <button key={d} onClick={() => setDays(d)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${days === d ? "bg-background shadow text-foreground" : "text-muted-foreground"}`}>
                {d}d
              </button>
            ))}
          </div>

          {/* Account selector */}
          <div className="relative">
            <button onClick={() => setOpen(!open)}
              className="flex items-center gap-2 bg-secondary border border-border/50 rounded-lg px-3 py-2 text-sm hover:border-violet-500/50 transition-colors">
              <Circle className="w-2 h-2 fill-emerald-400 text-emerald-400" />
              <span className="font-medium">{selected?.name || "Conta"}</span>
              <ChevronDown className="w-3 h-3 text-muted-foreground" />
            </button>
            {open && (
              <div className="absolute right-0 top-full mt-1 w-64 bg-popover border border-border rounded-xl shadow-xl z-50 overflow-hidden">
                {accounts.map(acc => (
                  <button key={acc.id} onClick={() => { setSelected(acc); setOpen(false); }}
                    className={`w-full text-left px-4 py-2.5 text-sm hover:bg-accent transition-colors ${selected?.id === acc.id ? "text-violet-400" : ""}`}>
                    {acc.name}
                  </button>
                ))}
              </div>
            )}
          </div>

          <Button onClick={() => selected && fetchCampaigns(selected.id)} variant="outline" size="sm" disabled={loading}>
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </Button>

          <Link href="/agents/traffic-manager">
            <Button className="bg-violet-600 hover:bg-violet-700" size="sm">
              <Plus className="w-4 h-4 mr-2" />Nova campanha
            </Button>
          </Link>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map(k => {
          const Icon = k.icon;
          return (
            <Card key={k.label} className="border-border/50">
              <CardContent className="pt-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground">{k.label}</p>
                    <p className="text-2xl font-bold mt-1">{k.value}</p>
                  </div>
                  <div className={`w-9 h-9 rounded-xl ${k.bg} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${k.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Campaigns table */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Carregando métricas...</span>
        </div>
      ) : campaigns.length === 0 ? (
        <Card className="border-dashed border-border/50">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <TrendingUp className="w-10 h-10 text-muted-foreground mb-3" />
            <p className="font-medium">Nenhuma campanha encontrada</p>
            <p className="text-sm text-muted-foreground mt-1">Crie sua primeira campanha com o Gestor de Tráfego IA</p>
            <Link href="/agents/traffic-manager" className="mt-4">
              <Button variant="outline" size="sm">Criar com IA</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {campaigns.map(c => {
            const st = STATUS_LABEL[c.status] || STATUS_LABEL.PAUSED;
            const ins = c.insights;
            return (
              <Card key={c.id} className="border-border/50 hover:border-border transition-colors">
                <CardContent className="py-4">
                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    {/* Left: name + status */}
                    <div className="flex items-center gap-3 min-w-0">
                      <button
                        onClick={() => toggleStatus(c)}
                        disabled={toggling === c.id}
                        className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all flex-shrink-0 ${
                          c.status === "ACTIVE"
                            ? "bg-emerald-500/10 hover:bg-red-500/10 text-emerald-400 hover:text-red-400"
                            : "bg-secondary hover:bg-emerald-500/10 text-muted-foreground hover:text-emerald-400"
                        }`}
                        title={c.status === "ACTIVE" ? "Pausar" : "Ativar"}
                      >
                        {toggling === c.id
                          ? <RefreshCw className="w-4 h-4 animate-spin" />
                          : c.status === "ACTIVE"
                          ? <Pause className="w-4 h-4" />
                          : <Play className="w-4 h-4" />}
                      </button>
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate">{c.name}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <Badge className={`text-xs border ${st.color}`}>{st.label}</Badge>
                          <span className="text-xs text-muted-foreground capitalize">{c.objective?.replace("OUTCOME_", "").toLowerCase()}</span>
                          {c.daily_budget_brl && <span className="text-xs text-muted-foreground">R${c.daily_budget_brl}/dia</span>}
                        </div>
                      </div>
                    </div>

                    {/* Right: metrics */}
                    {ins && (
                      <div className="flex items-center gap-6 flex-wrap">
                        <Metric label="Impressões" value={ins.impressions.toLocaleString("pt-BR")} icon={Eye} />
                        <Metric label="Cliques" value={ins.clicks.toLocaleString("pt-BR")} icon={MousePointerClick} />
                        <Metric label="CTR" value={`${ins.ctr}%`} icon={TrendingUp} highlight={ins.ctr >= 1} />
                        <Metric label="CPC" value={`R$${ins.cpc_brl}`} icon={DollarSign} />
                        <Metric label="Investido" value={`R$${ins.spend_brl.toFixed(2)}`} icon={DollarSign} />
                        {ins.leads > 0 && <Metric label="Leads" value={ins.leads.toString()} icon={Users} highlight />}
                        {ins.cpl_brl && <Metric label="CPL" value={`R$${ins.cpl_brl}`} icon={Users} />}
                      </div>
                    )}
                    {!ins || ins.impressions === 0 && (
                      <span className="text-xs text-muted-foreground italic">Sem dados no período</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, icon: Icon, highlight = false }: { label: string; value: string; icon: React.ElementType; highlight?: boolean }) {
  return (
    <div className="text-center">
      <p className={`text-sm font-semibold ${highlight ? "text-emerald-400" : "text-foreground"}`}>{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
