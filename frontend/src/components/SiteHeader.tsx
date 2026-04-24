"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { JWT_STORAGE_KEY, JWT_USER_STORAGE_KEY } from "@/lib/doc2action-api";

const navLink =
  "text-sm font-medium transition-colors text-slate-600 hover:text-slate-900";
const navActive = "text-indigo-600 hover:text-indigo-700";

export function SiteHeader() {
  const pathname = usePathname();
  const [userLabel, setUserLabel] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    setUserLabel(sessionStorage.getItem(JWT_USER_STORAGE_KEY));
  }, [pathname]);

  const logout = () => {
    sessionStorage.removeItem(JWT_STORAGE_KEY);
    sessionStorage.removeItem(JWT_USER_STORAGE_KEY);
    setUserLabel(null);
  };

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/90 bg-white/85 shadow-sm backdrop-blur-md supports-[backdrop-filter]:bg-white/70">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-6 py-3">
        <div className="flex min-w-0 flex-1 items-center gap-8">
          <Link
            href="/"
            className="shrink-0 text-base font-semibold tracking-tight text-slate-900"
          >
            Doc2Action
          </Link>
          <nav className="flex flex-wrap items-center gap-x-5 gap-y-1">
            <Link href="/" className={pathname === "/" ? `${navLink} ${navActive}` : navLink}>
              工作台
            </Link>
            <Link
              href="/kb"
              className={pathname === "/kb" || pathname.startsWith("/kb/") ? `${navLink} ${navActive}` : navLink}
            >
              知识库
            </Link>
            <Link
              href="/eval-summary"
              className={pathname === "/eval-summary" ? `${navLink} ${navActive}` : navLink}
            >
              评测摘要
            </Link>
          </nav>
        </div>
        <div className="flex shrink-0 items-center gap-3 text-sm">
          {userLabel ? (
            <>
              <span className="max-w-[12rem] truncate text-slate-600" title={userLabel}>
                已登录：<span className="font-medium text-slate-900">{userLabel}</span>
              </span>
              <button
                type="button"
                onClick={logout}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-slate-700 shadow-sm transition hover:bg-slate-50"
              >
                退出
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="rounded-lg bg-indigo-600 px-3 py-1.5 font-medium text-white shadow-sm transition hover:bg-indigo-700"
            >
              去登录
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
