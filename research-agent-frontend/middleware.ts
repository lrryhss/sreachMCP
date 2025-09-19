import { withAuth } from "next-auth/middleware"
import { NextResponse } from "next/server"

export default withAuth(
  function middleware(req) {
    // Allow the request to proceed
    return NextResponse.next()
  },
  {
    callbacks: {
      authorized: ({ req, token }) => {
        // Allow auth pages to be accessed without token
        if (req.nextUrl.pathname.startsWith("/auth/")) {
          return true
        }

        // Allow API routes (they have their own auth)
        if (req.nextUrl.pathname.startsWith("/api/")) {
          return true
        }

        // Check for demo mode (for testing)
        if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") {
          return true
        }

        // Require token for all other routes
        return !!token
      },
    },
    pages: {
      signIn: "/auth/signin",
    },
  }
)

// Protect all routes except auth and api
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - auth (auth pages)
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!auth|api|_next/static|_next/image|favicon.ico|public).*)',
  ],
}