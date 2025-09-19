"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { TrendingUp, Search, ExternalLink, Hash, ArrowUp } from "lucide-react"

export default function TrendingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trending Topics</h1>
        <p className="text-muted-foreground">
          Discover what topics are being researched most frequently
        </p>
      </div>

      {/* Trending Categories */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Technology</CardTitle>
            <CardDescription>Latest tech trends and innovations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-[100px] text-muted-foreground">
              <div className="text-center">
                <TrendingUp className="mx-auto h-8 w-8 mb-2" />
                <p className="text-sm">No trending topics</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Science</CardTitle>
            <CardDescription>Scientific breakthroughs and research</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-[100px] text-muted-foreground">
              <div className="text-center">
                <TrendingUp className="mx-auto h-8 w-8 mb-2" />
                <p className="text-sm">No trending topics</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Business</CardTitle>
            <CardDescription>Market trends and business insights</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-[100px] text-muted-foreground">
              <div className="text-center">
                <TrendingUp className="mx-auto h-8 w-8 mb-2" />
                <p className="text-sm">No trending topics</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trending Now */}
      <Card>
        <CardHeader>
          <CardTitle>Trending Now</CardTitle>
          <CardDescription>
            Most researched topics in the last 24 hours
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex h-[300px] items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Hash className="mx-auto h-12 w-12 mb-4" />
              <h3 className="text-lg font-medium mb-2">No Trending Data</h3>
              <p className="mb-4">Trending topics will appear here as more research is conducted</p>
              <Button variant="outline">
                <Search className="mr-2 h-4 w-4" />
                Start Research
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Placeholder for trending topics list */}
      <div className="hidden">
        <div className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1 text-green-600">
                    <ArrowUp className="h-4 w-4" />
                    <span className="text-sm font-medium">+15%</span>
                  </div>
                  <div>
                    <h4 className="font-medium">Artificial Intelligence</h4>
                    <p className="text-sm text-muted-foreground">AI developments and applications</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">127 searches</Badge>
                  <Button variant="ghost" size="sm">
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}