"use client";

import { useState, useEffect } from "react";
import { Zap, Plus, Trash2, ChevronDown, Search, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { listAdAccounts, type AdAccount } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface Creative {
  primary_text: string;
  headline: string;
  cta: string;
}

interface AdSetConfig {
  name: string;
  budget: string;
  creatives: Creative[];
}

interface TemplateData {
  account: AdAccount | null;
  objective: string;
  campaignName: string;
  budgetType: "ABO" | "CBO";
  totalBudget: string;
  audienceType: "advantage" | "manual";
  ageMin: string;
  ageMax: string;
  gender: string;
  location: string;
  locationKey: string;
  radiusKm: string;
  interests: string;
  adSets: AdSetConfig[];
}

const OBJECTIVES = [
  { value: "leads", label: "Geração de Leads" },
  { value: "vendas", label: "Vendas / Conversão" },
  { value: "trafego", label: "Tráfego para site" },
  { value: "reconhecimento", label: "Reconhecimento de marca" },
  { value: "engajamento", label: "Engajamento" },
];

const CTAS = ["LEARN_MORE", "SIGN_UP", "SHOP_NOW", "CONTACT_US", "GET_QUOTE"];

const EMPTY_CREATIVE: Creative = { primary_text: "", headline: "", cta: "LEARN_MORE" };
const EMPTY_ADSET = (idx: number): AdSetConfig => ({
  name: `Conjunto ${String(idx + 1).padStart(2, "0")}`,
  budget: "30",
  creatives: [{ ...EMPTY_CREATIVE }],
});

function buildMessage(data: TemplateData): string {
  const obj = OBJECTIVES.find(o => o.value === data.objective)?.label || data.objective;
  const month = new Date().toLocaleDateString("pt-BR", { month: "short", year: "numeric" });
  const name = data.campaignName || `${data.account?.name} | ${obj} | ${month}`;
  const loc = data.locationKey
    ? `${data.location} (key: ${data.locationKey})${data.radiusKm ? ` +${data.radiusKm}km` : ""}`
    : "Brasil";
  const budget = data.budgetType === "CBO"
    ? `CBO — R$${data.totalBudget}/dia total`
    : `ABO — R$${data.adSets[0]?.budget || "30"}/dia por conjunto`;
  const audience = data.audienceType === "advantage"
    ? "Advantage+ Audience"
    : `Manual — interesses: ${data.interests || "amplo"}`;

  const lines = [
    `Criar campanha completa com as seguintes configurações:`,
    ``,
    `Conta: ${data.account?.name} (${data.account?.id})`,
    `Objetivo: ${obj}`,
    `Nome: ${name}`,
    `Orçamento: ${budget}`,
    `Estrutura: ${data.adSets.length} conjunto(s) × ${data.adSets[0]?.creatives.length || 1} criativo(s) cada`,
    `Público: ${data.ageMin || 18}–${data.audienceType === "advantage" ? "65" : (data.ageMax || 65)} anos, ${data.gender || "todos os gêneros"}, ${loc}`,
    `Tipo de público: ${audience}`,
  ];

  data.adSets.forEach((set, i) => {
    lines.push(``, `[Conjunto ${i + 1}: ${set.name}]`);
    if (data.budgetType === "ABO") lines.push(`Orçamento: R$${set.budget}/dia`);
    set.creatives.forEach((cr, j) => {
      lines.push(`Criativo ${j + 1}: "${cr.primary_text}" | Headline: "${cr.headline}" | CTA: ${cr.cta}`);
    });
  });

  return lines.join("\n");
}

interface CampaignTemplateProps {
  onSend: (message: string) => void;
}

export function CampaignTemplate({ onSend }: CampaignTemplateProps) {
  const [open, setOpen] = useState(false);
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [searching, setSearching] = useState(false);
  const [locQuery, setLocQuery] = useState("");
  const [locResults, setLocResults] = useState<{ key: string; name: string; region: string }[]>([]);

  const [data, setData] = useState<TemplateData>({
    account: null, objective: "leads", campaignName: "",
    budgetType: "ABO", totalBudget: "50",
    audienceType: "advantage", ageMin: "18", ageMax: "65",
    gender: "", location: "", locationKey: "", radiusKm: "30",
    interests: "", adSets: [EMPTY_ADSET(0)],
  });

  useEffect(() => {
    listAdAccounts().then(a => {
      const active = a.filter(x => x.status === "Ativo");
      setAccounts(active);
      const gotrix = active.find(x => x.name.toLowerCase().includes("gotrix"));
      if (gotrix) set("account", gotrix);
    }).catch(() => {});
  }, []);

  function set(key: keyof TemplateData, value: unknown) {
    setData(p => ({ ...p, [key]: value }));
  }

  async function searchLocation() {
    if (!locQuery.trim()) return;
    setSearching(true);
    try {
      const r = await fetch(`${API_URL}/agents/traffic-manager/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: `search_location_only: ${locQuery}` }),
      });
      // Fallback: call search directly
      const res = await fetch(`${API_URL}/meta/search-locations?q=${encodeURIComponent(locQuery)}`);
      if (res.ok) {
        const d = await res.json();
        setLocResults(d.locations || []);
      }
    } catch {}
    setSearching(false);
  }

  function addAdSet() {
    set("adSets", [...data.adSets, EMPTY_ADSET(data.adSets.length)]);
  }

  function removeAdSet(i: number) {
    set("adSets", data.adSets.filter((_, idx) => idx !== i));
  }

  function updateAdSet(i: number, key: keyof AdSetConfig, value: unknown) {
    const updated = [...data.adSets];
    updated[i] = { ...updated[i], [key]: value };
    set("adSets", updated);
  }

  function addCreative(setIdx: number) {
    const updated = [...data.adSets];
    updated[setIdx].creatives.push({ ...EMPTY_CREATIVE });
    set("adSets", updated);
  }

  function removeCreative(setIdx: number, crIdx: number) {
    const updated = [...data.adSets];
    updated[setIdx].creatives = updated[setIdx].creatives.filter((_, i) => i !== crIdx);
    set("adSets", updated);
  }

  function updateCreative(setIdx: number, crIdx: number, key: keyof Creative, value: string) {
    const updated = [...data.adSets];
    updated[setIdx].creatives[crIdx][key] = value;
    set("adSets", updated);
  }

  function handleSend() {
    const msg = buildMessage(data);
    onSend(msg);
    setOpen(false);
  }

  const inputCls = "w-full bg-background border border-border/60 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500";
  const labelCls = "text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block";

  return (
    <>
      <Button variant="outline" size="sm"
        onClick={() => setOpen(true)}
        className="gap-2 border-violet-500/30 text-violet-400 hover:bg-violet-500/10 hover:border-violet-500/60">
        <Zap className="w-3.5 h-3.5" />
        Template rápido
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-violet-400" />
              Template de Campanha
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-5 pt-2">

            {/* Account + Objective */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelCls}>Conta</label>
                <select className={inputCls} value={data.account?.id || ""}
                  onChange={e => set("account", accounts.find(a => a.id === e.target.value) || null)}>
                  {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </div>
              <div>
                <label className={labelCls}>Objetivo</label>
                <select className={inputCls} value={data.objective}
                  onChange={e => set("objective", e.target.value)}>
                  {OBJECTIVES.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
            </div>

            {/* Campaign name */}
            <div>
              <label className={labelCls}>Nome da campanha (deixe vazio para gerar automaticamente)</label>
              <input className={inputCls} placeholder="Ex: Gotrix | Leads | Mai 2026"
                value={data.campaignName} onChange={e => set("campaignName", e.target.value)} />
            </div>

            {/* Budget */}
            <div>
              <label className={labelCls}>Tipo de orçamento</label>
              <div className="flex gap-2 mb-3">
                {(["ABO", "CBO"] as const).map(t => (
                  <button key={t} onClick={() => set("budgetType", t)}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-all ${data.budgetType === t ? "bg-violet-600 text-white border-violet-600" : "border-border text-muted-foreground hover:border-violet-500/50"}`}>
                    {t === "ABO" ? "ABO — Por conjunto" : "CBO — Total campanha"}
                  </button>
                ))}
              </div>
              {data.budgetType === "CBO" && (
                <div>
                  <label className={labelCls}>Orçamento total diário (R$)</label>
                  <input type="number" className={inputCls} value={data.totalBudget}
                    onChange={e => set("totalBudget", e.target.value)} />
                </div>
              )}
            </div>

            {/* Audience */}
            <div className="space-y-3">
              <label className={labelCls}>Público</label>
              <div className="flex gap-2">
                {(["advantage", "manual"] as const).map(t => (
                  <button key={t} onClick={() => set("audienceType", t)}
                    className={`flex-1 py-2 rounded-lg text-xs font-medium border transition-all ${data.audienceType === t ? "bg-violet-600 text-white border-violet-600" : "border-border text-muted-foreground"}`}>
                    {t === "advantage" ? "🤖 Advantage+" : "🎯 Manual"}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className={labelCls}>Idade mín.</label>
                  <input type="number" className={inputCls} value={data.ageMin}
                    onChange={e => set("ageMin", e.target.value)} />
                </div>
                <div>
                  <label className={labelCls}>Idade máx.</label>
                  <input type="number" className={inputCls}
                    value={data.audienceType === "advantage" ? "65 (fixo)" : data.ageMax}
                    disabled={data.audienceType === "advantage"}
                    onChange={e => set("ageMax", e.target.value)} />
                </div>
                <div>
                  <label className={labelCls}>Gênero</label>
                  <select className={inputCls} value={data.gender} onChange={e => set("gender", e.target.value)}>
                    <option value="">Todos</option>
                    <option value="masculino">Masculino</option>
                    <option value="feminino">Feminino</option>
                  </select>
                </div>
              </div>

              {data.audienceType === "manual" && (
                <div>
                  <label className={labelCls}>Interesses (ex: motos, fitness)</label>
                  <input className={inputCls} placeholder="motos, automóveis, esportes"
                    value={data.interests} onChange={e => set("interests", e.target.value)} />
                </div>
              )}

              {/* Location search */}
              <div>
                <label className={labelCls}>Localização</label>
                <div className="flex gap-2">
                  <input className={`${inputCls} flex-1`} placeholder="Buscar cidade... ex: Bebedouro"
                    value={locQuery} onChange={e => setLocQuery(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && searchLocation()} />
                  <button onClick={searchLocation} disabled={searching}
                    className="px-3 bg-secondary border border-border rounded-lg hover:border-violet-500/50 transition-colors">
                    {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  </button>
                </div>
                {locResults.length > 0 && (
                  <div className="mt-1 border border-border rounded-lg overflow-hidden">
                    {locResults.slice(0, 5).map(l => (
                      <button key={l.key} onClick={() => {
                        set("location", l.name); set("locationKey", l.key);
                        setLocQuery(`${l.name}, ${l.region}`); setLocResults([]);
                      }} className="w-full text-left px-3 py-2 text-sm hover:bg-accent transition-colors flex justify-between">
                        <span>{l.name}</span>
                        <span className="text-muted-foreground text-xs">{l.region}</span>
                      </button>
                    ))}
                  </div>
                )}
                {data.locationKey && (
                  <div className="mt-1 flex items-center gap-2">
                    <Badge variant="outline" className="text-xs text-violet-400 border-violet-500/30">
                      ✓ {data.location} (key: {data.locationKey})
                    </Badge>
                    <input type="number" className="w-20 bg-background border border-border/60 rounded px-2 py-1 text-xs"
                      placeholder="raio km" value={data.radiusKm}
                      onChange={e => set("radiusKm", e.target.value)} />
                    <span className="text-xs text-muted-foreground">km de raio</span>
                  </div>
                )}
              </div>
            </div>

            {/* Ad Sets */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className={labelCls}>Conjuntos e Criativos</label>
                <button onClick={addAdSet}
                  className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1">
                  <Plus className="w-3 h-3" />Adicionar conjunto
                </button>
              </div>

              <div className="space-y-3">
                {data.adSets.map((adset, si) => (
                  <div key={si} className="border border-border/50 rounded-xl p-4 space-y-3 bg-secondary/20">
                    <div className="flex items-center justify-between">
                      <input className="bg-transparent text-sm font-medium focus:outline-none border-b border-transparent hover:border-border focus:border-violet-500 pb-0.5"
                        value={adset.name} onChange={e => updateAdSet(si, "name", e.target.value)} />
                      <div className="flex items-center gap-2">
                        {data.budgetType === "ABO" && (
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground">R$</span>
                            <input type="number" className="w-16 bg-background border border-border/60 rounded px-2 py-1 text-xs text-center"
                              value={adset.budget} onChange={e => updateAdSet(si, "budget", e.target.value)} />
                            <span className="text-xs text-muted-foreground">/dia</span>
                          </div>
                        )}
                        {data.adSets.length > 1 && (
                          <button onClick={() => removeAdSet(si)} className="text-muted-foreground hover:text-red-400">
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Creatives */}
                    <div className="space-y-2">
                      {adset.creatives.map((cr, ci) => (
                        <div key={ci} className="bg-background border border-border/40 rounded-lg p-3 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-muted-foreground">Criativo {ci + 1}</span>
                            {adset.creatives.length > 1 && (
                              <button onClick={() => removeCreative(si, ci)} className="text-muted-foreground hover:text-red-400">
                                <Trash2 className="w-3 h-3" />
                              </button>
                            )}
                          </div>
                          <textarea rows={2} className={`${inputCls} resize-none`}
                            placeholder="Texto principal do anúncio..."
                            value={cr.primary_text}
                            onChange={e => updateCreative(si, ci, "primary_text", e.target.value)} />
                          <div className="flex gap-2">
                            <input className={`${inputCls} flex-1`} placeholder="Headline (máx 40 chars)"
                              maxLength={40} value={cr.headline}
                              onChange={e => updateCreative(si, ci, "headline", e.target.value)} />
                            <select className="bg-background border border-border/60 rounded-lg px-2 text-xs focus:outline-none"
                              value={cr.cta} onChange={e => updateCreative(si, ci, "cta", e.target.value)}>
                              {CTAS.map(c => <option key={c}>{c}</option>)}
                            </select>
                          </div>
                        </div>
                      ))}
                      <button onClick={() => addCreative(si)}
                        className="w-full py-1.5 border border-dashed border-border/50 rounded-lg text-xs text-muted-foreground hover:border-violet-500/50 hover:text-violet-400 transition-colors">
                        <Plus className="w-3 h-3 inline mr-1" />Adicionar criativo
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Send button */}
            <Button onClick={handleSend} className="w-full bg-violet-600 hover:bg-violet-700 h-11">
              <Zap className="w-4 h-4 mr-2" />
              Enviar para o Agente
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
