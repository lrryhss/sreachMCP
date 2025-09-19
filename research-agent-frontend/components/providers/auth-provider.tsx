"use client"

import { SessionProvider } from "next-auth/react"
import { ReactNode, useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter, usePathname } from "next/navigation"

interface AuthProviderProps {
  children: ReactNode
}

function AuthGuard({ children }: { children: ReactNode }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    // Public paths that don't require authentication
    const publicPaths = ['/landing', '/auth/', '/demo', '/privacy', '/terms', '/about']
    const isPublicPath = publicPaths.some(path => pathname?.startsWith(path))

    if (status === "loading") return

    // If not authenticated and not on public path, redirect to signin
    if (!session && !isPublicPath && pathname !== '/') {
      router.push('/auth/signin?callbackUrl=' + encodeURIComponent(pathname || '/'))
    }

    // If authenticated and on root, redirect to dashboard
    if (session && pathname === '/') {
      router.push('/dashboard')
    }

    // If not authenticated and on root, redirect to landing
    if (!session && pathname === '/') {
      router.push('/landing')
    }
  }, [session, status, pathname, router])

  return <>{children}</>
}

export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <SessionProvider
      refetchInterval={5 * 60} // Refetch session every 5 minutes
      refetchOnWindowFocus={true} // Refetch session when window regains focus
    >
      <AuthGuard>
        {children}
      </AuthGuard>
    </SessionProvider>
  )
}