"use client"

import { useParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CalendarDays, Download, ExternalLink, FileText, Share } from "lucide-react"
import Link from "next/link"

export default function ReportPage() {
  const params = useParams()
  const reportId = params.id as string

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Research Report</h1>
          <p className="text-muted-foreground">
            Detailed analysis and findings for report #{reportId}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Share className="mr-2 h-4 w-4" />
            Share
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Report Status */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-[200px] text-muted-foreground">
            <div className="text-center">
              <FileText className="mx-auto h-12 w-12 mb-4" />
              <h3 className="text-lg font-medium mb-2">Report Not Found</h3>
              <p className="mb-4">The research report you're looking for doesn't exist or hasn't been completed yet.</p>
              <Link href="/dashboard">
                <Button variant="outline">
                  Return to Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Placeholder for actual report content when available */}
      {/* This will be replaced with real report data once research is implemented */}
      <div className="hidden">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Sample Research Title</CardTitle>
                <CardDescription className="flex items-center gap-2 mt-2">
                  <CalendarDays className="h-4 w-4" />
                  Completed 2 hours ago
                  <Badge variant="secondary">24 sources</Badge>
                </CardDescription>
              </div>
              <Badge variant="default">Completed</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Executive Summary */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Executive Summary</h3>
                <p className="text-muted-foreground">
                  Report summary would appear here...
                </p>
              </div>

              {/* Key Findings */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Key Findings</h3>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Finding 1...</li>
                  <li>• Finding 2...</li>
                  <li>• Finding 3...</li>
                </ul>
              </div>

              {/* Sources */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Sources</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 p-2 border rounded">
                    <ExternalLink className="h-4 w-4" />
                    <span className="text-sm">Sample source would appear here...</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}