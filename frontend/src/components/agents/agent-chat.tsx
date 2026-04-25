"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Circle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { chatWithAgent, type AgentType } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface AgentChatProps {
  agentType: AgentType;
  agentName: string;
  agentDescription: string;
  agentIcon: React.ReactNode;
  gradientClass: string;
  suggestions?: string[];
}

export function AgentChat({
  agentType,
  agentName,
  agentDescription,
  agentIcon,
  gradientClass,
  suggestions = [],
}: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text?: string) {
    const content = text || input.trim();
    if (!content || loading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await chatWithAgent(agentType, content);
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: res.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Erro ao conectar com o agente. Verifique se o backend está rodando em `http://localhost:8000`.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Agent header */}
      <div className="px-6 py-4 border-b border-border/50 flex items-center justify-between bg-card/50">
        <div className="flex items-center gap-4">
          <div className={`w-11 h-11 rounded-2xl bg-gradient-to-br ${gradientClass} flex items-center justify-center shadow-lg`}>
            {agentIcon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-semibold text-foreground">{agentName}</h2>
              <div className="flex items-center gap-1">
                <Circle className="w-2 h-2 fill-emerald-400 text-emerald-400" />
                <span className="text-xs text-emerald-400">online</span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">{agentDescription}</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setMessages([])}
          className="text-muted-foreground hover:text-foreground"
        >
          <RotateCcw className="w-4 h-4 mr-2" />
          Limpar
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
            <div className={`w-16 h-16 rounded-3xl bg-gradient-to-br ${gradientClass} flex items-center justify-center shadow-xl opacity-80`}>
              {agentIcon}
            </div>
            <div>
              <h3 className="font-semibold text-foreground">{agentName}</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">{agentDescription}</p>
            </div>
            {suggestions.length > 0 && (
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => sendMessage(s)}
                    className="text-xs bg-secondary hover:bg-secondary/80 text-secondary-foreground px-3 py-1.5 rounded-full border border-border/50 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}
          >
            {msg.role === "assistant" && (
              <div className={`w-7 h-7 rounded-xl bg-gradient-to-br ${gradientClass} flex items-center justify-center mr-2 mt-0.5 flex-shrink-0`}>
                <span className="text-white text-xs">IA</span>
              </div>
            )}
            <div
              className={cn(
                "max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed",
                msg.role === "user"
                  ? "bg-violet-600 text-white rounded-br-sm"
                  : "bg-card border border-border/50 text-foreground rounded-bl-sm"
              )}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
              <p className={cn("text-xs mt-1.5", msg.role === "user" ? "text-violet-200" : "text-muted-foreground")}>
                {msg.timestamp.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
              </p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className={`w-7 h-7 rounded-xl bg-gradient-to-br ${gradientClass} flex items-center justify-center mr-2 mt-0.5`}>
              <span className="text-white text-xs">IA</span>
            </div>
            <div className="bg-card border border-border/50 px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Processando...</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-border/50 bg-background">
        <div className="flex gap-3 items-end">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Pergunte ao ${agentName}...`}
            className="resize-none min-h-[52px] max-h-32 text-sm"
            rows={1}
          />
          <Button
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            className="bg-violet-600 hover:bg-violet-700 h-[52px] px-4"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Enter para enviar · Shift+Enter para nova linha
        </p>
      </div>
    </div>
  );
}
