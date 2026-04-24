"use client";

import { ChangeEvent, useCallback, useEffect, useMemo, useState } from "react";

import { API_BASE_URL, apiHeaders, readErrorMessage } from "@/lib/doc2action-api";

type HealthResponse = {
  status: string;
  service: string;
};

type AnalyzeRequestBody = {
  text: string;
  document_type: string;
  use_rag?: boolean;
  use_semantic_chunks?: boolean;
  kb_collection_id?: string;
};

type ExtractorMode = "auto" | "rules" | "llm" | "lora";

type Chunk = {
  id: number;
  text: string;
};

type ActionItem = {
  title: string;
  priority: string;
  source_chunk_ids: number[];
};

type RiskItem = {
  description: string;
  severity: string;
  source_chunk_ids: number[];
};

type OpenQuestion = {
  question: string;
  source_chunk_ids: number[];
};

type AnalyzeResponse = {
  summary: string;
  action_items: ActionItem[];
  risks: RiskItem[];
  open_questions: OpenQuestion[];
  chunks: Chunk[];
  meta: {
    document_type: string;
    chunk_count: number;
    used_llm: boolean;
    used_lora?: boolean;
    extractor_mode?: string;
    llm_fallback?: boolean;
    lora_fallback?: boolean;
    semantic_chunks?: boolean;
    rag_enabled?: boolean;
    rag_applied?: boolean;
    rag_reason?: string;
    rag_top_k?: number;
    rag_prompt_char_budget?: number;
    rag_embedding_model?: string;
    rag_selected_positions?: number[];
    rag_embed_cache_enabled?: boolean;
    llm_prompt_chunks?: { id: number; text: string }[];
    llm_prompt_chunk_count?: number;
    llm_prompt_char_count?: number;
    llm_saw_prompt_chunks?: boolean;
  };
};

type EvidenceTarget = {
  kind: "action_item" | "risk" | "open_question";
  index: number;
  label: string;
  sourceChunkIds: number[];
};

type AnalysisRunRow = {
  run_id: string;
  run_kind: string;
  user_sub: string | null;
  status: string;
  document_type: string | null;
  extractor_mode: string | null;
  text_preview: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
  result_bytes: number;
};

type KbCollectionRow = {
  id: string;
  name: string;
  user_sub: string | null;
  created_at: string;
};

