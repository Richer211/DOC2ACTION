"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { API_BASE_URL, apiHeaders } from "@/lib/doc2action-api";

type EvalSummary = {
  exists: boolean;
  source_file: string;
  aggregate: Record<string, string | number>;
  excerpt: string;
  hint: string | null;
};

export default function EvalSummaryPage() {
  const [data, setData] = useState<EvalSummary | null>(null);
  const [err, setErr] = useState("");
  const [fullMd, setFullMd] = useState<string | null>(null);
  const [fullErr, setFullErr] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`${API_BASE_URL}/api/v1/eval/summary`, { headers: apiHeaders() });
        if (!r.ok) {
          setErr(`HTTP ${r.status}`);
          return;
        }
        setData(await r.json());
      } catch (e) {
        setErr(e instanceof Error ? e.message : "load failed");
      }
    };
    void load();
  }, []);

  const loadFullReport = async () => {
    setFullErr("");
    setFullMd(null);
    try {
      const r = await fetch(`${API_BASE_URL}/api/v1/eval/report.md`, { headers: apiHeaders() });
      if (!r.ok) {
        setFullErr(`HTTP ${r.status}`);
        return;
      }
      setFullMd(await r.text());
    } catch (e) {
      setFullErr(e instanceof Error ? e.message : "failed");
    }
  };

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <Link href="/" className="text-sm text-indigo-600 underline">
        ← 返回工作台
      </Link>
      <h1 className="mt-4 text-2xl font-bold">评测摘要</h1>
      <p className="mt-2 text-sm text-slate-600">
        数据来自离线脚本 <code className="rounded bg-slate-100 px-1">ml/eval/evaluate.py</code> 生成的 Markdown（默认{" "}
        <code className="rounded bg-slate-100 px-1">baseline-eval.md</code>）。需与后端相同鉴权（JWT 或 API Key）。
      </p>

      {err && (
        <div className="mt-4 rounded-md bg-rose-50 p-4 text-sm text-rose-700">
          加载失败：{err}
        </div>
      )}

      {data && !data.exists && (
        <div className="mt-4 rounded-md bg-amber-50 p-4 text-sm text-amber-900">
          {data.hint ?? "报告文件不存在。"}
          <div className="mt-2 text-xs text-slate-600">期望路径：{data.source_file}</div>
        </div>
      )}

      {data && data.exists && (
        <div className="mt-6 space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="font-semibold text-slate-800">Aggregate Metrics</h2>
            <ul className="mt-2 grid gap-1 text-sm sm:grid-cols-2">
              {Object.entries(data.aggregate).map(([k, v]) => (
                <li key={k}>
                  <span className="text-slate-500">{k}:</span>{" "}
                  <span className="font-mono text-slate-900">{String(v)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className="rounded-md bg-slate-900 px-3 py-1.5 text-sm text-white"
              onClick={() => void loadFullReport()}
            >
              加载完整报告（当前页，带鉴权）
            </button>
          </div>
          {fullErr && <p className="text-xs text-rose-600">{fullErr}</p>}
          {fullMd && (
            <pre className="mt-2 max-h-[32rem] overflow-auto rounded-md border border-slate-200 bg-white p-3 text-xs whitespace-pre-wrap">
              {fullMd}
            </pre>
          )}
          <details className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
            <summary className="cursor-pointer font-medium text-slate-800">报告摘录</summary>
            <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap break-words text-xs text-slate-700">
              {data.excerpt}
            </pre>
          </details>
        </div>
      )}
    </main>
  );
}
