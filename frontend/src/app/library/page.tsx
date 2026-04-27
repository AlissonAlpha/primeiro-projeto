"use client";

import { useState, useEffect } from "react";
import {
  FolderOpen, Folder, ImageIcon, ArrowLeft, Download,
  ExternalLink, RefreshCw, ChevronRight, Trash2, X, AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface FolderItem { name: string; path: string; }
interface FileItem { name: string; path: string; url: string; size: number; created_at: string; }
interface FilesResponse { prefix: string; files: FileItem[]; sub_folders: FolderItem[]; total_files: number; }

export default function LibraryPage() {
  const [prefix, setPrefix] = useState("");
  const [data, setData] = useState<FilesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<FileItem | null>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<{ name: string; prefix: string }[]>([]);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ type: "file" | "folder"; target: FileItem | FolderItem } | null>(null);

  async function loadFiles(p: string) {
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/library/files?prefix=${encodeURIComponent(p)}`);
      setData(await r.json());
    } catch {}
    setLoading(false);
  }

  useEffect(() => { loadFiles(prefix); }, [prefix]);

  function navigateTo(path: string, name: string) {
    setPrefix(path);
    setSelected(null);
    setBreadcrumbs(prev => [...prev, { name, prefix: path }]);
  }

  function navigateToBreadcrumb(idx: number) {
    setBreadcrumbs(prev => prev.slice(0, idx + 1));
    setPrefix(breadcrumbs[idx].prefix);
    setSelected(null);
  }

  function goRoot() {
    setPrefix(""); setBreadcrumbs([]); setSelected(null);
  }

  async function deleteFile(file: FileItem) {
    setDeleting(file.path);
    try {
      await fetch(`${API_URL}/library/files`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ paths: [file.path] }),
      });
      setSelected(null);
      loadFiles(prefix);
    } catch {}
    setDeleting(null);
    setConfirmDelete(null);
  }

  async function deleteFolder(folder: FolderItem) {
    setDeleting(folder.path);
    try {
      await fetch(`${API_URL}/library/folder?prefix=${encodeURIComponent(folder.path)}`, { method: "DELETE" });
      loadFiles(prefix);
    } catch {}
    setDeleting(null);
    setConfirmDelete(null);
  }

  function formatSize(bytes: number) {
    if (!bytes) return "—";
    return bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)}MB` : `${(bytes / 1024).toFixed(0)}KB`;
  }

  const isImage = (name: string) => /\.(jpg|jpeg|png|webp|gif)$/i.test(name);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 border-r border-border/50 flex flex-col bg-card/30">
        <div className="px-4 py-4 border-b border-border/40">
          <h2 className="font-semibold text-sm">Biblioteca de Criativos</h2>
          <p className="text-xs text-muted-foreground mt-0.5">Imagens geradas por IA</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          <button onClick={goRoot}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${prefix === "" ? "bg-violet-500/10 text-violet-400" : "text-muted-foreground hover:bg-accent"}`}>
            <FolderOpen className="w-4 h-4" />Todos os criativos
          </button>
          {data?.sub_folders.map(f => (
            <button key={f.path} onClick={() => navigateTo(f.path, f.name)}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors mt-0.5 ${prefix === f.path ? "bg-violet-500/10 text-violet-400" : "text-muted-foreground hover:bg-accent"}`}>
              <Folder className="w-4 h-4" />{f.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div className="px-6 py-3 border-b border-border/40 flex items-center gap-2 flex-wrap">
          {breadcrumbs.length > 0 && (
            <button onClick={() => { const prev = breadcrumbs[breadcrumbs.length - 2]; prev ? navigateToBreadcrumb(breadcrumbs.length - 2) : goRoot(); }}
              className="text-muted-foreground hover:text-foreground transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <div className="flex items-center gap-1 text-sm">
            <button onClick={goRoot} className="text-muted-foreground hover:text-foreground">creatives</button>
            {breadcrumbs.map((c, i) => (
              <span key={i} className="flex items-center gap-1">
                <ChevronRight className="w-3 h-3 text-muted-foreground" />
                <button onClick={() => navigateToBreadcrumb(i)}
                  className={i === breadcrumbs.length - 1 ? "text-foreground font-medium" : "text-muted-foreground hover:text-foreground"}>
                  {c.name}
                </button>
              </span>
            ))}
          </div>
          <div className="ml-auto flex items-center gap-2">
            {data && <span className="text-xs text-muted-foreground">{data.total_files} arquivo(s)</span>}
            <Button variant="ghost" size="sm" onClick={() => loadFiles(prefix)} disabled={loading}>
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-6">
              {/* Folders */}
              {data?.sub_folders && data.sub_folders.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">Pastas</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                    {data.sub_folders.map(f => (
                      <div key={f.path} className="group relative">
                        <button onClick={() => navigateTo(f.path, f.name)}
                          className="w-full flex flex-col items-center gap-2 p-4 rounded-xl border border-border/40 hover:border-violet-500/40 hover:bg-violet-500/5 transition-all text-center">
                          <FolderOpen className="w-10 h-10 text-amber-400 group-hover:text-amber-300 transition-colors" />
                          <span className="text-xs font-medium truncate w-full">{f.name}</span>
                        </button>
                        {/* Delete folder button */}
                        <button
                          onClick={e => { e.stopPropagation(); setConfirmDelete({ type: "folder", target: f }); }}
                          className="absolute top-2 right-2 w-6 h-6 rounded-lg bg-background/80 border border-border/50 flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-red-500/10 hover:border-red-500/40 hover:text-red-400 transition-all text-muted-foreground"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Files */}
              {data?.files && data.files.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">Imagens</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                    {data.files.map(file => (
                      <div key={file.path} className="group relative">
                        <button onClick={() => setSelected(file)}
                          className={`relative w-full rounded-xl overflow-hidden border-2 transition-all aspect-square ${selected?.path === file.path ? "border-violet-500" : "border-transparent hover:border-violet-500/40"}`}>
                          {isImage(file.name)
                            ? <img src={file.url} alt={file.name} className="w-full h-full object-cover" />
                            : <div className="w-full h-full bg-muted/50 flex items-center justify-center"><ImageIcon className="w-8 h-8 text-muted-foreground" /></div>}
                          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all" />
                          <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-all">
                            <p className="text-xs text-white truncate">{file.name}</p>
                          </div>
                        </button>
                        {/* Delete file button */}
                        <button
                          onClick={e => { e.stopPropagation(); setConfirmDelete({ type: "file", target: file }); }}
                          className="absolute top-1.5 right-1.5 w-6 h-6 rounded-lg bg-background/80 border border-border/50 flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-red-500/10 hover:border-red-500/40 hover:text-red-400 transition-all text-muted-foreground"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(!data?.files?.length && !data?.sub_folders?.length) && (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                  <FolderOpen className="w-12 h-12 text-muted-foreground/30 mb-3" />
                  <p className="text-muted-foreground">Pasta vazia</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="w-72 border-l border-border/50 flex flex-col bg-card/30">
          <div className="px-4 py-3 border-b border-border/40 flex items-center justify-between">
            <span className="text-sm font-medium">Detalhes</span>
            <button onClick={() => setSelected(null)} className="text-muted-foreground hover:text-foreground text-lg leading-none">×</button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {isImage(selected.name) && (
              <img src={selected.url} alt={selected.name} className="w-full rounded-xl border border-border/40" />
            )}
            <div className="space-y-2">
              <div><p className="text-xs text-muted-foreground">Nome</p><p className="text-sm font-medium break-all">{selected.name}</p></div>
              <div><p className="text-xs text-muted-foreground">Pasta</p><p className="text-xs text-muted-foreground font-mono break-all">{selected.path.replace(selected.name, "")}</p></div>
              {selected.size > 0 && <div><p className="text-xs text-muted-foreground">Tamanho</p><p className="text-sm">{formatSize(selected.size)}</p></div>}
              {selected.created_at && <div><p className="text-xs text-muted-foreground">Criado em</p><p className="text-sm">{new Date(selected.created_at).toLocaleDateString("pt-BR")}</p></div>}
            </div>
            <div className="space-y-2 pt-2">
              <a href={selected.url} target="_blank" rel="noopener noreferrer" className="w-full">
                <Button variant="outline" size="sm" className="w-full gap-2"><ExternalLink className="w-3.5 h-3.5" />Ver imagem</Button>
              </a>
              <a href={selected.url} download className="w-full">
                <Button size="sm" className="w-full gap-2 bg-violet-600 hover:bg-violet-700"><Download className="w-3.5 h-3.5" />Baixar</Button>
              </a>
              <Button
                size="sm" variant="outline"
                className="w-full gap-2 border-red-500/30 text-red-400 hover:bg-red-500/10 hover:border-red-500/50"
                onClick={() => setConfirmDelete({ type: "file", target: selected })}
              >
                <Trash2 className="w-3.5 h-3.5" />Excluir
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm delete modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-popover border border-border rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <p className="font-semibold text-sm">
                  {confirmDelete.type === "folder" ? "Excluir pasta?" : "Excluir imagem?"}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {confirmDelete.type === "folder"
                    ? "Todos os arquivos dentro serão excluídos permanentemente."
                    : "A imagem será excluída permanentemente."}
                </p>
              </div>
            </div>
            <div className="bg-muted/30 rounded-lg px-3 py-2 mb-5">
              <p className="text-xs font-mono text-muted-foreground break-all">
                {(confirmDelete.target as FileItem).path || (confirmDelete.target as FolderItem).path}
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="flex-1" onClick={() => setConfirmDelete(null)}>
                Cancelar
              </Button>
              <Button
                size="sm"
                className="flex-1 bg-red-600 hover:bg-red-700 gap-2"
                disabled={!!deleting}
                onClick={() => {
                  if (confirmDelete.type === "file") deleteFile(confirmDelete.target as FileItem);
                  else deleteFolder(confirmDelete.target as FolderItem);
                }}
              >
                {deleting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                Excluir
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
