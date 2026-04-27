"use client";

import { useState, useEffect } from "react";
import {
  Zap, Plus, Trash2, Search, Loader2, AlertCircle,
  CheckCircle2, ImageIcon, ChevronRight, ChevronLeft,
  Target, DollarSign, Users, Megaphone, Eye, X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { listAdAccounts, uploadCreative, type AdAccount } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ─── Types ────────────────────────────────────────────
interface Creative { primary_text: string; headline: string; cta: string; image_url: string; image_name: string; }
interface AdSetConfig { name: string; budget: string; creatives: Creative[]; }
interface TemplateData {
  account: AdAccount | null;
  objective: string; campaignName: string;
  budgetType: "ABO" | "CBO"; totalBudget: string;
  audienceType: "advantage" | "manual";
  ageMin: string; ageMax: string; gender: string;
  location: string; locationKey: string; radiusKm: string; interests: string;
  destinationType: "whatsapp" | "link"; destination: string; savedWhatsapp: string;
  adSets: AdSetConfig[];
}

const OBJECTIVES = [
  { value: "leads", label: "Geração de Leads", icon: "🎯", desc: "Capturar contatos interessados" },
  { value: "vendas", label: "Vendas", icon: "🛒", desc: "Converter em compras" },
  { value: "trafego", label: "Tráfego", icon: "🌐", desc: "Visitas ao site ou WhatsApp" },
  { value: "reconhecimento", label: "Reconhecimento", icon: "📢", desc: "Aumentar visibilidade da marca" },
  { value: "engajamento", label: "Engajamento", icon: "💬", desc: "Curtidas, comentários e shares" },
];

const CTAS = [
  { value: "LEARN_MORE", label: "Saiba Mais" },
  { value: "SIGN_UP", label: "Cadastre-se" },
  { value: "SHOP_NOW", label: "Comprar Agora" },
  { value: "CONTACT_US", label: "Fale Conosco" },
  { value: "GET_QUOTE", label: "Pedir Orçamento" },
  { value: "BOOK_TRAVEL", label: "Reservar" },
];

const STEPS = [
  { id: 1, label: "Campanha", icon: Target },
  { id: 2, label: "Público", icon: Users },
  { id: 3, label: "Criativos", icon: ImageIcon },
  { id: 4, label: "Revisão", icon: Eye },
];

const empty_creative = (): Creative => ({ primary_text: "", headline: "", cta: "LEARN_MORE", image_url: "", image_name: "" });
const empty_adset = (i: number): AdSetConfig => ({ name: `Conjunto ${String(i + 1).padStart(2, "0")}`, budget: "30", creatives: [empty_creative()] });
const initial: TemplateData = {
  account: null, objective: "leads", campaignName: "",
  budgetType: "ABO", totalBudget: "60",
  audienceType: "advantage", ageMin: "18", ageMax: "45", gender: "", location: "", locationKey: "", radiusKm: "30", interests: "",
  destinationType: "whatsapp", destination: "", savedWhatsapp: "",
  adSets: [empty_adset(0)],
};

function buildMessage(d: TemplateData): string {
  const obj = OBJECTIVES.find(o => o.value === d.objective)?.label || d.objective;
  const month = new Date().toLocaleDateString("pt-BR", { month: "short", year: "numeric" });
  const name = d.campaignName || `${d.account?.name} | ${obj} | ${month}`;
  const loc = d.locationKey ? `${d.location} (key: ${d.locationKey}), raio: ${d.radiusKm}km` : "Brasil inteiro";
  const dest = d.destinationType === "whatsapp" ? (d.savedWhatsapp || "buscar whatsapp vinculado") : d.destination;
  const budget = d.budgetType === "CBO" ? `CBO — R$${d.totalBudget}/dia` : "ABO — por conjunto";
  const audience = d.audienceType === "advantage" ? "Advantage+ Audience" : `Manual — interesses: ${d.interests || "amplo"}`;
  const lines = [
    "Criar campanha completa agora com TODOS os dados abaixo. Não pergunte nada — use exatamente o que está aqui:", "",
    `CONTA: ${d.account?.name} (ID: ${d.account?.id})`,
    `OBJETIVO: ${obj}`, `NOME: ${name}`, `ORÇAMENTO: ${budget}`,
    `LOCALIZAÇÃO: ${loc}`, `PÚBLICO: ${d.ageMin}–${d.audienceType === "advantage" ? "65" : d.ageMax} anos, ${d.gender || "todos"}, ${audience}`,
    `DESTINO: ${dest}`, `ESTRUTURA: ${d.adSets.length} conjunto(s)`, "",
  ];
  d.adSets.forEach((s, si) => {
    lines.push(`--- CONJUNTO ${si + 1}: ${s.name} ---`);
    if (d.budgetType === "ABO") lines.push(`Orçamento: R$${s.budget}/dia`);
    s.creatives.forEach((cr, ci) => {
      lines.push(`  CRIATIVO ${ci + 1}:`);
      lines.push(`  Texto: ${cr.primary_text || "(gerar com IA)"}`);
      lines.push(`  Headline: ${cr.headline || "(gerar com IA)"}`);
      lines.push(`  CTA: ${cr.cta}`);
      if (cr.image_url) lines.push(`  Imagem: ${cr.image_url}`);
    });
    lines.push("");
  });
  return lines.join("\n");
}

// ─── Component ────────────────────────────────────────
export function CampaignTemplate({ onSend }: { onSend: (msg: string) => void }) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(1);
  const [data, setData] = useState<TemplateData>(initial);
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [locQuery, setLocQuery] = useState("");
  const [locResults, setLocResults] = useState<{ key: string; name: string; region: string }[]>([]);
  const [searching, setSearching] = useState(false);
  const [uploadingIdx, setUploadingIdx] = useState<string | null>(null);
  const [uploadErrors, setUploadErrors] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    if (!open) return;
    listAdAccounts().then(a => {
      const active = a.filter(x => x.status === "Ativo");
      setAccounts(active);
      const gotrix = active.find(x => x.name.toLowerCase().includes("gotrix"));
      if (gotrix && !data.account) { set("account", gotrix); fetchWa(gotrix.id); }
    }).catch(() => {});
  }, [open]);

  function set(k: keyof TemplateData, v: unknown) { setData(p => ({ ...p, [k]: v })); setErrors([]); }

  async function fetchWa(id: string) {
    try {
      const r = await fetch(`${API_URL}/agents/traffic-manager/account-info/${id}`);
      if (r.ok) { const d = await r.json(); if (d.whatsapp_number) { const url = `https://wa.me/${d.whatsapp_number}`; setData(p => ({ ...p, savedWhatsapp: url, destination: p.destinationType === "whatsapp" ? url : p.destination })); } }
    } catch {}
  }

  async function searchLoc() {
    if (!locQuery.trim()) return;
    setSearching(true);
    try { const r = await fetch(`${API_URL}/meta/search-locations?q=${encodeURIComponent(locQuery)}`); if (r.ok) { const d = await r.json(); setLocResults(d.locations || []); } } catch {}
    setSearching(false);
  }

  async function uploadImg(si: number, ci: number, file: File) {
    const key = `${si}-${ci}`;
    setUploadingIdx(key);
    setUploadErrors(p => { const n = { ...p }; delete n[key]; return n; });
    try {
      const r = await uploadCreative(file);
      if (!r.public_url) throw new Error("URL não retornada");
      updateCr(si, ci, "image_url", r.public_url);
      updateCr(si, ci, "image_name", file.name);
    } catch (e) {
      setUploadErrors(p => ({ ...p, [key]: e instanceof Error ? e.message : "Erro no upload" }));
    }
    setUploadingIdx(null);
  }

  function updateSet(si: number, k: keyof AdSetConfig, v: unknown) { setData(p => ({ ...p, adSets: p.adSets.map((s, i) => i === si ? { ...s, [k]: v } : s) })); }
  function updateCr(si: number, ci: number, k: keyof Creative, v: string) { setData(p => ({ ...p, adSets: p.adSets.map((s, i) => i === si ? { ...s, creatives: s.creatives.map((c, j) => j === ci ? { ...c, [k]: v } : c) } : s) })); }
  function addSet() { setData(p => ({ ...p, adSets: [...p.adSets, empty_adset(p.adSets.length)] })); }
  function rmSet(i: number) { setData(p => ({ ...p, adSets: p.adSets.filter((_, j) => j !== i) })); }
  function addCr(si: number) { setData(p => ({ ...p, adSets: p.adSets.map((s, i) => i === si ? { ...s, creatives: [...s.creatives, empty_creative()] } : s) })); }
  function rmCr(si: number, ci: number) { setData(p => ({ ...p, adSets: p.adSets.map((s, i) => i === si ? { ...s, creatives: s.creatives.filter((_, j) => j !== ci) } : s) })); }

  function canNext() {
    if (step === 1) return !!data.account && !!data.objective;
    if (step === 2) return true;
    if (step === 3) return data.adSets.every(s => s.creatives.length > 0) && !uploadingIdx && Object.keys(uploadErrors).length === 0;
    return true;
  }

  function handleSend() {
    if (uploadingIdx) { setErrors(["Aguarde o upload terminar."]); return; }
    if (!data.account) { setErrors(["Selecione uma conta."]); return; }
    const dest = data.destinationType === "whatsapp" ? data.savedWhatsapp : data.destination;
    if (data.destinationType === "link" && !dest) { setErrors(["Informe a URL de destino."]); setStep(1); return; }
    onSend(buildMessage(data));
    setOpen(false); setStep(1);
  }

  function openModal() { setData(initial); setStep(1); setErrors([]); setLocQuery(""); setLocResults([]); setOpen(true); }

  // ─── Style helpers ───
  const inp = "w-full bg-muted/50 border border-border/60 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500/60 transition-all";
  const lbl = "text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 block";

  function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
    return <button onClick={onClick} className={`px-4 py-2 rounded-xl text-sm font-medium border transition-all ${active ? "bg-violet-600 text-white border-violet-600 shadow-lg shadow-violet-500/20" : "border-border/50 text-muted-foreground hover:border-violet-500/40 hover:text-foreground bg-muted/30"}`}>{children}</button>;
  }

  return (
    <>
      <Button variant="outline" size="sm" onClick={openModal}
        className="gap-2 border-violet-500/30 text-violet-400 hover:bg-violet-500/10 hover:border-violet-500/50 transition-all">
        <Zap className="w-3.5 h-3.5" />Template rápido
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          showCloseButton={false}
          className="sm:max-w-xl p-0 gap-0 overflow-hidden border-border/50 max-h-[90vh] w-[calc(100vw-2rem)]">

          {/* Header */}
          <div className="px-6 pt-5 pb-4 border-b border-border/40 bg-card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-violet-600 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-white" />
                </div>
                <span className="font-semibold text-sm">Template de Campanha</span>
              </div>
              <button onClick={() => setOpen(false)} className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded-lg hover:bg-muted">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Step indicators */}
            <div className="flex items-center gap-1">
              {STEPS.map((s, i) => {
                const Icon = s.icon;
                const done = step > s.id;
                const active = step === s.id;
                return (
                  <div key={s.id} className="flex items-center gap-1 flex-1">
                    <div className={`flex items-center gap-1.5 flex-1 py-1.5 px-2 rounded-lg transition-all ${active ? "bg-violet-600/15 border border-violet-500/30" : done ? "bg-emerald-500/10" : "opacity-40"}`}>
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${active ? "bg-violet-600" : done ? "bg-emerald-500" : "bg-muted"}`}>
                        {done ? <CheckCircle2 className="w-3 h-3 text-white" /> : <Icon className={`w-2.5 h-2.5 ${active ? "text-white" : "text-muted-foreground"}`} />}
                      </div>
                      <span className={`text-xs font-medium hidden sm:block ${active ? "text-violet-400" : done ? "text-emerald-400" : "text-muted-foreground"}`}>{s.label}</span>
                    </div>
                    {i < STEPS.length - 1 && <div className={`w-3 h-px flex-shrink-0 ${step > s.id ? "bg-emerald-500/50" : "bg-border/40"}`} />}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Body */}
          <div className="overflow-y-auto max-h-[calc(90vh-200px)]">
            <div className="px-6 py-5 space-y-5">

              {/* ─── STEP 1: Campaign ─── */}
              {step === 1 && (
                <div className="space-y-5">
                  {/* Account */}
                  <div>
                    <label className={lbl}>Conta de anúncios</label>
                    <select className={inp} value={data.account?.id || ""}
                      onChange={e => { const a = accounts.find(x => x.id === e.target.value) || null; setData(p => ({ ...p, account: a, savedWhatsapp: "", destination: p.destinationType === "whatsapp" ? "" : p.destination })); if (a) fetchWa(a.id); }}>
                      <option value="">Selecionar conta...</option>
                      {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                    </select>
                  </div>

                  {/* Objective */}
                  <div>
                    <label className={lbl}>Objetivo da campanha</label>
                    <div className="grid grid-cols-1 gap-2">
                      {OBJECTIVES.map(o => (
                        <button key={o.value} onClick={() => set("objective", o.value)}
                          className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-left transition-all ${data.objective === o.value ? "bg-violet-600/10 border-violet-500/40 text-foreground" : "border-border/40 text-muted-foreground hover:border-border hover:text-foreground bg-muted/20"}`}>
                          <span className="text-lg">{o.icon}</span>
                          <div>
                            <p className={`text-sm font-medium ${data.objective === o.value ? "text-violet-300" : ""}`}>{o.label}</p>
                            <p className="text-xs text-muted-foreground">{o.desc}</p>
                          </div>
                          {data.objective === o.value && <CheckCircle2 className="w-4 h-4 text-violet-400 ml-auto flex-shrink-0" />}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Budget */}
                  <div>
                    <label className={lbl}>Orçamento</label>
                    <div className="flex gap-2 mb-3">
                      <Chip active={data.budgetType === "ABO"} onClick={() => set("budgetType", "ABO")}>ABO — Por conjunto</Chip>
                      <Chip active={data.budgetType === "CBO"} onClick={() => set("budgetType", "CBO")}>CBO — Total campanha</Chip>
                    </div>
                    <p className="text-xs text-muted-foreground mb-3">
                      {data.budgetType === "ABO" ? "Você controla quanto cada conjunto gasta — ideal para testar públicos." : "O Meta distribui o orçamento automaticamente — ideal para escalar."}
                    </p>
                    {data.budgetType === "CBO" && (
                      <div className="flex items-center gap-3 bg-muted/30 rounded-xl px-4 py-3 border border-border/40">
                        <span className="text-muted-foreground text-sm">R$</span>
                        <input type="number" className="bg-transparent text-sm flex-1 focus:outline-none font-semibold" value={data.totalBudget} onChange={e => set("totalBudget", e.target.value)} />
                        <span className="text-muted-foreground text-sm">/dia total</span>
                      </div>
                    )}
                  </div>

                  {/* Destination */}
                  <div>
                    <label className={lbl}>Destino do anúncio</label>
                    <div className="flex gap-2 mb-3">
                      <Chip active={data.destinationType === "whatsapp"} onClick={() => { set("destinationType", "whatsapp"); if (data.savedWhatsapp) set("destination", data.savedWhatsapp); }}>💬 WhatsApp vinculado</Chip>
                      <Chip active={data.destinationType === "link"} onClick={() => { set("destinationType", "link"); set("destination", ""); }}>🔗 URL / Link</Chip>
                    </div>
                    {data.destinationType === "whatsapp" ? (
                      data.savedWhatsapp ? (
                        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          <span className="text-sm text-emerald-300 font-medium">{data.savedWhatsapp}</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
                          <AlertCircle className="w-4 h-4 text-amber-400" />
                          <span className="text-xs text-amber-300">Nenhum WhatsApp salvo para esta conta. O agente buscará automaticamente.</span>
                        </div>
                      )
                    ) : (
                      <input className={inp} placeholder="https://seusite.com.br" value={data.destination} onChange={e => set("destination", e.target.value)} />
                    )}
                  </div>
                </div>
              )}

              {/* ─── STEP 2: Audience ─── */}
              {step === 2 && (
                <div className="space-y-5">
                  {/* Audience type */}
                  <div>
                    <label className={lbl}>Tipo de público</label>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { v: "advantage", icon: "🤖", title: "Advantage+", desc: "IA do Meta encontra o público ideal automaticamente" },
                        { v: "manual", icon: "🎯", title: "Manual", desc: "Você define interesses e comportamentos específicos" },
                      ].map(opt => (
                        <button key={opt.v} onClick={() => set("audienceType", opt.v as "advantage" | "manual")}
                          className={`p-4 rounded-xl border text-left transition-all ${data.audienceType === opt.v ? "bg-violet-600/10 border-violet-500/40" : "border-border/40 bg-muted/20 hover:border-border"}`}>
                          <span className="text-2xl block mb-2">{opt.icon}</span>
                          <p className={`text-sm font-semibold mb-1 ${data.audienceType === opt.v ? "text-violet-300" : ""}`}>{opt.title}</p>
                          <p className="text-xs text-muted-foreground leading-snug">{opt.desc}</p>
                        </button>
                      ))}
                    </div>
                    {data.audienceType === "advantage" && (
                      <p className="mt-2 text-xs text-muted-foreground bg-muted/30 rounded-lg px-3 py-2">
                        ⚠️ Com Advantage+, o Meta exige idade máxima = 65. Sua faixa vira uma sugestão.
                      </p>
                    )}
                  </div>

                  {/* Age + Gender */}
                  <div>
                    <label className={lbl}>Faixa etária e gênero</label>
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-muted/30 border border-border/40 rounded-xl p-3">
                        <p className="text-xs text-muted-foreground mb-1.5">Idade mín.</p>
                        <input type="number" className="w-full bg-transparent text-sm font-semibold focus:outline-none" value={data.ageMin} onChange={e => set("ageMin", e.target.value)} />
                      </div>
                      <div className={`border rounded-xl p-3 ${data.audienceType === "advantage" ? "bg-muted/20 border-border/20 opacity-60" : "bg-muted/30 border-border/40"}`}>
                        <p className="text-xs text-muted-foreground mb-1.5">Idade máx.</p>
                        {data.audienceType === "advantage"
                          ? <p className="text-sm font-semibold text-muted-foreground">65 (fixo)</p>
                          : <input key="agemax" type="number" className="w-full bg-transparent text-sm font-semibold focus:outline-none" value={data.ageMax} min={data.ageMin} max="65" onChange={e => set("ageMax", e.target.value)} />}
                      </div>
                      <div className="bg-muted/30 border border-border/40 rounded-xl p-3">
                        <p className="text-xs text-muted-foreground mb-1.5">Gênero</p>
                        <select className="w-full bg-transparent text-sm font-semibold focus:outline-none" value={data.gender} onChange={e => set("gender", e.target.value)}>
                          <option value="">Todos</option>
                          <option value="masculino">Masculino</option>
                          <option value="feminino">Feminino</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Interests (manual only) */}
                  {data.audienceType === "manual" && (
                    <div>
                      <label className={lbl}>Interesses</label>
                      <input className={inp} placeholder="Ex: motos, automóveis, esportes radicais" value={data.interests} onChange={e => set("interests", e.target.value)} />
                    </div>
                  )}

                  {/* Location */}
                  <div>
                    <label className={lbl}>Localização</label>
                    <div className="flex gap-2">
                      <input className={`${inp} flex-1`} placeholder="Buscar cidade... ex: Bebedouro" value={locQuery} onChange={e => setLocQuery(e.target.value)} onKeyDown={e => e.key === "Enter" && searchLoc()} />
                      <button onClick={searchLoc} disabled={searching} className="px-4 bg-muted/50 border border-border/60 rounded-xl hover:border-violet-500/40 transition-all">
                        {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                      </button>
                    </div>

                    {locResults.length > 0 && (
                      <div className="mt-2 border border-border/50 rounded-xl overflow-hidden shadow-xl bg-popover">
                        {locResults.slice(0, 5).map(l => (
                          <button key={l.key} onClick={() => { set("location", l.name); set("locationKey", l.key); setLocQuery(`${l.name} — ${l.region}`); setLocResults([]); }}
                            className="w-full text-left px-4 py-3 text-sm hover:bg-accent transition-colors flex justify-between border-b border-border/30 last:border-0">
                            <span className="font-medium">{l.name}</span>
                            <span className="text-muted-foreground text-xs">{l.region}</span>
                          </button>
                        ))}
                      </div>
                    )}

                    {data.locationKey ? (
                      <div className="mt-3 flex items-center gap-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        <span className="text-sm text-emerald-300 font-medium flex-1">{data.location}</span>
                        <div className="flex items-center gap-2">
                          <input type="number" className="w-16 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-2 py-1 text-sm text-center focus:outline-none text-emerald-300" value={data.radiusKm} onChange={e => set("radiusKm", e.target.value)} />
                          <span className="text-xs text-emerald-400">km</span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground mt-2">Deixe em branco para Brasil inteiro</p>
                    )}
                  </div>
                </div>
              )}

              {/* ─── STEP 3: Creatives ─── */}
              {step === 3 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-muted-foreground">{data.adSets.length} conjunto(s) · {data.adSets.reduce((s, a) => s + a.creatives.length, 0)} criativo(s) total</p>
                    <button onClick={addSet} className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1 transition-colors">
                      <Plus className="w-3 h-3" />Conjunto
                    </button>
                  </div>

                  {data.adSets.map((adset, si) => (
                    <div key={si} className="border border-border/40 rounded-2xl overflow-hidden">
                      {/* Set header */}
                      <div className="flex items-center gap-3 px-4 py-3 bg-muted/30 border-b border-border/30">
                        <div className="w-6 h-6 rounded-lg bg-violet-600/20 flex items-center justify-center flex-shrink-0">
                          <Megaphone className="w-3 h-3 text-violet-400" />
                        </div>
                        <input className="bg-transparent text-sm font-semibold flex-1 focus:outline-none" value={adset.name} onChange={e => updateSet(si, "name", e.target.value)} />
                        {data.budgetType === "ABO" && (
                          <div className="flex items-center gap-1.5 bg-background/50 border border-border/40 rounded-lg px-2.5 py-1">
                            <span className="text-xs text-muted-foreground">R$</span>
                            <input type="number" className="w-12 bg-transparent text-xs font-bold text-center focus:outline-none" value={adset.budget} onChange={e => updateSet(si, "budget", e.target.value)} />
                            <span className="text-xs text-muted-foreground">/d</span>
                          </div>
                        )}
                        {data.adSets.length > 1 && (
                          <button onClick={() => rmSet(si)} className="text-muted-foreground hover:text-red-400 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                        )}
                      </div>

                      {/* Creatives */}
                      <div className="p-3 space-y-3">
                        {adset.creatives.map((cr, ci) => {
                          const uKey = `${si}-${ci}`;
                          const uErr = uploadErrors[uKey];
                          const uploading = uploadingIdx === uKey;
                          return (
                            <div key={ci} className="bg-background border border-border/30 rounded-xl p-3.5 space-y-3">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-violet-400 uppercase tracking-wide">Criativo {ci + 1}</span>
                                {adset.creatives.length > 1 && <button onClick={() => rmCr(si, ci)} className="text-muted-foreground hover:text-red-400 transition-colors"><X className="w-3.5 h-3.5" /></button>}
                              </div>

                              {/* Image */}
                              {cr.image_url ? (
                                <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">
                                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                                  <span className="text-xs text-emerald-300 flex-1 truncate">{cr.image_name}</span>
                                  <button onClick={() => { updateCr(si, ci, "image_url", ""); updateCr(si, ci, "image_name", ""); }} className="text-muted-foreground hover:text-red-400"><X className="w-3 h-3" /></button>
                                </div>
                              ) : (
                                <label className={`flex items-center gap-2.5 cursor-pointer rounded-xl px-3 py-2.5 border border-dashed transition-all ${uErr ? "bg-red-500/10 border-red-500/40" : "bg-muted/20 border-border/40 hover:border-violet-500/40 hover:bg-violet-500/5"}`}>
                                  {uploading ? <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" /> : uErr ? <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" /> : <ImageIcon className="w-4 h-4 text-muted-foreground" />}
                                  <span className={`text-xs ${uErr ? "text-red-400" : "text-muted-foreground"}`}>{uploading ? "Enviando imagem..." : uErr ? `${uErr} — tentar novamente` : "Adicionar imagem (JPG, PNG, WEBP)"}</span>
                                  <input type="file" accept="image/*" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) uploadImg(si, ci, f); e.target.value = ""; }} />
                                </label>
                              )}

                              {/* Text */}
                              <textarea rows={2} className={`${inp} resize-none text-xs`} placeholder="Texto do anúncio... (ou deixe vazio para gerar com IA)" value={cr.primary_text} onChange={e => updateCr(si, ci, "primary_text", e.target.value)} />

                              {/* Headline + CTA */}
                              <div className="flex gap-2">
                                <div className="flex-1 relative">
                                  <input className={`${inp} text-xs pr-10 ${cr.headline.length > 40 ? "border-red-500/50" : ""}`} placeholder="Headline (máx 40 chars)" value={cr.headline} onChange={e => updateCr(si, ci, "headline", e.target.value)} />
                                  <span className={`absolute right-3 top-1/2 -translate-y-1/2 text-xs ${cr.headline.length > 40 ? "text-red-400" : "text-muted-foreground"}`}>{cr.headline.length}/40</span>
                                </div>
                                <select className="bg-muted/50 border border-border/60 rounded-xl px-2.5 text-xs focus:outline-none min-w-[110px]" value={cr.cta} onChange={e => updateCr(si, ci, "cta", e.target.value)}>
                                  {CTAS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                                </select>
                              </div>
                            </div>
                          );
                        })}
                        <button onClick={() => addCr(si)} className="w-full py-2 border border-dashed border-border/40 rounded-xl text-xs text-muted-foreground hover:border-violet-500/40 hover:text-violet-400 transition-all flex items-center justify-center gap-1">
                          <Plus className="w-3 h-3" />Adicionar criativo
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* ─── STEP 4: Review ─── */}
              {step === 4 && (
                <div className="space-y-3">
                  <p className="text-xs text-muted-foreground">Confira antes de enviar ao agente</p>
                  {[
                    { icon: "🏢", label: "Conta", value: data.account?.name },
                    { icon: "🎯", label: "Objetivo", value: OBJECTIVES.find(o => o.value === data.objective)?.label },
                    { icon: "💰", label: "Orçamento", value: data.budgetType === "CBO" ? `CBO — R$${data.totalBudget}/dia` : `ABO — R$${data.adSets[0]?.budget}/dia por conjunto` },
                    { icon: "👥", label: "Público", value: `${data.ageMin}–${data.audienceType === "advantage" ? "65" : data.ageMax} anos · ${data.gender || "todos"} · ${data.audienceType === "advantage" ? "Advantage+" : "Manual"}` },
                    { icon: "📍", label: "Local", value: data.locationKey ? `${data.location} +${data.radiusKm}km` : "Brasil inteiro" },
                    { icon: "🔗", label: "Destino", value: data.destinationType === "whatsapp" ? (data.savedWhatsapp || "WhatsApp vinculado") : data.destination },
                    { icon: "📦", label: "Estrutura", value: `${data.adSets.length} conjunto(s) · ${data.adSets.reduce((s, a) => s + a.creatives.length, 0)} criativo(s)` },
                  ].map(row => (
                    <div key={row.label} className="flex items-start gap-3 py-2.5 border-b border-border/30 last:border-0">
                      <span className="text-base">{row.icon}</span>
                      <div>
                        <p className="text-xs text-muted-foreground">{row.label}</p>
                        <p className="text-sm font-medium">{row.value || "—"}</p>
                      </div>
                    </div>
                  ))}

                  {errors.length > 0 && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 space-y-1">
                      {errors.map((e, i) => <div key={i} className="flex items-center gap-2 text-xs text-red-400"><AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />{e}</div>)}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-border/40 bg-card flex items-center justify-between gap-3">
            <button onClick={() => setStep(s => Math.max(1, s - 1))} disabled={step === 1}
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground disabled:opacity-30 transition-all">
              <ChevronLeft className="w-4 h-4" />Voltar
            </button>

            <div className="flex items-center gap-1.5">
              {STEPS.map(s => <div key={s.id} className={`w-1.5 h-1.5 rounded-full transition-all ${step === s.id ? "bg-violet-500 w-4" : step > s.id ? "bg-emerald-500" : "bg-border"}`} />)}
            </div>

            {step < 4 ? (
              <Button size="sm" onClick={() => setStep(s => s + 1)} disabled={!canNext()}
                className="bg-violet-600 hover:bg-violet-700 gap-1.5">
                Próximo<ChevronRight className="w-4 h-4" />
              </Button>
            ) : (
              <Button size="sm" onClick={handleSend} className="bg-violet-600 hover:bg-violet-700 gap-1.5">
                <Zap className="w-4 h-4" />Criar campanha
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
