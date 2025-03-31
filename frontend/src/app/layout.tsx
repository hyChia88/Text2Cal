import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Memory Log - Store and Visualize Your Memory Patterns",
  description: "An experimental tool to log your memories, visualize your past, and gain personalized insights through AI attention mechanisms.",
  keywords: "memory log, personal journal, diary, memory attention, AI insights, visualization, memory patterns",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400;1,500&display=swap" rel="stylesheet" />
      </head>
      <body 
        className="geist_e531dabc-module__QGiZLq__variable geist_mono_68a01160-module__YLcDdW__varia..."
        suppressHydrationWarning={true}
      >
        {children}
      </body>
    </html>
  )
}