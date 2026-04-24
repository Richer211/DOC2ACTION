import type { Metadata } from "next";

import { SiteHeader } from "@/components/SiteHeader";

import "./globals.css";

export const metadata: Metadata = {
  title: "Doc2Action",
  description: "Document to action workspace"
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
