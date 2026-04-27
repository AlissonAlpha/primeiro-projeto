"use client";

import { useState, useRef, useEffect, useCallback, MutableRefObject } from "react";
import { Send, Loader2, Circle, RotateCcw, Paperclip, X, Image, FileVideo, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { chatWithAgent, uploadCreative, type AgentType } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  files?: UploadedFile[];
}

interface UploadedFile {
  name: string;
  url: string;
  type: string;
  preview?: string;
}

interface AgentChatProps {
  agentType: AgentType;
  agentName: string;
  agentDescription: string;
  agentIcon: React.ReactNode;
  gradientClass: string;
  suggestions?: string[];
  systemContext?: string;
  sendRef?: MutableRefObject<((msg: string) => void) | null>;
}

const SESSION_KEY_PREFIX = "chat_session_";
const MESSAGES_KEY_PREFIX = "chat_messages_";

function loadPersistedSession(agentType: string): { sessionId: string; messages: Message[] } {
  try {
    const sid = localStorage.getItem(`${SESSION_KEY_PREFIX}${agentType}`);
    const raw = localStorage.getItem(`${MESSAGES_KEY_PREFIX}${agentType}`);
    const msgs: Message[] = raw
      ? JSON.parse(raw).map((m: Message) => ({ ...m, timestamp: new Date(m.timestamp) }))
      : [];
    return {
      sessionId: sid || `${SESSION_KEY_PREFIX}${agentType}_${Date.now()}`,
      messages: msgs,
    };
  } catch {
    return { sessionId: `${SESSION_KEY_PREFIX}${agentType}_${Date.now()}`, messages: [] };
  }
}

