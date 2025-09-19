import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { LayoutWrapper } from "@/components/layout-wrapper";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { AuthProvider } from "@/components/providers/auth-provider";
import { ApiProvider } from "@/components/providers/api-provider";
import { AuthMonitor } from "@/components/providers/auth-monitor";

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
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <ApiProvider>
              <AuthMonitor>
                <Providers>
                  <LayoutWrapper>
                    {children}
                  </LayoutWrapper>
                </Providers>
              </AuthMonitor>
            </ApiProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
