"use client";

import { useState } from "react";
import { ChevronRight, ChevronLeft, Sparkles, Upload, Eye, Rocket, Check, Loader2, ImageIcon, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { generateCopy, uploadCreative, type CopyBrief } from "@/lib/api";

const STEPS = [
  { id: 1, label: "Briefing", icon: Sparkles },
  { id: 2, label: "Copy IA", icon: Sparkles },
  { id: 3, label: "Criativo", icon: ImageIcon },
  { id: 4, label: "Revisão", icon: Eye },
];

const TONES = ["Profissional", "Descontraído", "Urgente", "Inspirador", "Direto"];
const OBJECTIVES = [
  { value: "leads", label: "Geração de Leads" },
  { value: "vendas", label: "Vendas / Conversão" },
  { value: "trafego", label: "Tráfego para site" },
  { value: "awareness", label: "Reconhecimento de marca" },
];

export default function NewAdPage() {
  const [step, setStep] = useState(1);
  const [brief, setBrief] = useState<CopyBrief>({
    product: "", audience: "", objective: "leads",
    tone: "Profissional", differentials: "", cta_hint: "",
  });
  const [copyResponse, setCopyResponse] = useState("");
  const [loadingCopy, setLoadingCopy] = useState(false);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [selectedCopy, setSelectedCopy] = useState<{ headline: string; primary_text: string; cta: string } | null>(null);

  async function handleGenerateCopy() {
    setLoadingCopy(true);
    try {
      const res = await generateCopy(brief);
      setCopyResponse(res.raw_response);
      setStep(2);
    } catch {
      setCopyResponse("Erro ao conectar. Verifique se o backend está rodando.");
      setStep(2);
    } finally {
      setLoadingCopy(false);
    }
  }

  function handleImageSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  }

  async function handleImageUpload() {
    if (!imageFile) return;
    setUploadingImage(true);
    try {
      const res = await uploadCreative(imageFile);
      setUploadedUrl(res.public_url);
    } catch {
      alert("Erro no upload. Verifique o backend.");
    } finally {
      setUploadingImage(false);
    }
  }

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Criar Anúncio</h1>
        <p className="text-muted-foreground text-sm mt-1">Fluxo completo com geração de copy por IA</p>
      </div>

      {/* Steps */}
      <div className="flex items-center gap-2">
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          const isActive = step === s.id;
          const isDone = step > s.id;
          return (
            <div key={s.id} className="flex items-center gap-2">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                isActive ? "bg-violet-600 text-white" :
                isDone ? "bg-violet-500/20 text-violet-400" :
                "bg-secondary text-muted-foreground"
              }`}>
                {isDone ? <Check className="w-3 h-3" /> : <Icon className="w-3 h-3" />}
                {s.label}
              </div>
              {i < STEPS.length - 1 && <ChevronRight className="w-3 h-3 text-muted-foreground" />}
            </div>
          );
        })}
      </div>

      {/* Step 1 — Briefing */}
      {step === 1 && (
        <Card className="border-border/50">
          <CardHeader><CardTitle className="text-base">Briefing do Anúncio</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1.5 block">Produto / Serviço *</label>
              <textarea
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-violet-500"
                rows={2} placeholder="Ex: Clínica de estética especializada em tratamentos faciais"
                value={brief.product} onChange={e => setBrief(p => ({ ...p, product: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Público-alvo *</label>
              <textarea
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-violet-500"
                rows={2} placeholder="Ex: Mulheres de 25-45 anos em São Paulo interessadas em beleza e autocuidado"
                value={brief.audience} onChange={e => setBrief(p => ({ ...p, audience: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Objetivo da campanha *</label>
              <div className="flex flex-wrap gap-2">
                {OBJECTIVES.map(o => (
                  <button key={o.value} onClick={() => setBrief(p => ({ ...p, objective: o.value }))}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                      brief.objective === o.value ? "bg-violet-600 text-white border-violet-600" : "border-border text-muted-foreground hover:border-violet-500/50"
                    }`}>
                    {o.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Tom de voz</label>
              <div className="flex flex-wrap gap-2">
                {TONES.map(t => (
                  <button key={t} onClick={() => setBrief(p => ({ ...p, tone: t }))}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                      brief.tone === t ? "bg-violet-600 text-white border-violet-600" : "border-border text-muted-foreground hover:border-violet-500/50"
                    }`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Diferenciais / Promoção</label>
              <input
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500"
                placeholder="Ex: 1ª consulta gratuita, 10 anos de experiência, mais de 500 clientes atendidos"
                value={brief.differentials} onChange={e => setBrief(p => ({ ...p, differentials: e.target.value }))}
              />
            </div>
            <Button
              onClick={handleGenerateCopy}
              disabled={!brief.product || !brief.audience || loadingCopy}
              className="w-full bg-violet-600 hover:bg-violet-700"
            >
              {loadingCopy ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Gerando copy com IA...</>
              ) : (
                <><Sparkles className="w-4 h-4 mr-2" />Gerar Copy com Agente de IA</>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2 — Copy gerada */}
      {step === 2 && (
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-violet-400" />
                Copy gerada pelo Agente
              </CardTitle>
              <Button variant="outline" size="sm" onClick={() => setStep(1)}>
                <ChevronLeft className="w-3 h-3 mr-1" />Refazer briefing
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-secondary/50 border border-border/50 rounded-xl p-4 max-h-96 overflow-y-auto">
              <div className="text-sm whitespace-pre-wrap leading-relaxed">{copyResponse}</div>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={handleGenerateCopy} disabled={loadingCopy}>
                {loadingCopy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Regenerar
              </Button>
              <Button className="flex-1 bg-violet-600 hover:bg-violet-700" onClick={() => setStep(3)}>
                Usar essa copy
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3 — Upload criativo */}
      {step === 3 && (
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Upload do Criativo</CardTitle>
              <Button variant="outline" size="sm" onClick={() => setStep(2)}>
                <ChevronLeft className="w-3 h-3 mr-1" />Voltar
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {!imagePreview ? (
              <label className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-border/50 rounded-xl cursor-pointer hover:border-violet-500/50 transition-colors bg-secondary/30">
                <Upload className="w-8 h-8 text-muted-foreground mb-2" />
                <p className="text-sm font-medium">Clique para enviar imagem ou vídeo</p>
                <p className="text-xs text-muted-foreground mt-1">JPG, PNG, WEBP, MP4 · Máx 30MB</p>
                <input type="file" className="hidden" accept="image/*,video/mp4" onChange={handleImageSelect} />
              </label>
            ) : (
              <div className="relative">
                <img src={imagePreview} alt="Preview" className="w-full h-64 object-cover rounded-xl" />
                <button
                  onClick={() => { setImageFile(null); setImagePreview(null); setUploadedUrl(null); }}
                  className="absolute top-2 right-2 w-8 h-8 bg-black/60 rounded-full flex items-center justify-center hover:bg-black/80 transition-colors"
                >
                  <X className="w-4 h-4 text-white" />
                </button>
                {uploadedUrl && (
                  <div className="absolute bottom-2 left-2 bg-emerald-500/90 text-white text-xs px-2 py-1 rounded-lg flex items-center gap-1">
                    <Check className="w-3 h-3" />Enviado ao Supabase
                  </div>
                )}
              </div>
            )}

            {imageFile && !uploadedUrl && (
              <Button onClick={handleImageUpload} disabled={uploadingImage} className="w-full bg-violet-600 hover:bg-violet-700">
                {uploadingImage ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Enviando...</> : <><Upload className="w-4 h-4 mr-2" />Enviar para Supabase Storage</>}
              </Button>
            )}

            {uploadedUrl && (
              <Button className="w-full bg-violet-600 hover:bg-violet-700" onClick={() => setStep(4)}>
                Revisar anúncio
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            )}

            <Button variant="ghost" className="w-full text-muted-foreground" onClick={() => setStep(4)}>
              Pular por agora (configurar criativo depois)
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 4 — Revisão */}
      {step === 4 && (
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Eye className="w-4 h-4 text-violet-400" />
                Resumo do Anúncio
              </CardTitle>
              <Button variant="outline" size="sm" onClick={() => setStep(3)}>
                <ChevronLeft className="w-3 h-3 mr-1" />Voltar
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Preview card */}
            <div className="border border-border/50 rounded-xl overflow-hidden">
              {imagePreview && (
                <img src={imagePreview} alt="Creative" className="w-full h-48 object-cover" />
              )}
              <div className="p-4 bg-card space-y-1">
                <p className="text-xs text-muted-foreground">Anúncio · Patrocinado</p>
                <p className="font-semibold text-sm">{brief.product || "Seu produto"}</p>
                <p className="text-xs text-muted-foreground line-clamp-3">{brief.differentials || "Descrição do anúncio gerada pela IA..."}</p>
                <div className="mt-2 pt-2 border-t border-border/50 flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">{brief.audience}</span>
                  <Badge variant="outline" className="text-xs">Saiba mais</Badge>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-secondary/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">Objetivo</p>
                <p className="font-medium capitalize">{brief.objective}</p>
              </div>
              <div className="bg-secondary/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">Tom</p>
                <p className="font-medium">{brief.tone}</p>
              </div>
              <div className="bg-secondary/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">Criativo</p>
                <p className="font-medium">{uploadedUrl ? "✅ Enviado" : "⚠️ Pendente"}</p>
              </div>
              <div className="bg-secondary/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">Copy</p>
                <p className="font-medium">✅ Gerada</p>
              </div>
            </div>

            <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
              <p className="text-xs text-amber-400 font-medium">⚠️ O anúncio será criado como PAUSADO</p>
              <p className="text-xs text-muted-foreground mt-1">Você revisa no Gerenciador de Anúncios antes de ativar.</p>
            </div>

            <Button className="w-full bg-violet-600 hover:bg-violet-700 h-11">
              <Rocket className="w-4 h-4 mr-2" />
              Enviar para revisão no Meta Ads
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
