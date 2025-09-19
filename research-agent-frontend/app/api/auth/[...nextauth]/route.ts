import NextAuth from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import { NextAuthOptions } from "next-auth"
import { JWT } from "next-auth/jwt"

const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username_or_email: { label: "Email or Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.username_or_email || !credentials?.password) {
          return null
        }

        try {
          // Call backend API to authenticate (use internal service name for server-side calls)
          const apiUrl = process.env.INTERNAL_API_URL || 'http://research-agent:8000'
          const res = await fetch(`${apiUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              username_or_email: credentials.username_or_email,
              password: credentials.password,
            }),
          })

          const data = await res.json()

          if (res.ok && data.access_token) {
            // Get user info
            const userRes = await fetch(`${apiUrl}/api/auth/me`, {
              headers: {
                'Authorization': `Bearer ${data.access_token}`,
              },
            })

            const userData = await userRes.json()

            return {
              id: userData.id,
              email: userData.email,
              name: userData.username,
              accessToken: data.access_token,
              refreshToken: data.refresh_token,
            }
          }

          return null
        } catch (error) {
          console.error('Auth error:', error)
          return null
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, account, trigger, session }: { token: JWT; user: any; account: any; trigger?: string; session?: any }) {
      // Initial sign in
      if (user) {
        token.id = user.id
        token.email = user.email
        token.name = user.name
        token.accessToken = user.accessToken
        token.refreshToken = user.refreshToken
        // Store token expiry time (120 minutes from now)
        token.accessTokenExpires = Date.now() + 120 * 60 * 1000
      }

      // Handle manual session update (from token refresh)
      if (trigger === 'update' && session) {
        token.accessToken = session.accessToken
        token.refreshToken = session.refreshToken
        token.accessTokenExpires = Date.now() + 120 * 60 * 1000
      }

      // Return previous token if the access token has not expired yet
      if (Date.now() < (token.accessTokenExpires as number || 0)) {
        return token
      }

      // Access token has expired, try to refresh it
      try {
        const apiUrl = process.env.INTERNAL_API_URL || 'http://research-agent:8000'
        const response = await fetch(`${apiUrl}/api/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            refresh_token: token.refreshToken,
          }),
        })

        const data = await response.json()

        if (response.ok && data.access_token) {
          // Update token with new access token
          token.accessToken = data.access_token
          token.refreshToken = data.refresh_token
          token.accessTokenExpires = Date.now() + 120 * 60 * 1000
          return token
        }

        // Refresh failed
        throw new Error('Token refresh failed')
      } catch (error) {
        console.error('Error refreshing token:', error)
        // Return the old token and let the client handle the error
        token.error = 'RefreshAccessTokenError'
        return token
      }
    },
    async session({ session, token }: { session: any; token: JWT }) {
      if (token) {
        session.user = {
          id: token.id,
          email: token.email,
          name: token.name,
        }
        session.accessToken = token.accessToken
        session.refreshToken = token.refreshToken
        session.error = token.error
      }
      return session
    },
  },
  pages: {
    signIn: '/auth/signin',
    signOut: '/auth/signout',
    error: '/auth/error',
  },
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET || 'your-secret-key-change-in-production',
}

const handler = NextAuth(authOptions)
export { handler as GET, handler as POST }