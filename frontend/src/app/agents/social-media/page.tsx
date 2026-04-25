import { Camera } from "lucide-react";
import { AgentChat } from "@/components/agents/agent-chat";

const suggestions = [
  "Crie um calendário editorial para outubro para uma clínica de estética",
  "Escreva 5 legendas para posts de antes e depois",
  "Quais os melhores horários para postar no Camera?",
  "Gere hashtags para um post de tratamento facial",
];

export default function SocialMediaPage() {
  return (
    <AgentChat
      agentType="social-media"
      agentName="Social Media"
      agentDescription="Criação de conteúdo, legendas, hashtags e calendário editorial"
      agentIcon={<Camera className="w-5 h-5 text-white" />}
      gradientClass="from-pink-600 to-rose-700"
      suggestions={suggestions}
    />
  );
}
