"use client"

import * as React from "react"
import {
  Search,
  FileText,
  History,
  Settings,
  HelpCircle,
  ChevronDown,
  Plus,
  Clock,
  TrendingUp,
  BarChart3,
  Sparkles,
  Home,
  MessageSquare
} from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarSeparator,
} from "@/components/ui/sidebar"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

// Mock data for recent research reports
const recentReports = [
  {
    id: "1",
    title: "AI Safety Research",
    date: "2 hours ago",
    status: "completed",
    sources: 24,
  },
  {
    id: "2",
    title: "Market Analysis Q4 2024",
    date: "Yesterday",
    status: "completed",
    sources: 18,
  },
  {
    id: "3",
    title: "Climate Tech Innovations",
    date: "3 days ago",
    status: "completed",
    sources: 31,
  },
]

const navigation = [
  {
    name: "Dashboard",
    href: "/",
    icon: Home,
  },
  {
    name: "New Research",
    href: "/research/new",
    icon: Plus,
  },
  {
    name: "Research Chat",
    href: "/chat",
    icon: MessageSquare,
    badge: "New",
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
  {
    name: "Trending Topics",
    href: "/trending",
    icon: TrendingUp,
  },
]

export function AppSidebar() {
  const pathname = usePathname()
  const [isHistoryOpen, setIsHistoryOpen] = React.useState(true)

  return (
    <Sidebar className="border-r">
      <SidebarHeader className="border-b px-6 py-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Sparkles className="h-4 w-4 text-primary-foreground" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold">Research Agent</span>
            <span className="text-xs text-muted-foreground">AI-Powered Insights</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigation.map((item) => (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname === item.href}
                    className="transition-colors"
                  >
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.name}</span>
                      {item.badge && (
                        <Badge variant="secondary" className="ml-auto">
                          {item.badge}
                        </Badge>
                      )}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <Collapsible open={isHistoryOpen} onOpenChange={setIsHistoryOpen}>
            <CollapsibleTrigger asChild>
              <SidebarGroupLabel className="flex w-full items-center justify-between cursor-pointer hover:bg-accent/50 rounded-md px-2 py-1 transition-colors">
                <span className="flex items-center gap-2">
                  <History className="h-3 w-3" />
                  Recent Research
                </span>
                <ChevronDown className={cn(
                  "h-3 w-3 transition-transform",
                  isHistoryOpen && "rotate-180"
                )} />
              </SidebarGroupLabel>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <SidebarGroupContent>
                <SidebarMenu>
                  {recentReports.map((report) => (
                    <SidebarMenuItem key={report.id}>
                      <SidebarMenuButton asChild className="h-auto py-3">
                        <Link href={`/report/${report.id}`}>
                          <div className="flex flex-col gap-1 flex-1">
                            <div className="flex items-start justify-between">
                              <span className="text-sm font-medium line-clamp-1">
                                {report.title}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              <span>{report.date}</span>
                              <span>•</span>
                              <span>{report.sources} sources</span>
                            </div>
                          </div>
                          {report.status === "completed" && (
                            <Badge variant="secondary" className="ml-2 h-5 px-1.5 text-xs">
                              <FileText className="h-3 w-3" />
                            </Badge>
                          )}
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <Link href="/history" className="text-muted-foreground hover:text-foreground">
                        <span className="text-sm">View all reports →</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </CollapsibleContent>
          </Collapsible>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupLabel>Quick Actions</SidebarGroupLabel>
          <SidebarGroupContent>
            <div className="space-y-2 px-2">
              <Button variant="outline" className="w-full justify-start gap-2" size="sm">
                <Search className="h-4 w-4" />
                Quick Search
              </Button>
              <Button variant="outline" className="w-full justify-start gap-2" size="sm">
                <FileText className="h-4 w-4" />
                Import Data
              </Button>
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t p-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <Link href="/settings">
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <Link href="/help">
                <HelpCircle className="h-4 w-4" />
                <span>Help & Support</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}