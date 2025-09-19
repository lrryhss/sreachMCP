"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import { Settings, User, Bell, Shield, Database, Download } from "lucide-react"

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and research preferences
        </p>
      </div>

      {/* Profile Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Profile
          </CardTitle>
          <CardDescription>
            Update your personal information and preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="full-name">Full Name</Label>
              <Input
                id="full-name"
                placeholder="Enter your full name"
                defaultValue="Administrator"
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                defaultValue="admin@example.com"
                disabled
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="bio">Bio</Label>
            <Textarea
              id="bio"
              placeholder="Tell us about yourself"
              disabled
            />
          </div>
          <Button disabled>Save Profile</Button>
        </CardContent>
      </Card>

      {/* Research Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Research Preferences
          </CardTitle>
          <CardDescription>
            Configure how research tasks are executed
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>Default Research Depth</Label>
              <p className="text-sm text-muted-foreground">
                Choose the default depth for new research tasks
              </p>
            </div>
            <Select disabled>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Standard" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="quick">Quick</SelectItem>
                <SelectItem value="standard">Standard</SelectItem>
                <SelectItem value="comprehensive">Comprehensive</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>Maximum Sources</Label>
              <p className="text-sm text-muted-foreground">
                Default number of sources to analyze
              </p>
            </div>
            <Input
              type="number"
              placeholder="20"
              className="w-[180px]"
              disabled
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>Auto-save Results</Label>
              <p className="text-sm text-muted-foreground">
                Automatically save completed research to history
              </p>
            </div>
            <Switch disabled defaultChecked />
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notifications
          </CardTitle>
          <CardDescription>
            Configure how you receive updates about your research
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>Research Completion</Label>
              <p className="text-sm text-muted-foreground">
                Notify when research tasks are completed
              </p>
            </div>
            <Switch disabled defaultChecked />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>Research Failures</Label>
              <p className="text-sm text-muted-foreground">
                Notify when research tasks fail
              </p>
            </div>
            <Switch disabled defaultChecked />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>Weekly Summary</Label>
              <p className="text-sm text-muted-foreground">
                Receive weekly research activity summaries
              </p>
            </div>
            <Switch disabled />
          </div>
        </CardContent>
      </Card>

      {/* Data & Privacy */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Data & Privacy
          </CardTitle>
          <CardDescription>
            Manage your data and privacy settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>Data Retention</Label>
              <p className="text-sm text-muted-foreground">
                How long to keep your research data
              </p>
            </div>
            <Select disabled>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="1 year" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="30days">30 days</SelectItem>
                <SelectItem value="3months">3 months</SelectItem>
                <SelectItem value="1year">1 year</SelectItem>
                <SelectItem value="forever">Forever</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Separator />

          <div className="space-y-2">
            <Label>Export Data</Label>
            <p className="text-sm text-muted-foreground">
              Download all your research data and settings
            </p>
            <Button variant="outline" size="sm" disabled>
              <Download className="mr-2 h-4 w-4" />
              Export All Data
            </Button>
          </div>

          <Separator />

          <div className="space-y-2">
            <Label className="text-destructive">Delete Account</Label>
            <p className="text-sm text-muted-foreground">
              Permanently delete your account and all associated data
            </p>
            <Button variant="destructive" size="sm" disabled>
              Delete Account
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}