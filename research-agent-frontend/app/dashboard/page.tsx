"use client"

import { useAuthCheck } from "@/hooks/use-auth-check"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { UserMenu } from "@/components/user-menu"
import {
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Plus,
  Search,
  Trash2,
  Eye
} from "lucide-react"
import { formatDistanceToNow } from "date-fns"

interface ResearchTask {
  id: string
  task_id: string
  query: string
  status: string
  depth: string
  max_sources: number
  progress: number
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
}

export default function DashboardPage() {
  const { session, status } = useAuthCheck()
  const router = useRouter()
  const [tasks, setTasks] = useState<ResearchTask[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/signin")
    }
  }, [status, router])

  useEffect(() => {
    if (session?.accessToken) {
      fetchResearchHistory()
    }
  }, [session])

  const fetchResearchHistory = async () => {
    try {
      setLoading(true)
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/research/history?limit=20`,
        {
          headers: {
            'Authorization': `Bearer ${session?.accessToken}`,
          },
        }
      )

      if (!res.ok) {
        throw new Error('Failed to fetch research history')
      }

      const data = await res.json()
      setTasks(data.tasks)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'pending':
      case 'analyzing':
      case 'searching':
      case 'fetching':
      case 'synthesizing':
      case 'generating':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />
      case 'cancelled':
        return <AlertCircle className="h-4 w-4 text-gray-500" />
      default:
        return null
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'failed':
        return 'destructive'
      case 'cancelled':
        return 'secondary'
      default:
        return 'default'
    }
  }

  const handleViewResult = (taskId: string) => {
    router.push(`/research/${taskId}`)
  }

  const handleDeleteTask = async (taskId: string) => {
    if (!confirm('Are you sure you want to delete this research?')) return

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/research/${taskId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${session?.accessToken}`,
          },
        }
      )

      if (res.ok) {
        setTasks(tasks.filter(t => t.task_id !== taskId))
      }
    } catch (err) {
      console.error('Failed to delete task:', err)
    }
  }

  if (status === "loading" || loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      </div>
    )
  }

  if (!session) {
    return null
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Research Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Welcome back, {session.user?.name || session.user?.email}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button onClick={() => router.push('/research/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Research
          </Button>
          <UserMenu />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Research</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tasks.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tasks.filter(t => t.status === 'completed').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tasks.filter(t => !['completed', 'failed', 'cancelled'].includes(t.status)).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tasks.filter(t => t.status === 'failed').length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Research History */}
      <Card>
        <CardHeader>
          <CardTitle>Research History</CardTitle>
          <CardDescription>
            Your recent research tasks and their status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="text-center py-8 text-red-500">
              Error: {error}
            </div>
          )}

          {!error && tasks.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No research tasks yet</p>
              <Button className="mt-4" variant="outline" onClick={() => router.push('/research/new')}>
                Start Your First Research
              </Button>
            </div>
          )}

          {!error && tasks.length > 0 && (
            <div className="space-y-4">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start space-x-4 flex-1">
                    <div className="mt-1">
                      {getStatusIcon(task.status)}
                    </div>
                    <div className="flex-1 space-y-1">
                      <p className="font-medium line-clamp-1">
                        {task.query}
                      </p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Badge variant={getStatusColor(task.status) as any}>
                          {task.status}
                        </Badge>
                        <span>•</span>
                        <span>{task.depth}</span>
                        <span>•</span>
                        <span>{task.max_sources} sources</span>
                        <span>•</span>
                        <span>
                          {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                        </span>
                      </div>
                      {task.error_message && (
                        <p className="text-sm text-red-500 mt-1">
                          Error: {task.error_message}
                        </p>
                      )}
                      {task.status !== 'completed' && task.status !== 'failed' && task.status !== 'cancelled' && (
                        <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
                          <div
                            className="bg-blue-600 h-1.5 rounded-full transition-all"
                            style={{ width: `${task.progress}%` }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {task.status === 'completed' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleViewResult(task.task_id)}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        View
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDeleteTask(task.task_id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}