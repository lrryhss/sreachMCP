import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider, SidebarTrigger, SidebarInset } from "@/components/ui/sidebar";
import { ThemeToggle } from "@/components/theme-toggle";
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
                  <SidebarProvider>
              <div className="flex h-screen w-full">
                <AppSidebar />
                <SidebarInset className="flex-1 overflow-hidden">
                  <header className="flex h-16 items-center justify-between border-b px-6 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                    <div className="flex items-center gap-2">
                      <SidebarTrigger />
                      <div className="h-4 w-px bg-border" />
                      <h2 className="text-lg font-semibold">Research Dashboard</h2>
                    </div>
                    <ThemeToggle />
                  </header>
                  <main className="flex-1 overflow-y-auto bg-muted/40">
                    <div className="container mx-auto p-6">
                      {children}
                    </div>
                  </main>
                </SidebarInset>
              </div>
                  </SidebarProvider>
                </Providers>
              </AuthMonitor>
            </ApiProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
