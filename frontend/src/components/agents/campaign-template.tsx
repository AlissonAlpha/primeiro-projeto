"use client";

import { useState, useEffect, MutableRefObject } from "react";
import { Zap, Plus, Trash2, Search, Loader2, AlertCircle, CheckCircle2, Image } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { listAdAccounts, uploadCreative, type AdAccount } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface Creative {
  primary_text: string;
  headline: string;
  cta: string;
  image_url: string;
  image_name: string;
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
  destinationType: "whatsapp" | "link";
  destination: string;
  savedWhatsapp: string;
  adSets: AdSetConfig[];
}

const OBJECTIVES = [
  { value: "leads", label: "Geração de Leads" },
  { value: "vendas", label: "Vendas / Conversão" },
  { value: "trafego", label: "Tráfego para site" },
  { value: "reconhecimento", label: "Reconhecimento de marca" },
  { value: "engajamento", label: "Engajamento" },
];

const CTAS = [
  { value: "LEARN_MORE", label: "Saiba Mais" },
  { value: "SIGN_UP", label: "Cadastre-se" },
  { value: "SHOP_NOW", label: "Comprar Agora" },
  { value: "CONTACT_US", label: "Fale Conosco" },
  { value: "GET_QUOTE", label: "Solicitar Orçamento" },
  { value: "BOOK_TRAVEL", label: "Reservar" },
];

const EMPTY_CREATIVE = (): Creative => ({
  primary_text: "", headline: "", cta: "LEARN_MORE", image_url: "", image_name: "",
});

const EMPTY_ADSET = (idx: number): AdSetConfig => ({
  name: `Conjunto ${String(idx + 1).padStart(2, "0")}`,
  budget: "30",
  creatives: [EMPTY_CREATIVE()],
});

function buildMessage(data: TemplateData): string {
  const obj = OBJECTIVES.find(o => o.value === data.objective)?.label || data.objective;
  const month = new Date().toLocaleDateString("pt-BR", { month: "short", year: "numeric" });
  const name = data.campaignName || `${data.account?.name} | ${obj} | ${month}`;

  const loc = data.locationKey
    ? `${data.location} (key: ${data.locationKey}), raio: ${data.radiusKm || "0"}km`
    : "Brasil inteiro";

  const destFinal = data.destinationType === "whatsapp"
    ? (data.savedWhatsapp || "buscar whatsapp vinculado da conta")
    : data.destination;

  const budget = data.budgetType === "CBO"
    ? `CBO — R$${data.totalBudget}/dia total para a campanha`
    : `ABO — orçamento individual por conjunto`;

  const audience = data.audienceType === "advantage"
    ? "Advantage+ Audience (IA do Meta)"
    : `Manual — interesses: ${data.interests || "amplo sem interesses"}`;

  const ageStr = `${data.ageMin || 18}–${data.audienceType === "advantage" ? "65" : (data.ageMax || 65)} anos`;
  const genderStr = data.gender === "masculino" ? "masculino" : data.gender === "feminino" ? "feminino" : "todos os gêneros";

  const lines: string[] = [
    `Criar campanha completa agora com TODOS os dados abaixo. Não pergunte nada — use exatamente o que está aqui:`,
    ``,
    `CONTA: ${data.account?.name} (ID: ${data.account?.id})`,
    `OBJETIVO: ${obj}`,
    `NOME: ${name}`,
    `ORÇAMENTO: ${budget}`,
    `LOCALIZAÇÃO: ${loc}`,
    `PÚBLICO: ${ageStr}, ${genderStr}, ${audience}`,
    `DESTINO: ${destFinal}`,
    `ESTRUTURA: ${data.adSets.length} conjunto(s)`,
    ``,
  ];

  data.adSets.forEach((set, si) => {
    lines.push(`--- CONJUNTO ${si + 1}: ${set.name} ---`);
    if (data.budgetType === "ABO") lines.push(`Orçamento: R$${set.budget}/dia`);
    lines.push(`Criativos: ${set.creatives.length}`);
    set.creatives.forEach((cr, ci) => {
      lines.push(``);
      lines.push(`  CRIATIVO ${ci + 1}:`);
      lines.push(`  Texto: ${cr.primary_text || "(gerar com IA)"}`);
      lines.push(`  Headline: ${cr.headline || "(gerar com IA)"}`);
      lines.push(`  CTA: ${cr.cta}`);
      if (cr.image_url) lines.push(`  Imagem: ${cr.image_url}`);
    });
    lines.push(``);
  });

  return lines.join("\n");
}

