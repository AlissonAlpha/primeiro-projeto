import Link from "next/link";
import { Brain, Megaphone, Camera, TrendingUp, Users, DollarSign, MousePointerClick, ArrowUpRight, Zap, Circle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const kpis = [
  {
    label: "Investimento Total",
    value: "R$ 0",
    sub: "Aguardando campanhas",
    icon: DollarSign,
    color: "text-violet-400",
    bg: "bg-violet-500/10",
  },
  {
    label: "Cliques",
    value: "0",
    sub: "Aguardando dados",
    icon: MousePointerClick,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    label: "Leads Gerados",
    value: "0",
    sub: "Aguardando campanhas",
    icon: Users,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  {
    label: "ROAS Médio",
    value: "—",
    sub: "Sem dados ainda",
    icon: TrendingUp,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
];

const agents = [
  {
    name: "CEO Estrategista",
    description: "Define estratégia, metas e KPIs do negócio",
    href: "/agents/ceo",
    icon: Brain,
    color: "from-violet-600 to-purple-700",
    badge: "Estratégia",
  },
  {
    name: "Gestor de Tráfego",
    description: "Cria e otimiza campanhas no Meta Ads e Google Ads",
    href: "/agents/traffic-manager",
    icon: Megaphone,
    color: "from-blue-600 to-cyan-700",
    badge: "Meta + Google",
  },
  {
    name: "Social Media",
    description: "Cria conteúdo e gerencia calendário editorial",
    href: "/agents/social-media",
    icon: Camera,
    color: "from-pink-600 to-rose-700",
    badge: "Conteúdo",
  },
];

export default function DashboardPage() {
  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">Bem-vindo à Agência do Futuro IA</p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-4 py-1.5">
          <Circle className="w-2 h-2 fill-emerald-400 text-emerald-400" />
          <span className="text-emerald-400 text-xs font-medium">Sistema operacional</span>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <Card key={kpi.label} className="border-border/50">
              <CardContent className="pt-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground font-medium">{kpi.label}</p>
                    <p className="text-2xl font-bold mt-1">{kpi.value}</p>
                    <p className="text-xs text-muted-foreground mt-1">{kpi.sub}</p>
                  </div>
                  <div className={`w-10 h-10 rounded-xl ${kpi.bg} flex items-center justify-center`}>
                    <Icon className={`w-5 h-5 ${kpi.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Agents */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Agentes IA</h2>
          <Badge variant="secondary" className="text-xs">
            <Zap className="w-3 h-3 mr-1" />{agents.length} ativos
          </Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {agents.map((agent) => {
            const Icon = agent.icon;
            return (
              <Link key={agent.href} href={agent.href}>
                <Card className="border-border/50 hover:border-violet-500/40 transition-all hover:shadow-lg hover:shadow-violet-500/5 cursor-pointer group h-full">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${agent.color} flex items-center justify-center shadow-lg`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Circle className="w-2 h-2 fill-emerald-400 text-emerald-400" />
                        <span className="text-xs text-emerald-400">online</span>
                      </div>
                    </div>
                    <CardTitle className="text-base mt-3 group-hover:text-violet-400 transition-colors">
                      {agent.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <p className="text-sm text-muted-foreground">{agent.description}</p>
                    <div className="flex items-center justify-between mt-4">
                      <Badge variant="outline" className="text-xs">{agent.badge}</Badge>
                      <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-violet-400 transition-colors" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Setup CTA */}
      <Card className="border-dashed border-violet-500/30 bg-violet-500/5">
        <CardContent className="flex items-center justify-between py-5">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
              <Zap className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <p className="text-sm font-semibold">Próximo passo: configure as APIs de anúncios</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Adicione Meta Ads e Google Ads para ativar campanhas automáticas
              </p>
            </div>
          </div>
          <Link href="/settings" className="text-xs bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg transition-colors font-medium">
            Configurar
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
