"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { API_BASE_URL, apiHeaders, readErrorMessage } from "@/lib/doc2action-api";

type KbCollection = {
  id: string;
  name: string;
  user_sub: string | null;
  created_at: string;
};

type KbDocument = {
  id: string;
  collection_id: string;
  title: string;
  created_at: string;
};

export default function KnowledgeBasePage() {
  const [collections, setCollections] = useState<KbCollection[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<KbDocument[]>([]);
  const [newCollectionName, setNewCollectionName] = useState("");
  const [docTitle, setDocTitle] = useState("");
  const [docContent, setDocContent] = useState("");
  const [listErr, setListErr] = useState("");
  const [actionErr, setActionErr] = useState("");
  const [loadingList, setLoadingList] = useState(true);
  const [savingCollection, setSavingCollection] = useState(false);
  const [savingDoc, setSavingDoc] = useState(false);

  const loadCollections = useCallback(async () => {
    setListErr("");
    setLoadingList(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/v1/kb/collections`, {
        headers: apiHeaders({ Accept: "application/json" })
      });
      if (!r.ok) {
        setListErr(await readErrorMessage(r));
        return;
      }
      const data: { items: KbCollection[] } = await r.json();
      setCollections(data.items ?? []);
      setSelectedId((prev) => {
        if (prev && data.items?.some((c) => c.id === prev)) {
          return prev;
        }
        return data.items?.[0]?.id ?? null;
      });
    } catch (e) {
      setListErr(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoadingList(false);
    }
  }, []);

  const loadDocuments = useCallback(async (collectionId: string) => {
    setActionErr("");
    try {
      const r = await fetch(`${API_BASE_URL}/api/v1/kb/collections/${collectionId}/documents`, {
        headers: apiHeaders({ Accept: "application/json" })
      });
      if (!r.ok) {
        setActionErr(await readErrorMessage(r));
        setDocuments([]);
        return;
      }
      const data: { items: KbDocument[] } = await r.json();
      setDocuments(data.items ?? []);
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : "加载文档失败");
      setDocuments([]);
    }
  }, []);

  useEffect(() => {
    void loadCollections();
  }, [loadCollections]);

  useEffect(() => {
    if (selectedId) {
      void loadDocuments(selectedId);
    } else {
      setDocuments([]);
    }
  }, [selectedId, loadDocuments]);

  const createCollection = async () => {
    const name = newCollectionName.trim();
    if (!name) {
      return;
    }
    setSavingCollection(true);
    setActionErr("");
    try {
      const r = await fetch(`${API_BASE_URL}/api/v1/kb/collections`, {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json", Accept: "application/json" }),
        body: JSON.stringify({ name })
      });
      if (!r.ok) {
        setActionErr(await readErrorMessage(r));
        return;
      }
      const created: KbCollection = await r.json();
      setNewCollectionName("");
      await loadCollections();
      setSelectedId(created.id);
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : "创建失败");
    } finally {
      setSavingCollection(false);
    }
  };

  const addDocument = async () => {
    if (!selectedId) {
      return;
    }
    const title = docTitle.trim();
    const content = docContent.trim();
    if (!title || !content) {
      setActionErr("请填写标题与正文");
      return;
    }
    setSavingDoc(true);
    setActionErr("");
    try {
      const r = await fetch(`${API_BASE_URL}/api/v1/kb/collections/${selectedId}/documents`, {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json", Accept: "application/json" }),
        body: JSON.stringify({ title, content })
      });
      if (!r.ok) {
        setActionErr(await readErrorMessage(r));
        return;
      }
      setDocTitle("");
      setDocContent("");
      await loadDocuments(selectedId);
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : "添加失败");
    } finally {
      setSavingDoc(false);
    }
  };

  const selected = collections.find((c) => c.id === selectedId);

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">知识库</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
            创建文档集合，在{" "}
            <Link href="/" className="font-medium text-indigo-600 hover:text-indigo-800">
              工作台
            </Link>{" "}
            启用 RAG 时可选择知识库，检索片段会并入分析提示。
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadCollections()}
          className="self-start rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm hover:bg-slate-50"
        >
          刷新列表
        </button>
      </div>

      {listErr && (
        <div className="mt-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {listErr}
        </div>
      )}
      {actionErr && (
        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {actionErr}
        </div>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-12">
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm lg:col-span-4">
          <h2 className="text-lg font-semibold text-slate-800">集合</h2>
          <div className="mt-4 flex gap-2">
            <input
              className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              placeholder="新集合名称"
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  void createCollection();
                }
              }}
            />
            <button
              type="button"
              disabled={savingCollection || !newCollectionName.trim()}
              onClick={() => void createCollection()}
              className="shrink-0 rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:bg-slate-400"
            >
              新建
            </button>
          </div>
          <div className="mt-4 max-h-[28rem] space-y-1 overflow-y-auto">
            {loadingList && <p className="text-sm text-slate-500">加载中…</p>}
            {!loadingList && collections.length === 0 && (
              <p className="text-sm text-slate-500">暂无集合，先新建一个。</p>
            )}
            {collections.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setSelectedId(c.id)}
                className={`flex w-full flex-col rounded-lg border px-3 py-2.5 text-left text-sm transition ${
                  c.id === selectedId
                    ? "border-indigo-300 bg-indigo-50/80 text-indigo-950"
                    : "border-transparent bg-slate-50 hover:border-slate-200 hover:bg-white"
                }`}
              >
                <span className="font-medium">{c.name}</span>
                <span className="mt-0.5 font-mono text-[11px] text-slate-500">{c.id.slice(0, 8)}…</span>
              </button>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm lg:col-span-8">
          {selected ? (
            <>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="text-lg font-semibold text-slate-800">{selected.name}</h2>
                <span className="font-mono text-xs text-slate-500">{selected.id}</span>
              </div>

              <div className="mt-6 rounded-xl border border-slate-100 bg-slate-50/80 p-4">
                <h3 className="text-sm font-semibold text-slate-800">添加文档</h3>
                <input
                  className="mt-3 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  placeholder="标题"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                />
                <textarea
                  className="mt-2 min-h-32 w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  placeholder="正文（将按语义切块参与 RAG）"
                  value={docContent}
                  onChange={(e) => setDocContent(e.target.value)}
                />
                <button
                  type="button"
                  disabled={savingDoc || !docTitle.trim() || !docContent.trim()}
                  onClick={() => void addDocument()}
                  className="mt-3 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-slate-400"
                >
                  {savingDoc ? "保存中…" : "添加文档"}
                </button>
              </div>

              <div className="mt-6">
                <h3 className="text-sm font-semibold text-slate-800">文档列表</h3>
                {documents.length === 0 ? (
                  <p className="mt-2 text-sm text-slate-500">暂无文档。</p>
                ) : (
                  <ul className="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-100">
                    {documents.map((d) => (
                      <li key={d.id} className="flex flex-col gap-0.5 px-4 py-3 text-sm">
                        <span className="font-medium text-slate-900">{d.title}</span>
                        <span className="font-mono text-xs text-slate-500">
                          {d.id.slice(0, 8)}… · {d.created_at}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">请选择左侧集合，或先新建一个。</p>
          )}
        </section>
      </div>
    </main>
  );
}