function validate(data: TemplateData): string[] {
  const errors: string[] = [];
  if (!data.account) errors.push("Selecione uma conta de anúncios");
  const dest = data.destinationType === "whatsapp" ? data.savedWhatsapp : data.destination;
  if (!dest && data.destinationType === "link") errors.push("Informe a URL de destino");
  data.adSets.forEach((set, si) => {
    if (data.budgetType === "ABO" && (!set.budget || Number(set.budget) < 5))
      errors.push(`Conjunto ${si + 1}: orçamento mínimo R$5/dia`);
    set.creatives.forEach((cr, ci) => {
      if (cr.headline && cr.headline.length > 40)
        errors.push(`Conjunto ${si + 1}, Criativo ${ci + 1}: headline muito longa (${cr.headline.length}/40 chars)`);
    });
  });
  return errors;
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
  const [uploadingIdx, setUploadingIdx] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  const [data, setData] = useState<TemplateData>({
    account: null, objective: "leads", campaignName: "",
    budgetType: "ABO", totalBudget: "60",
    audienceType: "advantage", ageMin: "18", ageMax: "45",
    gender: "", location: "", locationKey: "", radiusKm: "30",
    interests: "", destinationType: "whatsapp", destination: "", savedWhatsapp: "",
    adSets: [EMPTY_ADSET(0)],
  });

  useEffect(() => {
    if (!open) return;
    listAdAccounts().then(a => {
      const active = a.filter(x => x.status === "Ativo");
      setAccounts(active);
      const gotrix = active.find(x => x.name.toLowerCase().includes("gotrix"));
      if (gotrix && !data.account) {
        setField("account", gotrix);
        fetchAccountWhatsapp(gotrix.id);
      }
    }).catch(() => {});
  }, [open]);

  async function fetchAccountWhatsapp(accountId: string) {
    try {
      const res = await fetch(`${API_URL}/agents/traffic-manager/account-info/${accountId}`);
      if (res.ok) {
        const d = await res.json();
        if (d.whatsapp_number) {
          const url = `https://wa.me/${d.whatsapp_number}`;
          setData(p => ({ ...p, savedWhatsapp: url, destination: p.destinationType === "whatsapp" ? url : p.destination }));
        }
      }
    } catch {}
  }

  function setField(key: keyof TemplateData, value: unknown) {
    setData(p => ({ ...p, [key]: value }));
    setErrors([]);
  }

  async function searchLocation() {
    if (!locQuery.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`${API_URL}/meta/search-locations?q=${encodeURIComponent(locQuery)}`);
      if (res.ok) {
        const d = await res.json();
        setLocResults(d.locations || []);
      }
    } catch {}
    setSearching(false);
  }

  function selectLocation(loc: { key: string; name: string; region: string }) {
    setField("location", loc.name);
    setField("locationKey", loc.key);
    setLocQuery(`${loc.name} — ${loc.region}`);
    setLocResults([]);
  }

  function addAdSet() {
    setField("adSets", [...data.adSets, EMPTY_ADSET(data.adSets.length)]);
  }

  function removeAdSet(i: number) {
    setField("adSets", data.adSets.filter((_, idx) => idx !== i));
  }

  function updateAdSet(i: number, key: keyof AdSetConfig, value: unknown) {
    const updated = data.adSets.map((s, idx) => idx === i ? { ...s, [key]: value } : s);
    setField("adSets", updated);
  }

  function addCreative(si: number) {
    const updated = data.adSets.map((s, i) =>
      i === si ? { ...s, creatives: [...s.creatives, EMPTY_CREATIVE()] } : s
    );
    setField("adSets", updated);
  }

  function removeCreative(si: number, ci: number) {
    const updated = data.adSets.map((s, i) =>
      i === si ? { ...s, creatives: s.creatives.filter((_, j) => j !== ci) } : s
    );
    setField("adSets", updated);
  }

  function updateCreative(si: number, ci: number, key: keyof Creative, value: string) {
    const updated = data.adSets.map((s, i) =>
      i === si ? {
        ...s,
        creatives: s.creatives.map((cr, j) => j === ci ? { ...cr, [key]: value } : cr)
      } : s
    );
    setField("adSets", updated);
  }

  async function handleImageUpload(si: number, ci: number, file: File) {
    const key = `${si}-${ci}`;
    setUploadingIdx(key);
    try {
      const res = await uploadCreative(file);
      updateCreative(si, ci, "image_url", res.public_url);
      updateCreative(si, ci, "image_name", file.name);
    } catch {
      alert("Erro no upload da imagem.");
    }
    setUploadingIdx(null);
  }

  function handleSend() {
    const errs = validate(data);
    if (errs.length > 0) { setErrors(errs); return; }
    onSend(buildMessage(data));
    setOpen(false);
  }

  const inp = "w-full bg-background border border-border/60 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500";
  const lbl = "text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block";
  const tabBtn = (active: boolean) =>
    `flex-1 py-2 rounded-lg text-xs font-medium border transition-all ${active ? "bg-violet-600 text-white border-violet-600" : "border-border text-muted-foreground hover:border-violet-500/40"}`;

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}
        className="gap-2 border-violet-500/30 text-violet-400 hover:bg-violet-500/10 hover:border-violet-500/60">
        <Zap className="w-3.5 h-3.5" />Template rápido
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl max-h-[92vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-violet-400" />
              Template de Campanha
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-5 pt-1">

            {/* Account + Objective */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={lbl}>Conta *</label>
                <select className={inp} value={data.account?.id || ""}
                  onChange={e => {
                    const acc = accounts.find(a => a.id === e.target.value) || null;
                    setField("account", acc);
                    setData(p => ({ ...p, account: acc, savedWhatsapp: "", destination: p.destinationType === "whatsapp" ? "" : p.destination }));
                    if (acc) fetchAccountWhatsapp(acc.id);
                  }}>
                  <option value="">Selecionar conta...</option>
                  {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </div>
              <div>
                <label className={lbl}>Objetivo</label>
                <select className={inp} value={data.objective} onChange={e => setField("objective", e.target.value)}>
                  {OBJECTIVES.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
            </div>

            {/* Name */}
            <div>
              <label className={lbl}>Nome da campanha</label>
              <input className={inp} placeholder="Ex: Gotrix | Leads | Mai 2026"
                value={data.campaignName} onChange={e => setField("campaignName", e.target.value)} />
            </div>

            {/* Destination */}
            <div>
              <label className={lbl}>Destino do anúncio *</label>
              <div className="flex gap-2 mb-2">
                <button className={tabBtn(data.destinationType === "whatsapp")}
                  onClick={() => {
                    setField("destinationType", "whatsapp");
                    if (data.savedWhatsapp) setField("destination", data.savedWhatsapp);
                  }}>
                  💬 WhatsApp vinculado
                </button>
                <button className={tabBtn(data.destinationType === "link")}
                  onClick={() => { setField("destinationType", "link"); setField("destination", ""); }}>
                  🔗 Link / URL
                </button>
              </div>
              {data.destinationType === "whatsapp" ? (
                data.savedWhatsapp ? (
                  <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span className="text-sm text-emerald-400">{data.savedWhatsapp}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                    <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <span className="text-xs text-amber-400">
                      WhatsApp não encontrado para esta conta. O agente vai buscar automaticamente.
                    </span>
                  </div>
                )
              ) : (
                <input className={inp} placeholder="https://seusite.com.br"
                  value={data.destination} onChange={e => setField("destination", e.target.value)} />
              )}
            </div>

            {/* Budget */}
            <div>
              <label className={lbl}>Tipo de orçamento</label>
              <div className="flex gap-2 mb-3">
                <button className={tabBtn(data.budgetType === "ABO")} onClick={() => setField("budgetType", "ABO")}>
                  ABO — Por conjunto
                </button>
                <button className={tabBtn(data.budgetType === "CBO")} onClick={() => setField("budgetType", "CBO")}>
                  CBO — Total campanha
                </button>
              </div>
              {data.budgetType === "CBO" && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">R$</span>
                  <input type="number" className={`${inp} w-32`} value={data.totalBudget}
                    onChange={e => setField("totalBudget", e.target.value)} />
                  <span className="text-sm text-muted-foreground">/dia total</span>
                </div>
              )}
            </div>

            {/* Audience */}
            <div className="space-y-3">
              <label className={lbl}>Público</label>
              <div className="flex gap-2">
                <button className={tabBtn(data.audienceType === "advantage")} onClick={() => setField("audienceType", "advantage")}>
                  🤖 Advantage+ (IA do Meta)
                </button>
                <button className={tabBtn(data.audienceType === "manual")} onClick={() => setField("audienceType", "manual")}>
                  🎯 Manual por interesses
                </button>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className={lbl}>Idade mín.</label>
                  <input type="number" className={inp} value={data.ageMin}
                    onChange={e => setField("ageMin", e.target.value)} />
                </div>
                <div>
                  <label className={lbl}>Idade máx.</label>
                  {data.audienceType === "advantage" ? (
                    <div className="flex items-center gap-1.5 bg-secondary/50 border border-border/40 rounded-lg px-3 py-2">
                      <span className="text-sm text-muted-foreground">65</span>
                      <span className="text-xs text-muted-foreground ml-1">(fixo Meta)</span>
                    </div>
                  ) : (
                    <input
                      key="age-max-manual"
                      type="number"
                      className={inp}
                      value={data.ageMax}
                      min={data.ageMin || "18"}
                      max="65"
                      onChange={e => setField("ageMax", e.target.value)}
                    />
                  )}
                </div>
                <div>
                  <label className={lbl}>Gênero</label>
                  <select className={inp} value={data.gender} onChange={e => setField("gender", e.target.value)}>
                    <option value="">Todos</option>
                    <option value="masculino">Masculino</option>
                    <option value="feminino">Feminino</option>
                  </select>
                </div>
              </div>

              {data.audienceType === "manual" && (
                <div>
                  <label className={lbl}>Interesses (separados por vírgula)</label>
                  <input className={inp} placeholder="motos, automóveis, esportes radicais"
                    value={data.interests} onChange={e => setField("interests", e.target.value)} />
                </div>
              )}

              {/* Location */}
              <div>
                <label className={lbl}>Localização</label>
                <div className="flex gap-2">
                  <input className={`${inp} flex-1`} placeholder="Buscar cidade... ex: Bebedouro"
                    value={locQuery} onChange={e => setLocQuery(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && searchLocation()} />
                  <button onClick={searchLocation} disabled={searching}
                    className="px-3 bg-secondary border border-border/60 rounded-lg hover:border-violet-500/50 transition-colors flex-shrink-0">
                    {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  </button>
                </div>

                {locResults.length > 0 && (
                  <div className="mt-1 border border-border rounded-xl overflow-hidden shadow-lg z-10 relative bg-popover">
                    {locResults.slice(0, 5).map(l => (
                      <button key={l.key} onClick={() => selectLocation(l)}
                        className="w-full text-left px-3 py-2.5 text-sm hover:bg-accent transition-colors flex justify-between border-b border-border/30 last:border-0">
                        <span className="font-medium">{l.name}</span>
                        <span className="text-muted-foreground text-xs">{l.region}</span>
                      </button>
                    ))}
                  </div>
                )}

                {data.locationKey && (
                  <div className="mt-2 flex items-center gap-3 flex-wrap">
                    <Badge variant="outline" className="text-xs text-violet-400 border-violet-500/30 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      {data.location} (key: {data.locationKey})
                    </Badge>
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-muted-foreground whitespace-nowrap">Raio de alcance:</label>
                      <input type="number" className="w-20 bg-background border border-border/60 rounded-lg px-2 py-1 text-sm text-center focus:outline-none focus:ring-1 focus:ring-violet-500"
                        value={data.radiusKm} onChange={e => setField("radiusKm", e.target.value)} />
                      <span className="text-xs text-muted-foreground">km</span>
                    </div>
                  </div>
                )}
                {!data.locationKey && (
                  <p className="text-xs text-muted-foreground mt-1">Deixe em branco para Brasil inteiro</p>
                )}
              </div>
            </div>

            {/* Ad Sets & Creatives */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className={lbl}>Conjuntos e Criativos *</label>
                <button onClick={addAdSet}
                  className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1 transition-colors">
                  <Plus className="w-3 h-3" />Adicionar conjunto
                </button>
              </div>

              <div className="space-y-4">
                {data.adSets.map((adset, si) => (
                  <div key={si} className="border border-border/50 rounded-xl p-4 space-y-3 bg-secondary/20">
                    {/* Set header */}
                    <div className="flex items-center justify-between gap-2">
                      <input
                        className="bg-transparent text-sm font-semibold focus:outline-none border-b border-transparent hover:border-border/50 focus:border-violet-500 pb-0.5 flex-1"
                        value={adset.name} onChange={e => updateAdSet(si, "name", e.target.value)} />
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {data.budgetType === "ABO" && (
                          <div className="flex items-center gap-1.5 bg-background border border-border/60 rounded-lg px-2 py-1">
                            <span className="text-xs text-muted-foreground">R$</span>
                            <input type="number" className="w-14 bg-transparent text-sm text-center focus:outline-none"
                              value={adset.budget} onChange={e => updateAdSet(si, "budget", e.target.value)} />
                            <span className="text-xs text-muted-foreground">/dia</span>
                          </div>
                        )}
                        {data.adSets.length > 1 && (
                          <button onClick={() => removeAdSet(si)}
                            className="w-7 h-7 rounded-lg bg-background border border-border/50 hover:border-red-500/50 hover:text-red-400 flex items-center justify-center transition-colors">
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Creatives */}
                    <div className="space-y-3">
                      {adset.creatives.map((cr, ci) => (
                        <div key={ci} className="bg-background border border-border/40 rounded-xl p-3 space-y-2.5">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-violet-400">Criativo {ci + 1}</span>
                            {adset.creatives.length > 1 && (
                              <button onClick={() => removeCreative(si, ci)}
                                className="text-muted-foreground hover:text-red-400 transition-colors">
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>

                          {/* Image upload */}
                          <div>
                            <label className="text-xs text-muted-foreground mb-1 block">Imagem (opcional)</label>
                            {cr.image_url ? (
                              <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                                <span className="text-xs text-emerald-400 truncate flex-1">{cr.image_name}</span>
                                <button onClick={() => { updateCreative(si, ci, "image_url", ""); updateCreative(si, ci, "image_name", ""); }}
                                  className="text-muted-foreground hover:text-red-400 flex-shrink-0">
                                  <Trash2 className="w-3 h-3" />
                                </button>
                              </div>
                            ) : (
                              <label className="flex items-center gap-2 cursor-pointer bg-secondary/50 border border-dashed border-border/60 hover:border-violet-500/50 rounded-lg px-3 py-2 transition-colors">
                                {uploadingIdx === `${si}-${ci}` ? (
                                  <><Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" /><span className="text-xs text-muted-foreground">Enviando...</span></>
                                ) : (
                                  <><Image className="w-3.5 h-3.5 text-muted-foreground" /><span className="text-xs text-muted-foreground">Clique para enviar imagem (JPG, PNG, WEBP)</span></>
                                )}
                                <input type="file" accept="image/*" className="hidden"
                                  onChange={e => { const f = e.target.files?.[0]; if (f) handleImageUpload(si, ci, f); }} />
                              </label>
                            )}
                          </div>

                          {/* Text */}
                          <div>
                            <label className="text-xs text-muted-foreground mb-1 block">Texto principal</label>
                            <textarea rows={2} className={`${inp} resize-none`}
                              placeholder="Texto do anúncio... (deixe vazio para gerar com IA)"
                              value={cr.primary_text}
                              onChange={e => updateCreative(si, ci, "primary_text", e.target.value)} />
                          </div>

                          {/* Headline + CTA */}
                          <div className="flex gap-2">
                            <div className="flex-1">
                              <div className="flex items-center justify-between mb-1">
                                <label className="text-xs text-muted-foreground">Headline</label>
                                <span className={`text-xs ${cr.headline.length > 40 ? "text-red-400" : "text-muted-foreground"}`}>
                                  {cr.headline.length}/40
                                </span>
                              </div>
                              <input className={`${inp} ${cr.headline.length > 40 ? "border-red-500/50 ring-red-500/30" : ""}`}
                                placeholder="Título do anúncio (máx 40)"
                                maxLength={42} value={cr.headline}
                                onChange={e => updateCreative(si, ci, "headline", e.target.value)} />
                            </div>
                            <div className="w-40">
                              <label className="text-xs text-muted-foreground mb-1 block">CTA</label>
                              <select className={inp} value={cr.cta}
                                onChange={e => updateCreative(si, ci, "cta", e.target.value)}>
                                {CTAS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                              </select>
                            </div>
                          </div>
                        </div>
                      ))}

                      <button onClick={() => addCreative(si)}
                        className="w-full py-2 border border-dashed border-border/50 rounded-xl text-xs text-muted-foreground hover:border-violet-500/50 hover:text-violet-400 transition-colors flex items-center justify-center gap-1">
                        <Plus className="w-3 h-3" />Adicionar criativo
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Errors */}
            {errors.length > 0 && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 space-y-1">
                {errors.map((e, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-red-400">
                    <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                    {e}
                  </div>
                ))}
              </div>
            )}

            {/* Send */}
            <Button onClick={handleSend} className="w-full bg-violet-600 hover:bg-violet-700 h-11 text-sm font-semibold">
              <Zap className="w-4 h-4 mr-2" />
              Enviar para o Agente e Criar Campanha
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