export function AgentChat({
  agentType, agentName, agentDescription, agentIcon,
  gradientClass, suggestions = [], systemContext = "", sendRef,
}: AgentChatProps) {
  const persisted = loadPersistedSession(agentType);
  const [messages, setMessages] = useState<Message[]>(persisted.messages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(persisted.sessionId);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Persist session ID
  useEffect(() => {
    localStorage.setItem(`${SESSION_KEY_PREFIX}${agentType}`, sessionId);
  }, [sessionId, agentType]);

  // Persist messages on every update
  useEffect(() => {
    try {
      localStorage.setItem(`${MESSAGES_KEY_PREFIX}${agentType}`, JSON.stringify(messages));
    } catch {}
  }, [messages, agentType]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Expose sendMessage to parent via ref
  useEffect(() => {
    if (sendRef) sendRef.current = (msg: string) => sendMessage(msg);
  });

  const uploadFiles = useCallback(async (files: File[]): Promise<UploadedFile[]> => {
    const uploaded: UploadedFile[] = [];
    for (const file of files) {
      try {
        const res = await uploadCreative(file);
        uploaded.push({
          name: file.name,
          url: res.public_url,
          type: file.type,
          preview: file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined,
        });
      } catch {
        uploaded.push({ name: file.name, url: "", type: file.type });
      }
    }
    return uploaded;
  }, []);

  async function sendMessage(text?: string) {
    const content = (text || input).trim();
    if ((!content && pendingFiles.length === 0) || loading) return;

    let filesUploaded: UploadedFile[] = [];

    if (pendingFiles.length > 0) {
      setUploadingFiles(true);
      filesUploaded = await uploadFiles(pendingFiles);
      setUploadingFiles(false);
      setPendingFiles([]);
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: content || `📎 ${filesUploaded.length} arquivo(s) enviado(s)`,
      timestamp: new Date(),
      files: filesUploaded.length > 0 ? filesUploaded : undefined,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setUploadedFiles([]);
    setLoading(true);

    const fileContext = filesUploaded.length > 0
      ? `\n\n[Arquivos enviados: ${filesUploaded.map(f => `${f.name} (${f.url})`).join(", ")}]`
      : "";

    const fullMessage = `${content}${fileContext}${systemContext}`;

    try {
      const res = await chatWithAgent(agentType, fullMessage, sessionId);
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: "assistant",
        content: res.response,
        timestamp: new Date(),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Erro ao conectar com o agente. Verifique se o backend está rodando em `http://localhost:8000`.",
        timestamp: new Date(),
      }]);
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

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setPendingFiles(prev => [...prev, ...files]);
    e.target.value = "";
  }

  function removePendingFile(index: number) {
    setPendingFiles(prev => prev.filter((_, i) => i !== index));
  }

  function clearChat() {
    setMessages([]);
    setPendingFiles([]);
    localStorage.removeItem(`${MESSAGES_KEY_PREFIX}${agentType}`);
    localStorage.removeItem(`${SESSION_KEY_PREFIX}${agentType}`);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border/50 flex items-center justify-between bg-card/50">
        <div className="flex items-center gap-4">
          <div className={`w-11 h-11 rounded-2xl bg-gradient-to-br ${gradientClass} flex items-center justify-center shadow-lg`}>
            {agentIcon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-semibold">{agentName}</h2>
              <Circle className="w-2 h-2 fill-emerald-400 text-emerald-400" />
              <span className="text-xs text-emerald-400">online</span>
            </div>
            <p className="text-xs text-muted-foreground">{agentDescription}</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={clearChat} className="text-muted-foreground hover:text-foreground">
          <RotateCcw className="w-4 h-4 mr-2" />Nova conversa
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
              <h3 className="font-semibold">{agentName}</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">{agentDescription}</p>
            </div>
            {suggestions.length > 0 && (
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {suggestions.map(s => (
                  <button key={s} onClick={() => sendMessage(s)}
                    className="text-xs bg-secondary hover:bg-secondary/80 text-secondary-foreground px-3 py-1.5 rounded-full border border-border/50 transition-colors">
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
            {msg.role === "assistant" && (
              <div className={`w-7 h-7 rounded-xl bg-gradient-to-br ${gradientClass} flex items-center justify-center mr-2 mt-0.5 flex-shrink-0`}>
                <span className="text-white text-xs font-bold">IA</span>
              </div>
            )}
            <div className={cn(
              "max-w-[78%] space-y-2",
            )}>
              {/* File previews */}
              {msg.files && msg.files.length > 0 && (
                <div className="flex flex-wrap gap-2 justify-end">
                  {msg.files.map((f, i) => (
                    <div key={i} className="relative group">
                      {f.preview ? (
                        <img src={f.preview} alt={f.name}
                          className="w-24 h-24 object-cover rounded-xl border border-border/50" />
                      ) : (
                        <div className="w-24 h-24 bg-secondary rounded-xl border border-border/50 flex flex-col items-center justify-center gap-1">
                          <FileVideo className="w-6 h-6 text-muted-foreground" />
                          <span className="text-xs text-muted-foreground truncate px-1 w-full text-center">{f.name}</span>
                        </div>
                      )}
                      {f.url && (
                        <div className="absolute -top-1 -right-1 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center">
                          <CheckCircle className="w-3 h-3 text-white" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {/* Text bubble */}
              {msg.content && (
                <div className={cn(
                  "px-4 py-3 rounded-2xl text-sm leading-relaxed",
                  msg.role === "user"
                    ? "bg-violet-600 text-white rounded-br-sm"
                    : "bg-card border border-border/50 text-foreground rounded-bl-sm"
                )}>
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  <p className={cn("text-xs mt-1.5", msg.role === "user" ? "text-violet-200" : "text-muted-foreground")}>
                    {msg.timestamp.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}

        {(loading || uploadingFiles) && (
          <div className="flex justify-start">
            <div className={`w-7 h-7 rounded-xl bg-gradient-to-br ${gradientClass} flex items-center justify-center mr-2 mt-0.5`}>
              <span className="text-white text-xs font-bold">IA</span>
            </div>
            <div className="bg-card border border-border/50 px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {uploadingFiles ? "Enviando arquivos..." : "Processando..."}
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Pending files preview */}
      {pendingFiles.length > 0 && (
        <div className="px-6 py-3 border-t border-border/50 bg-secondary/30">
          <p className="text-xs text-muted-foreground mb-2">{pendingFiles.length} arquivo(s) prontos para envio:</p>
          <div className="flex flex-wrap gap-2">
            {pendingFiles.map((file, i) => (
              <div key={i} className="flex items-center gap-1.5 bg-secondary border border-border/50 rounded-lg px-2 py-1">
                {file.type.startsWith("image/") ? <Image className="w-3 h-3 text-violet-400" /> : <FileVideo className="w-3 h-3 text-blue-400" />}
                <span className="text-xs max-w-[120px] truncate">{file.name}</span>
                <button onClick={() => removePendingFile(i)} className="text-muted-foreground hover:text-foreground">
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="px-6 py-4 border-t border-border/50 bg-background">
        <div className="flex gap-2 items-end">
          {/* File upload button */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*,video/mp4,video/quicktime"
            className="hidden"
            onChange={handleFileSelect}
          />
          <Button
            variant="outline"
            size="icon"
            className="h-[52px] w-[52px] flex-shrink-0 border-border/50 hover:border-violet-500/50"
            onClick={() => fileInputRef.current?.click()}
            title="Enviar imagens ou vídeos"
          >
            <Paperclip className="w-4 h-4" />
          </Button>

          <Textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Mensagem para ${agentName}...`}
            className="resize-none min-h-[52px] max-h-32 text-sm flex-1"
            rows={1}
          />

          <Button
            onClick={() => sendMessage()}
            disabled={(!input.trim() && pendingFiles.length === 0) || loading || uploadingFiles}
            className="bg-violet-600 hover:bg-violet-700 h-[52px] w-[52px] flex-shrink-0"
          >
            {loading || uploadingFiles
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Send className="w-4 h-4" />}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Enter para enviar · Shift+Enter para nova linha · 📎 para enviar arquivos
        </p>
      </div>
    </div>
  );
}
