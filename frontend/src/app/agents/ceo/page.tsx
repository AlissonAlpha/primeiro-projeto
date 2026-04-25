import { Brain } from "lucide-react";
import { AgentChat } from "@/components/agents/agent-chat";

const suggestions = [
  "Crie uma estratégia de marketing para uma clínica de estética",
  "Quais KPIs devo acompanhar para e-commerce?",
  "Como distribuir R$5.000/mês entre Meta Ads e Google?",
  "Analise o funil de vendas do meu negócio",
];

export default function CEOPage() {
  return (
    <AgentChat
      agentType="ceo"
      agentName="CEO Estrategista"
      agentDescription="Estratégia, metas de negócio e alocação de budget entre canais"
      agentIcon={<Brain className="w-5 h-5 text-white" />}
      gradientClass="from-violet-600 to-purple-700"
      suggestions={suggestions}
    />
  );
}
