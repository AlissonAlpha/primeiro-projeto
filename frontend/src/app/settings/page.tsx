import { Settings, CheckCircle, XCircle, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const integrations = [
  {
    name: "Claude (Anthropic)",
    description: "Modelo de IA principal dos agentes",
    status: "connected",
    badge: "claude-sonnet-4-6",
    link: "https://console.anthropic.com",
  },
  {
    name: "OpenAI (GPT-4o)",
    description: "Geração de imagens (DALL-E 3)",
    status: "no-credits",
    badge: "Sem créditos",
    link: "https://platform.openai.com/settings/billing",
  },
  {
    name: "Supabase",
    description: "Banco de dados — Agencia do futuro",
    status: "connected",
    badge: "sa-east-1",
    link: "https://supabase.com/dashboard/project/azecoanlrryuipbikamr",
  },
  {
    name: "Meta Ads",
    description: "Campanhas no Facebook e Instagram",
    status: "pending",
    badge: "Não configurado",
    link: "https://developers.facebook.com",
  },
  {
    name: "Google Ads",
    description: "Campanhas no Google Search e Display",
    status: "pending",
    badge: "Não configurado",
    link: "https://developers.google.com/google-ads",
  },
];

export default function SettingsPage() {
  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Configurações</h1>
        <p className="text-muted-foreground text-sm mt-1">Integrações e chaves de API</p>
      </div>

      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="text-base">Integrações</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {integrations.map((item) => (
            <div
              key={item.name}
              className="flex items-center justify-between p-4 rounded-xl bg-secondary/30 border border-border/30"
            >
              <div className="flex items-center gap-3">
                {item.status === "connected" ? (
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                ) : item.status === "no-credits" ? (
                  <XCircle className="w-5 h-5 text-amber-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-muted-foreground" />
                )}
                <div>
                  <p className="text-sm font-medium">{item.name}</p>
                  <p className="text-xs text-muted-foreground">{item.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge
                  variant={item.status === "connected" ? "default" : "secondary"}
                  className={
                    item.status === "connected"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : item.status === "no-credits"
                      ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                      : ""
                  }
                >
                  {item.badge}
                </Badge>
                <a href={item.link} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="w-4 h-4 text-muted-foreground hover:text-foreground transition-colors" />
                </a>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
