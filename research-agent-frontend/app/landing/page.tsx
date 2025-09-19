import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Search, Brain, FileText, MessageSquare, TrendingUp } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center space-y-6 max-w-3xl mx-auto">
          <div className="flex justify-center">
            <div className="p-4 rounded-full bg-primary/10">
              <Sparkles className="h-12 w-12 text-primary" />
            </div>
          </div>

          <h1 className="text-5xl font-bold tracking-tight">
            AI-Powered Research Agent
          </h1>

          <p className="text-xl text-muted-foreground">
            Get comprehensive research reports on any topic in minutes.
            Powered by advanced AI and GraphRAG technology.
          </p>

          <div className="flex gap-4 justify-center pt-4">
            <Button size="lg" asChild>
              <Link href="/auth/signin">Get Started</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/demo">Try Demo</Link>
            </Button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">
          Powerful Research Features
        </h2>

        <div className="grid md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <Search className="h-8 w-8 text-primary mb-2" />
              <CardTitle>Smart Search</CardTitle>
              <CardDescription>
                Searches across multiple sources simultaneously to find the most relevant information
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm space-y-2">
                <li>• Academic papers</li>
                <li>• News articles</li>
                <li>• Web content</li>
                <li>• Research databases</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Brain className="h-8 w-8 text-primary mb-2" />
              <CardTitle>AI Analysis</CardTitle>
              <CardDescription>
                Advanced AI synthesizes information into comprehensive, structured reports
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm space-y-2">
                <li>• Key findings extraction</li>
                <li>• Detailed analysis</li>
                <li>• Source verification</li>
                <li>• Fact checking</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <MessageSquare className="h-8 w-8 text-primary mb-2" />
              <CardTitle>GraphRAG Chat</CardTitle>
              <CardDescription>
                Chat with your research database using state-of-the-art GraphRAG technology
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm space-y-2">
                <li>• Natural language queries</li>
                <li>• Knowledge graph traversal</li>
                <li>• Context-aware responses</li>
                <li>• Source citations</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* How It Works */}
      <div className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">
          How It Works
        </h2>

        <div className="max-w-3xl mx-auto space-y-8">
          <div className="flex gap-4 items-start">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
              1
            </div>
            <div>
              <h3 className="font-semibold text-lg">Enter Your Query</h3>
              <p className="text-muted-foreground">
                Describe what you want to research in detail. Be specific for better results.
              </p>
            </div>
          </div>

          <div className="flex gap-4 items-start">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
              2
            </div>
            <div>
              <h3 className="font-semibold text-lg">AI Searches & Analyzes</h3>
              <p className="text-muted-foreground">
                Our AI searches multiple sources, extracts relevant information, and performs deep analysis.
              </p>
            </div>
          </div>

          <div className="flex gap-4 items-start">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
              3
            </div>
            <div>
              <h3 className="font-semibold text-lg">Get Comprehensive Report</h3>
              <p className="text-muted-foreground">
                Receive a detailed report with synthesis, key findings, sources, and actionable insights.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="container mx-auto px-4 py-16">
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="py-12">
            <div className="text-center space-y-4">
              <h2 className="text-3xl font-bold">Ready to Start Researching?</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Join thousands of researchers, students, and professionals who use our AI-powered research agent
                to save time and discover insights.
              </p>
              <div className="flex gap-4 justify-center pt-4">
                <Button size="lg" asChild>
                  <Link href="/auth/signup">Create Free Account</Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link href="/auth/signin">Sign In</Link>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-muted-foreground">
              © 2025 Research Agent. Powered by GraphRAG technology.
            </p>
            <div className="flex gap-4">
              <Link href="/privacy" className="text-sm text-muted-foreground hover:text-foreground">
                Privacy
              </Link>
              <Link href="/terms" className="text-sm text-muted-foreground hover:text-foreground">
                Terms
              </Link>
              <Link href="/about" className="text-sm text-muted-foreground hover:text-foreground">
                About
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}