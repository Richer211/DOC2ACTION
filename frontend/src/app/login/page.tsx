"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import {
  API_BASE_URL,
  JWT_STORAGE_KEY,
  JWT_USER_STORAGE_KEY,
  readErrorMessage
} from "@/lib/doc2action-api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ username, password })
      });
      if (!response.ok) {
        setError(await readErrorMessage(response));
        return;
      }
      const data: { access_token: string } = await response.json();
      sessionStorage.setItem(JWT_STORAGE_KEY, data.access_token);
      sessionStorage.setItem(JWT_USER_STORAGE_KEY, username);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-md px-6 py-16">
      <Link href="/" className="text-sm text-indigo-600 hover:text-indigo-800">
        ← 返回工作台
      </Link>
      <div className="mt-8 rounded-2xl border border-slate-200/80 bg-white p-8 shadow-lg shadow-slate-200/50">
        <h1 className="text-2xl font-bold text-slate-900">登录</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          后端需配置 <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">DOC2ACTION_JWT_SECRET</code>
          。登录后请求携带 <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">Authorization: Bearer</code>
          ，分析记录会关联 <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">user_sub</code>。
        </p>
        <div className="mt-6 space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">用户名</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm shadow-sm transition focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">密码</label>
            <input
              type="password"
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm shadow-sm transition focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  void submit();
                }
              }}
            />
          </div>
          {error && (
            <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>
          )}
          <button
            type="button"
            disabled={loading || !username.trim()}
            onClick={() => void submit()}
            className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {loading ? "登录中…" : "登录"}
          </button>
        </div>
      </div>
    </main>
  );
}
