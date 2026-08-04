import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-plus-jakarta",
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "Aurora RAG — RMIT Vietnam AI Assistant & Analytics",
  description: "Futuristic Glassmorphic AI Assistant & RAG Analytics Dashboard for RMIT Vietnam",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${plusJakartaSans.variable} font-sans h-full antialiased dark`}>
      <body className="min-h-full bg-[#050811] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
