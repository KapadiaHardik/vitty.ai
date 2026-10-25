import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Vitty AI | Smart Document Assistant & Workflow Engine",
  description: "AI-assisted document intelligence and invoice verification for financial auditors.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.className} antialiased bg-[#f8fafc] text-slate-800 min-h-screen selection:bg-primary-500/20 flex flex-col`}
      >
        <div className="fixed inset-0 z-[-1] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-50/60 via-[#f8fafc] to-[#f1f5f9]"></div>
        <Navbar />
        <div className="flex-1 w-full">{children}</div>
      </body>
    </html>
  );
}
