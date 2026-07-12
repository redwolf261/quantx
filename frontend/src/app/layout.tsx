import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FutureLens – AI Financial Decision Intelligence",
  description:
    "FutureLens creates your Financial Digital Twin and simulates possible financial futures using Monte Carlo simulation and AI-powered analytics. IDBI Innovate 2026.",
  keywords: ["financial planning", "wealth management", "Monte Carlo", "goal planning", "India"],
  openGraph: {
    title: "FutureLens – AI Financial Decision Intelligence",
    description: "Simulate your financial future with Monte Carlo analytics",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-navy-950 antialiased">{children}</body>
    </html>
  );
}
