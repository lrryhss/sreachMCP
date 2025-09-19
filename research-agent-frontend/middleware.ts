import { withAuth } from "next-auth/middleware"
import { NextResponse } from "next/server"

export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token
    const pathname = req.nextUrl.pathname

    // If user is authenticated and tries to access root, redirect to dashboard
    if (token && pathname === '/') {
      return NextResponse.redirect(new URL('/dashboard', req.url))
    }

    // If user is not authenticated and tries to access root, redirect to landing
    if (!token && pathname === '/') {
      return NextResponse.redirect(new URL('/landing', req.url))
    }

    // Allow the request to proceed
    return NextResponse.next()
  },
  {
    callbacks: {
      authorized: ({ req, token }) => {
        const pathname = req.nextUrl.pathname

        // Public pages that don't require auth
        const publicPaths = [
          '/landing',
          '/auth/',
          '/api/',
          '/demo',
          '/privacy',
          '/terms',
          '/about'
        ]

        // Check if current path is public
        const isPublicPath = publicPaths.some(path => pathname.startsWith(path))

        // Allow public paths without token
        if (isPublicPath) {
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
      error: "/auth/error",
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