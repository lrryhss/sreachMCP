"use client"

import { useSession, signOut } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export function useAuthCheck() {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    // Check for session errors
    if (session?.error === "RefreshAccessTokenError") {
      // Token refresh failed, sign out and redirect to landing
      signOut({ redirect: false }).then(() => {
        // Clear all storage
        localStorage.clear()
        sessionStorage.clear()

        // Redirect to landing page
        router.push('/landing')
      })
    }
  }, [session, router])

  return { session, status }
}