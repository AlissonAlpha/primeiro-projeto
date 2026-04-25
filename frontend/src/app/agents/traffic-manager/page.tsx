import { Megaphone } from "lucide-react";
import { AgentChat } from "@/components/agents/agent-chat";

const suggestions = [
  "Crie uma campanha de leads para clínica de estética, R$50/dia, SP",
  "Como otimizar meu ROAS no Meta Ads?",
  "Qual a melhor estrutura de campanha para e-commerce?",
  "Monte uma campanha de remarketing no Google Ads",
];

export default function TrafficManagerPage() {
  return (
    <AgentChat
      agentType="traffic-manager"
      agentName="Gestor de Tráfego"
      agentDescription="Criação e otimização de campanhas no Meta Ads e Google Ads"
      agentIcon={<Megaphone className="w-5 h-5 text-white" />}
      gradientClass="from-blue-600 to-cyan-700"
      suggestions={suggestions}
    />
  );
}
