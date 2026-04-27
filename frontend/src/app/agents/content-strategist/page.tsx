import { Sparkles } from "lucide-react";
import { AgentChat } from "@/components/agents/agent-chat";

const suggestions = [
  "Crie um brief para a Gotrix Motos, foco em Dia das Mães, Instagram",
  "Pesquise tendências de conteúdo para concessionárias de motos",
  "Quais datas comemorativas posso usar para a Gotrix em maio?",
  "Analise o que concorrentes do segmento automotivo estão postando",
];

export default function ContentStrategistPage() {
  return (
    <AgentChat
      agentType={"content-strategist" as never}
      agentName="Estrategista de Conteúdo"
      agentDescription="Pesquisa tendências, analisa concorrentes e gera briefs criativos"
      agentIcon={<Sparkles className="w-5 h-5 text-white" />}
      gradientClass="from-amber-500 to-orange-600"
      suggestions={suggestions}
    />
  );
}
