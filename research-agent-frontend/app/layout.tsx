import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Research Agent",
  description: "AI-powered research assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b">
              <div className="container mx-auto px-4 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <h1 className="text-2xl font-bold">Research Agent</h1>
                    <nav className="hidden md:flex gap-4">
                      <a href="/" className="text-sm hover:underline">
                        New Research
                      </a>
                      <a href="/history" className="text-sm hover:underline">
                        History
                      </a>
                    </nav>
                  </div>
                </div>
              </div>
            </header>

            {/* Main content */}
            <main className="container mx-auto px-4 py-8">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
