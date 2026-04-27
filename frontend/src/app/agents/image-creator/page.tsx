import { ImageIcon } from "lucide-react";
import { AgentChat } from "@/components/agents/agent-chat";

const suggestions = [
  "Gere uma imagem para post de Dia das Mães, concessionária de motos",
  "Crie 3 variações de imagem para o feed do Instagram da Gotrix",
  "Gere um criativo para Stories: oferta de moto com 20% de desconto",
  "Crie uma imagem estilo fotorrealista para anúncio do Facebook",
];

export default function ImageCreatorPage() {
  return (
    <AgentChat
      agentType={"image-creator" as never}
      agentName="Criador de Imagens"
      agentDescription="Gera imagens profissionais para marketing usando Freepik AI"
      agentIcon={<ImageIcon className="w-5 h-5 text-white" />}
      gradientClass="from-purple-600 to-pink-600"
      suggestions={suggestions}
    />
  );
}
