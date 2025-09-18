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
          // Call backend API to authenticate
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/auth/login`, {
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
            const userRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/auth/me`, {
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
    async jwt({ token, user }: { token: JWT; user: any }) {
      if (user) {
        token.id = user.id
        token.email = user.email
        token.name = user.name
        token.accessToken = user.accessToken
        token.refreshToken = user.refreshToken
      }
      return token
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