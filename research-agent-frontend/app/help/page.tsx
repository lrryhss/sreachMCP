"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { HelpCircle, Search, MessageCircle, FileText, Settings, Zap, Users, Mail } from "lucide-react"

export default function HelpPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Help & Support</h1>
        <p className="text-muted-foreground">
          Find answers to common questions and get support for using Research Agent
        </p>
      </div>

      {/* Quick Help Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2">
            <Search className="h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search help articles..."
              className="flex-1"
              disabled
            />
            <Button disabled>Search</Button>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Zap className="h-5 w-5 text-primary" />
              Getting Started
            </CardTitle>
            <CardDescription>
              Learn the basics of conducting research
            </CardDescription>
          </CardHeader>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Settings className="h-5 w-5 text-primary" />
              Troubleshooting
            </CardTitle>
            <CardDescription>
              Resolve common issues and errors
            </CardDescription>
          </CardHeader>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <MessageCircle className="h-5 w-5 text-primary" />
              Contact Support
            </CardTitle>
            <CardDescription>
              Get help from our support team
            </CardDescription>
          </CardHeader>
        </Card>
      </div>

      {/* FAQ Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5" />
            Frequently Asked Questions
          </CardTitle>
          <CardDescription>
            Common questions about Research Agent
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="item-1">
              <AccordionTrigger>How do I start a new research task?</AccordionTrigger>
              <AccordionContent>
                Click on "New Research" in the dashboard or sidebar, enter your research query,
                select your preferred depth and source count, then click "Start Research" to begin.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-2">
              <AccordionTrigger>What are the different research depths?</AccordionTrigger>
              <AccordionContent>
                <ul className="space-y-2">
                  <li><Badge variant="outline">Quick</Badge> - Fast overview with 5-10 sources</li>
                  <li><Badge variant="outline">Standard</Badge> - Balanced research with 15-20 sources</li>
                  <li><Badge variant="outline">Comprehensive</Badge> - In-depth analysis with 25+ sources</li>
                </ul>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-3">
              <AccordionTrigger>How long does a research task take?</AccordionTrigger>
              <AccordionContent>
                Research time varies based on depth and complexity:
                <ul className="mt-2 space-y-1">
                  <li>• Quick: 2-5 minutes</li>
                  <li>• Standard: 5-15 minutes</li>
                  <li>• Comprehensive: 15-30 minutes</li>
                </ul>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-4">
              <AccordionTrigger>Can I export my research results?</AccordionTrigger>
              <AccordionContent>
                Yes! Research results can be exported in multiple formats including HTML,
                Markdown, and JSON. Use the export button in the research report view.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-5">
              <AccordionTrigger>How do I share research with others?</AccordionTrigger>
              <AccordionContent>
                Research reports can be shared via secure links. Click the "Share" button
                in any research report to generate a shareable link with configurable permissions.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-6">
              <AccordionTrigger>Is my research data secure?</AccordionTrigger>
              <AccordionContent>
                Yes, all research data is encrypted in transit and at rest. Your research
                queries and results are private and only accessible to you unless explicitly shared.
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>

      {/* Documentation Links */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Documentation
          </CardTitle>
          <CardDescription>
            Detailed guides and documentation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-3">
              <h4 className="font-medium">User Guides</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <button className="text-primary hover:underline" disabled>
                    Getting Started Guide
                  </button>
                </li>
                <li>
                  <button className="text-primary hover:underline" disabled>
                    Advanced Research Tips
                  </button>
                </li>
                <li>
                  <button className="text-primary hover:underline" disabled>
                    Collaboration Features
                  </button>
                </li>
                <li>
                  <button className="text-primary hover:underline" disabled>
                    Data Export Guide
                  </button>
                </li>
              </ul>
            </div>
            <div className="space-y-3">
              <h4 className="font-medium">Technical Docs</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <button className="text-primary hover:underline" disabled>
                    API Reference
                  </button>
                </li>
                <li>
                  <button className="text-primary hover:underline" disabled>
                    Integration Guide
                  </button>
                </li>
                <li>
                  <button className="text-primary hover:underline" disabled>
                    Security Overview
                  </button>
                </li>
                <li>
                  <button className="text-primary hover:underline" disabled>
                    Rate Limits & Usage
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contact Support */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Need More Help?
          </CardTitle>
          <CardDescription>
            Get in touch with our support team
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <Button variant="outline" className="h-auto p-4" disabled>
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5" />
                <div className="text-left">
                  <div className="font-medium">Email Support</div>
                  <div className="text-sm text-muted-foreground">
                    Get help via email within 24 hours
                  </div>
                </div>
              </div>
            </Button>
            <Button variant="outline" className="h-auto p-4" disabled>
              <div className="flex items-center gap-3">
                <MessageCircle className="h-5 w-5" />
                <div className="text-left">
                  <div className="font-medium">Live Chat</div>
                  <div className="text-sm text-muted-foreground">
                    Chat with support during business hours
                  </div>
                </div>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}