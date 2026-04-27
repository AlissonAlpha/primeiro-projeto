"use client";

import { useState } from "react";
import { Sparkles, ImageIcon, Camera, ChevronRight, Loader2, CheckCircle2, AlertCircle, Play, FolderOpen, ExternalLink } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { listAdAccounts, type AdAccount } from "@/lib/api";
import { useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type StepStatus = "idle" | "running" | "done" | "error";

interface PipelineStep {
  id: string;
  label: string;
  desc: string;
  icon: React.ElementType;
  color: string;
  status: StepStatus;
  output?: string;
  images?: { url: string; folder: string }[];
}

const INITIAL_STEPS: PipelineStep[] = [
  { id: "strategist", label: "Estrategista", desc: "Pesquisa tendências e gera brief criativo", icon: Sparkles, color: "from-amber-500 to-orange-500", status: "idle" },
  { id: "image", label: "Criador de Imagens", desc: "Gera visuais com Freepik AI", icon: ImageIcon, color: "from-purple-600 to-pink-600", status: "idle" },
  { id: "social", label: "Social Media", desc: "Cria legenda, hashtags e horário ideal", icon: Camera, color: "from-pink-500 to-rose-600", status: "idle" },
];

export default function PipelinePage() {
  const [message, setMessage] = useState("");
  const [clientName, setClientName] = useState("geral");
  const [numImages, setNumImages] = useState(1);
  const [steps, setSteps] = useState<PipelineStep[]>(INITIAL_STEPS);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [accounts, setAccounts] = useState<AdAccount[]>([]);

  useEffect(() => {
    listAdAccounts().then(a => {
      setAccounts(a.filter(x => x.status === "Ativo"));
    }).catch(() => {});
  }, []);

  function updateStep(id: string, patch: Partial<PipelineStep>) {
    setSteps(prev => prev.map(s => s.id === id ? { ...s, ...patch } : s));
  }

  async function runPipeline() {
    if (!message.trim()) return;
    setRunning(true);
    setResult(null);
    setSteps(INITIAL_STEPS);

    try {
      updateStep("strategist", { status: "running" });

      const evtSource = new EventSource(
        `${API_URL}/content/pipeline/stream?message=${encodeURIComponent(message)}&client_name=${encodeURIComponent(clientName)}&num_images=${numImages}`
      );

      evtSource.onmessage = (e) => {
        const data = JSON.parse(e.data);

        if (data.step === "strategist_start") {
          updateStep("strategist", { status: "running", desc: data.message });
        }
        if (data.step === "image_start") {
          updateStep("strategist", { status: "done" });
          updateStep("image", { status: "running", desc: data.message });
        }
        if (data.step === "image_ready") {
          updateStep("image", {
            status: "done",
            images: [{ url: data.url, folder: data.folder }],
          });
          updateStep("social", { status: "running", desc: "Criando legenda e hashtags..." });
        }
        if (data.step === "social_done") {
          updateStep("social", { status: "done", output: data.content });
        }
        if (data.step === "completed") {
          setResult(data.result);
          setRunning(false);
          evtSource.close();
        }
        if (data.step === "error") {
          setSteps(prev => prev.map(s => s.status === "running" ? { ...s, status: "error", desc: data.message } : s));
          setRunning(false);
          evtSource.close();
        }
      };

      evtSource.onerror = () => {
        setSteps(prev => prev.map(s => s.status === "running" ? { ...s, status: "error" } : s));
        setRunning(false);
        evtSource.close();
      };

    } catch (err) {
      setRunning(false);
    }
  }

  const allDone = steps.every(s => s.status === "done");

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Pipeline de Conteúdo</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Estrategista → Criador de Imagens → Social Media — tudo automático
        </p>
      </div>

      {/* Input */}
      <Card className="border-border/50">
        <CardContent className="pt-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Cliente / Conta</label>
              <select className="w-full bg-muted/50 border border-border/60 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/40"
                value={clientName} onChange={e => setClientName(e.target.value)}>
                <option value="geral">Geral</option>
                {accounts.map(a => <option key={a.id} value={a.name}>{a.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Qtd. de imagens</label>
              <div className="flex gap-2">
                {[1, 2, 3].map(n => (
                  <button key={n} onClick={() => setNumImages(n)}
                    className={`flex-1 py-2 rounded-xl text-sm font-medium border transition-all ${numImages === n ? "bg-violet-600 text-white border-violet-600" : "border-border/50 text-muted-foreground hover:border-violet-500/40"}`}>
                    {n}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">O que você quer comunicar?</label>
            <textarea
              className="w-full bg-muted/50 border border-border/60 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/40 resize-none"
              rows={3}
              placeholder="Ex: Crie conteúdo para a Gotrix Motos no Dia das Mães, foco em mães motociclistas, Instagram"
              value={message}
              onChange={e => setMessage(e.target.value)}
              onKeyDown={e => e.key === "Enter" && e.metaKey && runPipeline()}
            />
          </div>

          <Button onClick={runPipeline} disabled={running || !message.trim()}
            className="w-full bg-violet-600 hover:bg-violet-700 h-11 gap-2">
            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {running ? "Pipeline rodando..." : "Executar Pipeline Completo"}
          </Button>
        </CardContent>
      </Card>

      {/* Pipeline steps */}
      <div className="space-y-3">
        {steps.map((step, i) => {
          const Icon = step.icon;
          const isRunning = step.status === "running";
          const isDone = step.status === "done";
          const isError = step.status === "error";

          return (
            <div key={step.id} className="flex gap-3">
              {/* Connector */}
              <div className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center flex-shrink-0 transition-all ${step.status === "idle" ? "opacity-30" : "opacity-100 shadow-lg"}`}>
                  {isRunning ? <Loader2 className="w-5 h-5 text-white animate-spin" />
                    : isDone ? <CheckCircle2 className="w-5 h-5 text-white" />
                    : isError ? <AlertCircle className="w-5 h-5 text-white" />
                    : <Icon className="w-5 h-5 text-white" />}
                </div>
                {i < steps.length - 1 && (
                  <div className={`w-0.5 h-full min-h-[20px] mt-1 transition-all ${isDone ? "bg-emerald-500/50" : "bg-border/30"}`} />
                )}
              </div>

              {/* Content */}
              <div className={`flex-1 pb-4 transition-all`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-sm font-semibold ${step.status === "idle" ? "text-muted-foreground" : "text-foreground"}`}>{step.label}</span>
                  {isRunning && <Badge className="text-xs bg-amber-500/10 text-amber-400 border-amber-500/20">Processando...</Badge>}
                  {isDone && <Badge className="text-xs bg-emerald-500/10 text-emerald-400 border-emerald-500/20">Concluído</Badge>}
                  {isError && <Badge className="text-xs bg-red-500/10 text-red-400 border-red-500/20">Erro</Badge>}
                </div>
                <p className={`text-xs ${step.status === "idle" ? "text-muted-foreground/50" : "text-muted-foreground"}`}>{step.desc}</p>

                {/* Images */}
                {step.images && step.images.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {step.images.map((img, j) => (
                      <div key={j} className="flex items-center gap-3 bg-muted/30 border border-border/40 rounded-xl p-3">
                        <img src={img.url} alt="Gerada" className="w-16 h-16 object-cover rounded-lg" />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />Imagem gerada
                          </p>
                          <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1 truncate">
                            <FolderOpen className="w-3 h-3 flex-shrink-0" />{img.folder || "storage/creatives/"}
                          </p>
                          <a href={img.url} target="_blank" rel="noopener noreferrer"
                            className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1 mt-1 transition-colors">
                            <ExternalLink className="w-3 h-3" />Ver imagem completa
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Social output preview */}
                {step.output && (
                  <div className="mt-3 bg-muted/20 border border-border/40 rounded-xl p-3 max-h-32 overflow-y-auto">
                    <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">{step.output}</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Final result */}
      {allDone && result && (
        <Card className="border-emerald-500/20 bg-emerald-500/5">
          <CardContent className="pt-5">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <span className="font-semibold text-emerald-400">Pipeline concluído!</span>
            </div>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="bg-background/50 rounded-xl p-3 border border-border/40">
                <p className="text-2xl font-bold">{(result.images as unknown[])?.length || 0}</p>
                <p className="text-xs text-muted-foreground">Imagens geradas</p>
              </div>
              <div className="bg-background/50 rounded-xl p-3 border border-border/40">
                <p className="text-2xl font-bold">1</p>
                <p className="text-xs text-muted-foreground">Brief criativo</p>
              </div>
              <div className="bg-background/50 rounded-xl p-3 border border-border/40">
                <p className="text-2xl font-bold">✓</p>
                <p className="text-xs text-muted-foreground">Pronto para postar</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
