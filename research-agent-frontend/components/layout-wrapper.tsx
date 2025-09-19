"use client"

import { useSession } from "next-auth/react"
import { usePathname } from "next/navigation"
import { ReactNode } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { SidebarProvider, SidebarTrigger, SidebarInset } from "@/components/ui/sidebar"
import { ThemeToggle } from "@/components/theme-toggle"
import { UserMenu } from "@/components/user-menu"

interface LayoutWrapperProps {
  children: ReactNode
}

export function LayoutWrapper({ children }: LayoutWrapperProps) {
  const { data: session, status } = useSession()
  const pathname = usePathname()

  // Public paths that should use minimal layout
  const publicPaths = ['/landing', '/auth/', '/demo', '/privacy', '/terms', '/about']
  const isPublicPath = publicPaths.some(path => pathname?.startsWith(path))

  // If loading or on public path, use minimal layout
  if (status === "loading" || isPublicPath || !session) {
    return (
      <div className="min-h-screen">
        {/* Minimal header for public pages */}
        <header className="border-b">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold">Research Agent</h1>
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle />
            </div>
          </div>
        </header>
        {/* Content without sidebar */}
        <main className="min-h-[calc(100vh-4rem)]">
          {children}
        </main>
      </div>
    )
  }

  // Authenticated users get full dashboard layout with sidebar
  return (
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
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <UserMenu />
            </div>
          </header>
          <main className="flex-1 overflow-y-auto bg-muted/40">
            <div className="container mx-auto p-6">
              {children}
            </div>
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}