/** 异步任务轮询：长文本 + LLM 常超过 1～2 分钟，默认约 10 分钟上限 */
const JOB_POLL_INTERVAL_MS = 800;
const JOB_POLL_MAX_ROUNDS = 750;

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string>("");

  const [inputText, setInputText] = useState("");
  const [documentType, setDocumentType] = useState("general");
  const [extractorMode, setExtractorMode] = useState<ExtractorMode>("auto");
  /** 本次请求启用 RAG（语义切块 + 向量检索片段，需后端 OPENAI_API_KEY） */
  const [useRag, setUseRag] = useState(false);
  /** 仅语义切块，不做向量检索（可与「关闭 RAG」组合，用于对比切块效果） */
  const [semanticChunksOnly, setSemanticChunksOnly] = useState(false);
  /** 走 POST /api/v1/jobs/analyze 并轮询（配置 Redis+RQ 时可多进程执行） */
  const [useAsyncQueue, setUseAsyncQueue] = useState(false);
  const [jobStatusLine, setJobStatusLine] = useState("");
  const [selectedFileName, setSelectedFileName] = useState("");

  const [editableResult, setEditableResult] = useState<AnalyzeResponse | null>(null);
  const [analyzeError, setAnalyzeError] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceTarget | null>(null);
  const isLoraMode = extractorMode === "lora";

  const [kbCollections, setKbCollections] = useState<KbCollectionRow[]>([]);
  const [kbCollectionId, setKbCollectionId] = useState("");
  const [recentItems, setRecentItems] = useState<AnalysisRunRow[]>([]);

  const refreshRecent = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analyses/recent?limit=8`, {
        headers: apiHeaders()
      });
      if (!response.ok) {
        return;
      }
      const data: { items: AnalysisRunRow[] } = await response.json();
      setRecentItems(data.items ?? []);
    } catch {
      /* ignore */
    }
  }, []);

  const refreshKbCollections = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/kb/collections`, {
        headers: apiHeaders({ Accept: "application/json" })
      });
      if (!response.ok) {
        return;
      }
      const data: { items: KbCollectionRow[] } = await response.json();
      setKbCollections(data.items ?? []);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void refreshKbCollections();
  }, [refreshKbCollections]);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`, {
          headers: apiHeaders()
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data: HealthResponse = await response.json();
        setHealth(data);
        await refreshRecent();
      } catch (err) {
        setHealthError(err instanceof Error ? err.message : "unknown error");
      }
    };

    checkHealth();
  }, [refreshRecent]);

  const canAnalyze = useMemo(() => inputText.trim().length > 0 && !isAnalyzing, [inputText, isAnalyzing]);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setSelectedFileName(file.name);
    const text = await file.text();
    setInputText(text);
  };

  const runAnalyze = async () => {
    if (!canAnalyze) {
      return;
    }
    setAnalyzeError("");
    setJobStatusLine("");
    setEditableResult(null);
    setSelectedEvidence(null);
    setIsAnalyzing(true);

    const payload: AnalyzeRequestBody = {
      text: inputText,
      document_type: documentType
    };
    if (useRag) {
      payload.use_rag = true;
      if (kbCollectionId.trim()) {
        payload.kb_collection_id = kbCollectionId.trim();
      }
    } else if (semanticChunksOnly) {
      payload.use_semantic_chunks = true;
      payload.use_rag = false;
    }

    try {
      if (useAsyncQueue) {
        const submit = await fetch(`${API_BASE_URL}/api/v1/jobs/analyze`, {
          method: "POST",
          headers: apiHeaders({
            "Content-Type": "application/json",
            "X-Extractor-Mode": extractorMode
          }),
          body: JSON.stringify(payload)
        });
        if (!submit.ok) {
          throw new Error(await readErrorMessage(submit));
        }
        const enq: { job_id: string; status: string } = await submit.json();
        const { job_id: jobId } = enq;
        let completed = false;
        const pollMinutesMax = Math.round(
          (JOB_POLL_MAX_ROUNDS * JOB_POLL_INTERVAL_MS) / 60000
        );
        for (let i = 0; i < JOB_POLL_MAX_ROUNDS; i++) {
          setJobStatusLine(
            `异步任务已提交，轮询中…（${jobId.slice(0, 8)}…）约 ${i + 1}/${JOB_POLL_MAX_ROUNDS} 次 · 最长等待约 ${pollMinutesMax} 分钟`
          );
          const poll = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`, {
            headers: apiHeaders()
          });
          if (!poll.ok) {
            throw new Error(await readErrorMessage(poll));
          }
          const st: {
            status: string;
            result?: AnalyzeResponse;
            error?: string | null;
          } = await poll.json();
          if (st.status === "completed" && st.result) {
            setEditableResult(st.result);
            completed = true;
            break;
          }
          if (st.status === "failed") {
            throw new Error(st.error || "异步任务失败");
          }
          await new Promise((r) => setTimeout(r, JOB_POLL_INTERVAL_MS));
        }
        if (!completed) {
          throw new Error(
            `等待异步结果超时（前端已轮询约 ${pollMinutesMax} 分钟）。长文档 + Auto/LLM 在后台常要更久。请确认：① 另开终端已运行 cd backend && python -m app.rq_worker；② DevTools 里该 job 的 status 是否长期为 running（说明仍在执行）。也可改用同步 Analyze 或先缩短文本试跑。`
          );
        }
        setJobStatusLine("");
      } else {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
          method: "POST",
          headers: apiHeaders({
            "Content-Type": "application/json",
            "X-Extractor-Mode": extractorMode
          }),
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          throw new Error(await readErrorMessage(response));
        }

        const data: AnalyzeResponse = await response.json();
        setEditableResult(data);
      }
    } catch (err) {
      setAnalyzeError(err instanceof Error ? err.message : "unknown error");
    } finally {
      setIsAnalyzing(false);
      setJobStatusLine("");
      void refreshRecent();
    }
  };

  const evidenceChunks = useMemo(() => {
    if (!editableResult || !selectedEvidence) {
      return [];
    }
    return editableResult.chunks.filter((chunk) => selectedEvidence.sourceChunkIds.includes(chunk.id));
  }, [editableResult, selectedEvidence]);

  const updateSummary = (newSummary: string) => {
    if (!editableResult) {
      return;
    }
    setEditableResult({
      ...editableResult,
      summary: newSummary
    });
  };

  const updateActionItemTitle = (index: number, title: string) => {
    if (!editableResult) {
      return;
    }
    const updated = editableResult.action_items.map((item, itemIndex) =>
      itemIndex === index ? { ...item, title } : item
    );
    setEditableResult({
      ...editableResult,
      action_items: updated
    });
  };

  const updateActionItemPriority = (index: number, priority: string) => {
    if (!editableResult) {
      return;
    }
    const updated = editableResult.action_items.map((item, itemIndex) =>
      itemIndex === index ? { ...item, priority } : item
    );
    setEditableResult({
      ...editableResult,
      action_items: updated
    });
  };

  const deleteActionItem = (index: number) => {
    if (!editableResult) {
      return;
    }
    setEditableResult({
      ...editableResult,
      action_items: editableResult.action_items.filter((_, itemIndex) => itemIndex !== index)
    });
    if (selectedEvidence?.kind === "action_item" && selectedEvidence.index === index) {
      setSelectedEvidence(null);
    }
  };

  const addActionItem = () => {
    if (!editableResult) {
      return;
    }
    setEditableResult({
      ...editableResult,
      action_items: [
        ...editableResult.action_items,
        {
          title: "New action item",
          priority: "medium",
          source_chunk_ids: []
        }
      ]
    });
  };

  const updateRiskDescription = (index: number, description: string) => {
    if (!editableResult) {
      return;
    }
    const updated = editableResult.risks.map((item, itemIndex) =>
      itemIndex === index ? { ...item, description } : item
    );
    setEditableResult({ ...editableResult, risks: updated });
    if (selectedEvidence?.kind === "risk" && selectedEvidence.index === index) {
      setSelectedEvidence({ ...selectedEvidence, label: description });
    }
  };

  const updateRiskSeverity = (index: number, severity: string) => {
    if (!editableResult) {
      return;
    }
    const updated = editableResult.risks.map((item, itemIndex) =>
      itemIndex === index ? { ...item, severity } : item
    );
    setEditableResult({ ...editableResult, risks: updated });
  };

  const deleteRisk = (index: number) => {
    if (!editableResult) {
      return;
    }
    setEditableResult({
      ...editableResult,
      risks: editableResult.risks.filter((_, itemIndex) => itemIndex !== index)
    });
    if (selectedEvidence?.kind === "risk" && selectedEvidence.index === index) {
      setSelectedEvidence(null);
    }
  };

  const addRisk = () => {
    if (!editableResult) {
      return;
    }
    setEditableResult({
      ...editableResult,
      risks: [
        ...editableResult.risks,
        { description: "New risk", severity: "medium", source_chunk_ids: [] }
      ]
    });
  };

  const updateOpenQuestion = (index: number, question: string) => {
    if (!editableResult) {
      return;
    }
    const updated = editableResult.open_questions.map((item, itemIndex) =>
      itemIndex === index ? { ...item, question } : item
    );
    setEditableResult({ ...editableResult, open_questions: updated });
    if (selectedEvidence?.kind === "open_question" && selectedEvidence.index === index) {
      setSelectedEvidence({ ...selectedEvidence, label: question });
    }
  };

  const deleteOpenQuestion = (index: number) => {
    if (!editableResult) {
      return;
    }
    setEditableResult({
      ...editableResult,
      open_questions: editableResult.open_questions.filter((_, itemIndex) => itemIndex !== index)
    });
    if (selectedEvidence?.kind === "open_question" && selectedEvidence.index === index) {
      setSelectedEvidence(null);
    }
  };

  const addOpenQuestion = () => {
    if (!editableResult) {
      return;
    }
    setEditableResult({
      ...editableResult,
      open_questions: [
        ...editableResult.open_questions,
        { question: "New open question", source_chunk_ids: [] }
      ]
    });
  };

  const toMarkdown = (data: AnalyzeResponse) => {
    const actionLines =
      data.action_items.length > 0
        ? data.action_items
          .map((item, index) => {
            const source = item.source_chunk_ids.length > 0 ? item.source_chunk_ids.join(", ") : "-";
            return `${index + 1}. ${item.title} (priority: ${item.priority}, sources: ${source})`;
          })
          .join("\n")
        : "暂无 action items";

    const riskLines =
      data.risks.length > 0
        ? data.risks
          .map((item, index) => {
            const source = item.source_chunk_ids.length > 0 ? item.source_chunk_ids.join(", ") : "-";
            return `${index + 1}. ${item.description} (severity: ${item.severity}, sources: ${source})`;
          })
          .join("\n")
        : "暂无风险项";

    const questionLines =
      data.open_questions.length > 0
        ? data.open_questions
          .map((item, index) => {
            const source = item.source_chunk_ids.length > 0 ? item.source_chunk_ids.join(", ") : "-";
            return `${index + 1}. ${item.question} (sources: ${source})`;
          })
          .join("\n")
        : "暂无待确认问题";

    return [
      "# Doc2Action Export",
      "",
      "## Summary",
      data.summary || "暂无 summary",
      "",
      "## Action Items",
      actionLines,
      "",
      "## Risks",
      riskLines,
      "",
      "## Open Questions",
      questionLines,
      "",
      "## Meta",
      `- document_type: ${data.meta.document_type}`,
      `- chunk_count: ${data.meta.chunk_count}`,
      `- used_llm: ${String(data.meta.used_llm)}`,
      ...(data.meta.used_lora != null
        ? [`- used_lora: ${String(data.meta.used_lora)}`]
        : []),
      ...(data.meta.extractor_mode != null
        ? [`- extractor_mode: ${data.meta.extractor_mode}`]
        : []),
      ...(data.meta.llm_fallback != null
        ? [`- llm_fallback: ${String(data.meta.llm_fallback)}`]
        : []),
      ...(data.meta.lora_fallback != null
        ? [`- lora_fallback: ${String(data.meta.lora_fallback)}`]
        : []),
      ...(data.meta.semantic_chunks != null
        ? [`- semantic_chunks: ${String(data.meta.semantic_chunks)}`]
        : []),
      ...(data.meta.rag_enabled != null ? [`- rag_enabled: ${String(data.meta.rag_enabled)}`] : []),
      ...(data.meta.rag_applied != null ? [`- rag_applied: ${String(data.meta.rag_applied)}`] : []),
      ...(data.meta.rag_reason != null ? [`- rag_reason: ${data.meta.rag_reason}`] : []),
      ...(data.meta.rag_embed_cache_enabled != null
        ? [`- rag_embed_cache_enabled: ${String(data.meta.rag_embed_cache_enabled)}`]
        : []),
      ...(data.meta.llm_saw_prompt_chunks != null
        ? [`- llm_saw_prompt_chunks: ${String(data.meta.llm_saw_prompt_chunks)}`]
        : []),
      ...(data.meta.llm_prompt_chunk_count != null
        ? [`- llm_prompt_chunk_count: ${data.meta.llm_prompt_chunk_count}`]
        : []),
      ...(data.meta.llm_prompt_chunks != null && data.meta.llm_prompt_chunks.length > 0
        ? [
          "",
          "## LLM 实际使用的片段",
          ...data.meta.llm_prompt_chunks.map(
            (c) => `### chunk_${c.id}\n\n${c.text}\n`
          )
        ]
        : [])
    ].join("\n");
  };

  const exportMarkdown = () => {
    if (!editableResult) {
      return;
    }
    const markdown = toMarkdown(editableResult);
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `doc2action-export-${Date.now()}.md`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  };

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-3xl font-bold">Doc2Action</h1>
      <p className="mt-2 text-slate-600">
        输入文档文本后，系统将返回结构化执行信息（Summary / Action Items / Risks / Open Questions）。
      </p>

      <section className="mt-8 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold">Backend Health</h2>
        <p className="mt-2 text-sm text-slate-500">
          API Base URL: <code>{API_BASE_URL}</code>
        </p>

        {health && (
          <div className="mt-4 rounded-md bg-emerald-50 p-4 text-emerald-700">
            <div>
              <strong>status:</strong> {health.status}
            </div>
            <div>
              <strong>service:</strong> {health.service}
            </div>
          </div>
        )}

        {healthError && (
          <div className="mt-4 rounded-md bg-rose-50 p-4 text-rose-700">
            <strong>health check failed:</strong> {healthError}
          </div>
        )}

        {!health && !healthError && (
          <div className="mt-4 rounded-md bg-slate-100 p-4 text-slate-700">
            正在检测后端服务状态...
          </div>
        )}

        <div className="mt-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">最近分析（SQLite）</h3>
            <button
              type="button"
              className="text-xs text-indigo-600 underline"
              onClick={() => void refreshRecent()}
            >
              刷新列表
            </button>
          </div>
          {recentItems.length === 0 ? (
            <p className="mt-2 text-xs text-slate-500">暂无记录；完成一次 Analyze 后自动刷新。</p>
          ) : (
            <ul className="mt-2 max-h-48 space-y-2 overflow-y-auto text-xs text-slate-700">
              {recentItems.map((row) => (
                <li key={row.run_id} className="rounded border border-slate-100 bg-white px-2 py-1.5">
                  <span className="font-mono text-[11px] text-slate-500">{row.run_id.slice(0, 8)}…</span>
                  {" · "}
                  <span className="font-medium">{row.status}</span>
                  {row.user_sub ? ` · ${row.user_sub}` : ""}
                  {row.document_type ? ` · ${row.document_type}` : ""}
                  {row.run_kind ? ` · ${row.run_kind}` : ""}
                  {row.text_preview ? (
                    <div className="mt-0.5 line-clamp-2 text-slate-500">{row.text_preview}</div>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold">Input</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              文档类型
            </label>
            <select
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              value={documentType}
              onChange={(event) => setDocumentType(event.target.value)}
            >
              <option value="general">General</option>
              <option value="meeting_notes">Meeting Notes</option>
              <option value="prd">PRD</option>
              <option value="email_thread">Email Thread</option>
              <option value="sop">SOP</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              推理模式
            </label>
            <select
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              value={extractorMode}
              onChange={(event) => setExtractorMode(event.target.value as ExtractorMode)}
            >
              <option value="auto">Auto（优先 LLM）</option>
              <option value="rules">Rules</option>
              <option value="llm">LLM API</option>
              <option value="lora">LoRA Local</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              上传文件（.txt / .md）
            </label>
            <input
              type="file"
              accept=".txt,.md,text/plain,text/markdown"
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              onChange={handleFileChange}
            />
            {selectedFileName && (
              <p className="mt-1 text-xs text-slate-500">已加载文件：{selectedFileName}</p>
            )}
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-6 rounded-md border border-slate-100 bg-slate-50/80 px-4 py-3 text-sm">
          <label className="inline-flex cursor-pointer items-center gap-2 text-slate-800">
            <input
              type="checkbox"
              className="rounded border-slate-300"
              checked={useRag}
              onChange={(event) => {
                const next = event.target.checked;
                setUseRag(next);
                if (next) {
                  setSemanticChunksOnly(false);
                }
              }}
            />
            启用 RAG（语义切块 + 检索最相关片段，需 OpenAI Embedding）
          </label>
          <label className="inline-flex cursor-pointer items-center gap-2 text-slate-800">
            <input
              type="checkbox"
              className="rounded border-slate-300"
              checked={semanticChunksOnly}
              disabled={useRag}
              onChange={(event) => {
                const next = event.target.checked;
                setSemanticChunksOnly(next);
                if (next) {
                  setUseRag(false);
                }
              }}
            />
            仅语义切块（不检索）
          </label>
          <label className="inline-flex cursor-pointer items-center gap-2 text-slate-800">
            <input
              type="checkbox"
              className="rounded border-slate-300"
              checked={useAsyncQueue}
              onChange={(event) => setUseAsyncQueue(event.target.checked)}
            />
            异步任务（后台队列，结果轮询展示）
          </label>
        </div>
        {useRag && (
          <div className="mt-3 flex flex-col gap-2 rounded-lg border border-indigo-100 bg-indigo-50/50 px-4 py-3 text-sm sm:flex-row sm:items-end sm:gap-4">
            <div className="min-w-0 flex-1">
              <label className="mb-1 block text-xs font-medium text-indigo-900/90">
                知识库（可选，与当前文档一起做 RAG 检索）
              </label>
              <select
                className="w-full rounded-md border border-indigo-200/80 bg-white px-3 py-2 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/25"
                value={kbCollectionId}
                onChange={(e) => setKbCollectionId(e.target.value)}
              >
                <option value="">不附加知识库（仅文档内检索）</option>
                {kbCollections.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              className="shrink-0 rounded-md border border-indigo-200 bg-white px-3 py-2 text-xs font-medium text-indigo-800 shadow-sm hover:bg-indigo-50"
              onClick={() => void refreshKbCollections()}
            >
              刷新知识库列表
            </button>
          </div>
        )}
        {useAsyncQueue && (
          <p className="mt-2 text-xs text-slate-600">
            未配置 Redis 时任务仍在当前后端进程内执行；配置 <code className="rounded bg-slate-100 px-1">DOC2ACTION_REDIS_URL</code>{" "}
            并运行 <code className="rounded bg-slate-100 px-1">python -m app.rq_worker</code> 可多进程消费队列。
          </p>
        )}

        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-slate-700">输入文本</label>
          <textarea
            className="min-h-48 w-full rounded-md border border-slate-300 p-3 text-sm"
            placeholder="粘贴会议纪要、PRD、邮件等文本..."
            value={inputText}
            onChange={(event) => setInputText(event.target.value)}
          />
        </div>

        <div className="mt-4 flex items-center gap-3">
          <button
            type="button"
            className="rounded-md bg-slate-900 px-4 py-2 text-white disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={!canAnalyze}
            onClick={runAnalyze}
          >
            {isAnalyzing ? "Analyzing..." : "Analyze"}
          </button>
          <span className="text-sm text-slate-500">
            {inputText.trim().length} chars
          </span>
        </div>
        {jobStatusLine && (
          <p className="mt-2 text-sm text-indigo-700">{jobStatusLine}</p>
        )}
        {isLoraMode && (
          <p className="mt-2 text-xs text-amber-700">
            LoRA Local 首次分析会加载本地模型，可能比 Rules/LLM 更慢；后续请求通常会更快。
          </p>
        )}
        {useRag && (extractorMode === "rules" || extractorMode === "lora") && (
          <p className="mt-2 text-xs text-slate-600">
            提示：RAG 主要影响「送给云端 LLM 的片段」；当前为 Rules / LoRA 时仍会返回语义切块与
            meta，但抽取未走 OpenAI 时检索增益有限。想用检索+LLM 时请选 Auto 或 LLM API。
          </p>
        )}

        {analyzeError && (
          <div className="mt-4 rounded-md bg-rose-50 p-4 text-rose-700">
            <strong>analyze failed:</strong> {analyzeError}
          </div>
        )}
      </section>

      <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold">Analysis Result</h2>
        {!editableResult && !isAnalyzing && (
          <p className="mt-3 text-slate-500">运行 Analyze 后将在这里显示结果。</p>
        )}
        {isAnalyzing && (
          <p className="mt-3 text-slate-600">正在生成结构化结果，请稍候...</p>
        )}

        {editableResult && (
          <div className="mt-4 grid gap-6 lg:grid-cols-3">
            <div className="space-y-5 lg:col-span-2">
              <div className="rounded-md bg-slate-50 p-4">
                <h3 className="font-semibold">Summary（可编辑）</h3>
                <textarea
                  className="mt-2 min-h-28 w-full rounded-md border border-slate-300 p-3 text-sm"
                  value={editableResult.summary}
                  onChange={(event) => updateSummary(event.target.value)}
                />
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Action Items（可编辑）</h3>
                  <button
                    type="button"
                    className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-50"
                    onClick={addActionItem}
                  >
                    + 新增
                  </button>
                </div>

                <ul className="mt-2 space-y-3">
                  {editableResult.action_items.map((item, index) => (
                    <li key={`action-${index}`} className="rounded-md border border-slate-200 p-3">
                      <div className="grid gap-2 md:grid-cols-6">
                        <input
                          className="rounded-md border border-slate-300 px-3 py-2 text-sm md:col-span-4"
                          value={item.title}
                          onChange={(event) => updateActionItemTitle(index, event.target.value)}
                        />
                        <select
                          className="rounded-md border border-slate-300 px-2 py-2 text-sm md:col-span-1"
                          value={item.priority}
                          onChange={(event) => updateActionItemPriority(index, event.target.value)}
                        >
                          <option value="high">high</option>
                          <option value="medium">medium</option>
                          <option value="low">low</option>
                        </select>
                        <button
                          type="button"
                          className="rounded-md border border-rose-300 px-2 py-2 text-sm text-rose-600 hover:bg-rose-50 md:col-span-1"
                          onClick={() => deleteActionItem(index)}
                        >
                          删除
                        </button>
                      </div>
                      <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                        <span>sources: {item.source_chunk_ids.join(", ") || "-"}</span>
                        <button
                          type="button"
                          className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
                          onClick={() =>
                            setSelectedEvidence({
                              kind: "action_item",
                              index,
                              label: item.title,
                              sourceChunkIds: item.source_chunk_ids
                            })
                          }
                        >
                          查看引用
                        </button>
                      </div>
                    </li>
                  ))}
                  {editableResult.action_items.length === 0 && (
                    <li className="text-sm text-slate-500">暂无 action items</li>
                  )}
                </ul>
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Risks（可编辑）</h3>
                  <button
                    type="button"
                    className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-50"
                    onClick={addRisk}
                  >
                    + 新增
                  </button>
                </div>
                <ul className="mt-2 space-y-3">
                  {editableResult.risks.map((risk, index) => (
                    <li key={`risk-${index}`} className="rounded-md border border-slate-200 p-3">
                      <div className="grid gap-2 md:grid-cols-6">
                        <input
                          className="rounded-md border border-slate-300 px-3 py-2 text-sm md:col-span-4"
                          value={risk.description}
                          onChange={(event) => updateRiskDescription(index, event.target.value)}
                        />
                        <select
                          className="rounded-md border border-slate-300 px-2 py-2 text-sm md:col-span-1"
                          value={risk.severity}
                          onChange={(event) => updateRiskSeverity(index, event.target.value)}
                        >
                          <option value="high">high</option>
                          <option value="medium">medium</option>
                          <option value="low">low</option>
                        </select>
                        <button
                          type="button"
                          className="rounded-md border border-rose-300 px-2 py-2 text-sm text-rose-600 hover:bg-rose-50 md:col-span-1"
                          onClick={() => deleteRisk(index)}
                        >
                          删除
                        </button>
                      </div>
                      <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                        <span>sources: {risk.source_chunk_ids.join(", ") || "-"}</span>
                        <button
                          type="button"
                          className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
                          onClick={() =>
                            setSelectedEvidence({
                              kind: "risk",
                              index,
                              label: risk.description,
                              sourceChunkIds: risk.source_chunk_ids
                            })
                          }
                        >
                          查看引用
                        </button>
                      </div>
                    </li>
                  ))}
                  {editableResult.risks.length === 0 && (
                    <li className="text-sm text-slate-500">暂无风险项</li>
                  )}
                </ul>
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Open Questions（可编辑）</h3>
                  <button
                    type="button"
                    className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-50"
                    onClick={addOpenQuestion}
                  >
                    + 新增
                  </button>
                </div>
                <ul className="mt-2 space-y-3">
                  {editableResult.open_questions.map((question, index) => (
                    <li key={`question-${index}`} className="rounded-md border border-slate-200 p-3">
                      <div className="grid gap-2 md:grid-cols-6">
                        <input
                          className="rounded-md border border-slate-300 px-3 py-2 text-sm md:col-span-5"
                          value={question.question}
                          onChange={(event) => updateOpenQuestion(index, event.target.value)}
                        />
                        <button
                          type="button"
                          className="rounded-md border border-rose-300 px-2 py-2 text-sm text-rose-600 hover:bg-rose-50 md:col-span-1"
                          onClick={() => deleteOpenQuestion(index)}
                        >
                          删除
                        </button>
                      </div>
                      <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                        <span>sources: {question.source_chunk_ids.join(", ") || "-"}</span>
                        <button
                          type="button"
                          className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
                          onClick={() =>
                            setSelectedEvidence({
                              kind: "open_question",
                              index,
                              label: question.question,
                              sourceChunkIds: question.source_chunk_ids
                            })
                          }
                        >
                          查看引用
                        </button>
                      </div>
                    </li>
                  ))}
                  {editableResult.open_questions.length === 0 && (
                    <li className="text-sm text-slate-500">暂无待确认问题</li>
                  )}
                </ul>
              </div>

              <div className="rounded-md bg-slate-50 p-4 text-xs text-slate-600">
                <div>document_type: {editableResult.meta.document_type}</div>
                <div>chunk_count: {editableResult.meta.chunk_count}</div>
                <div>used_llm: {String(editableResult.meta.used_llm)}</div>
                {editableResult.meta.used_lora != null && (
                  <div>used_lora: {String(editableResult.meta.used_lora)}</div>
                )}
                {editableResult.meta.extractor_mode != null && (
                  <div>extractor_mode: {editableResult.meta.extractor_mode}</div>
                )}
                {editableResult.meta.llm_fallback != null && (
                  <div>llm_fallback: {String(editableResult.meta.llm_fallback)}</div>
                )}
                {editableResult.meta.lora_fallback != null && (
                  <div>lora_fallback: {String(editableResult.meta.lora_fallback)}</div>
                )}
                {editableResult.meta.semantic_chunks != null && (
                  <div>semantic_chunks: {String(editableResult.meta.semantic_chunks)}</div>
                )}
                {editableResult.meta.rag_enabled != null && (
                  <div>rag_enabled: {String(editableResult.meta.rag_enabled)}</div>
                )}
                {editableResult.meta.rag_applied != null && (
                  <div>rag_applied: {String(editableResult.meta.rag_applied)}</div>
                )}
                {editableResult.meta.rag_reason != null && (
                  <div>rag_reason: {editableResult.meta.rag_reason}</div>
                )}
                {editableResult.meta.rag_selected_positions != null &&
                  editableResult.meta.rag_selected_positions.length > 0 && (
                    <div>rag_selected_positions: {editableResult.meta.rag_selected_positions.join(", ")}</div>
                  )}
                {editableResult.meta.rag_embed_cache_enabled != null && (
                  <div>rag_embed_cache_enabled: {String(editableResult.meta.rag_embed_cache_enabled)}</div>
                )}
                {editableResult.meta.llm_prompt_chunk_count != null && (
                  <div>
                    llm_prompt: {editableResult.meta.llm_prompt_chunk_count} chunks,{" "}
                    {editableResult.meta.llm_prompt_char_count ?? "?"} chars, saw_by_llm:{" "}
                    {String(editableResult.meta.llm_saw_prompt_chunks ?? false)}
                  </div>
                )}
                {editableResult.meta.extractor_mode === "lora" &&
                  editableResult.meta.lora_fallback === true && (
                    <div className="mt-1 text-rose-600">
                      提示：本次 LoRA 解析失败，已自动回退到 Rules。
                    </div>
                  )}
              </div>

              {editableResult.meta.llm_prompt_chunks != null &&
                editableResult.meta.llm_prompt_chunks.length > 0 && (
                  <details className="rounded-md border border-indigo-200 bg-indigo-50/60 p-4 text-sm text-slate-800">
                    <summary className="cursor-pointer select-none font-medium text-indigo-900">
                      LLM 实际使用的片段（{editableResult.meta.llm_prompt_chunk_count ?? "?"} 块
                      {editableResult.meta.llm_saw_prompt_chunks
                        ? "，已调用 LLM"
                        : "，未调用 LLM — 以下为构建 prompt 用的片段，供对照 Rules/LoRA"}
                      ）
                    </summary>
                    <div className="mt-3 max-h-96 space-y-4 overflow-y-auto">
                      {editableResult.meta.llm_prompt_chunks.map((c) => (
                        <div key={`llm-chunk-${c.id}`} className="rounded-md border border-white/80 bg-white/90 p-3">
                          <div className="mb-1 text-xs font-semibold text-indigo-800">chunk #{c.id}</div>
                          <pre className="whitespace-pre-wrap break-words font-sans text-xs leading-relaxed text-slate-700">
                            {c.text}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </details>
                )}

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  className="rounded-md bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700"
                  onClick={exportMarkdown}
                >
                  导出 Markdown
                </button>
                <span className="text-xs text-slate-500">导出当前编辑后的结果</span>
              </div>
            </div>

            <aside className="rounded-md border border-slate-200 bg-slate-50 p-4 lg:sticky lg:top-6 lg:h-fit">
              <h3 className="font-semibold">引用依据</h3>
              <p className="mt-1 text-xs text-slate-500">
                点击各条旁边的「查看引用」，在下方显示对应 chunk 原文。
              </p>

              {!selectedEvidence && (
                <div className="mt-3 rounded-md bg-white p-3 text-sm text-slate-500">
                  请选择左侧任一条目查看引用依据。
                </div>
              )}

              {selectedEvidence && (
                <div className="mt-3 space-y-3">
                  <div className="rounded-md bg-white p-3">
                    <div className="text-xs uppercase tracking-wide text-slate-500">
                      {selectedEvidence.kind}
                    </div>
                    <div className="mt-1 text-sm text-slate-800">{selectedEvidence.label}</div>
                    <div className="mt-2 text-xs text-slate-500">
                      source ids: {selectedEvidence.sourceChunkIds.join(", ") || "-"}
                    </div>
                  </div>

                  {selectedEvidence.sourceChunkIds.length === 0 && (
                    <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-700">
                      该条目暂未返回引用，请在后续编辑阶段人工补充确认。
                    </div>
                  )}

                  {selectedEvidence.sourceChunkIds.length > 0 && evidenceChunks.length === 0 && (
                    <div className="rounded-md bg-rose-50 p-3 text-sm text-rose-700">
                      source ids 无法映射到现有 chunk，请检查后端引用映射逻辑。
                    </div>
                  )}

                  {evidenceChunks.map((chunk) => (
                    <div key={`chunk-${chunk.id}`} className="rounded-md bg-white p-3">
                      <div className="text-xs font-semibold text-slate-600">chunk #{chunk.id}</div>
                      <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{chunk.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </aside>
          </div>
        )}
      </section>
    </main>
  );
}
