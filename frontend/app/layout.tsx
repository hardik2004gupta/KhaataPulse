import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
  weight: ["300", "400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-jetbrains-mono",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: {
    default: "KhaataPulse - Revenue Intelligence Engine",
    template: "%s · KhaataPulse",
  },
  description:
    "KhaataPulse detects payment friction before failure, diagnoses the root cause, ranks the economically optimal intervention, and enforces deterministic policy control over every recovery action.",
  applicationName: "KhaataPulse",
  keywords: [
    "revenue recovery",
    "payment risk",
    "policy engine",
    "subscription renewals",
    "dunning",
  ],
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: "#07090D",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-bg-primary text-text-primary antialiased">{children}</body>
    </html>
  );
}
