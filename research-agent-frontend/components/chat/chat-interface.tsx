"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, FileText, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useApi } from "@/hooks/use-api";
import { cn } from "@/lib/utils";
import { MessageRenderer } from "./message-renderer";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: Source[];
  timestamp: Date;
  isStreaming?: boolean;
}

interface Source {
  id: string;
  task_id?: string;
  query?: string;
  type?: string;
  url?: string;
  title?: string;
  created_at?: string;
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
}

export function ChatInterface() {
  const api = useApi();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [showSources, setShowSources] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Create new session on mount
  useEffect(() => {
    createNewSession();
  }, []);

  const createNewSession = async () => {
    try {
      const response = await api.client.post("/api/chat/sessions", {
        title: `Chat ${new Date().toLocaleString()}`
      });
      setCurrentSession({
        id: response.data.id,
        title: response.data.title,
        messages: []
      });
      setMessages([]);
    } catch (error) {
      console.error("Failed to create session:", error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading || !currentSession) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await api.client.post("/api/chat/messages", {
        session_id: currentSession.id,
        content: userMessage.content,
        stream: false
      });

      const assistantMessage: Message = {
        id: response.data.id,
        role: "assistant",
        content: response.data.content,
        sources: response.data.sources,
        timestamp: new Date(response.data.created_at)
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Failed to send message:", error);

      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "system",
        content: "Sorry, I encountered an error processing your message. Please try again.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const toggleSources = (messageId: string) => {
    setShowSources(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const messageDate = new Date(date);
    const diffInSeconds = Math.floor((now.getTime() - messageDate.getTime()) / 1000);

    if (diffInSeconds < 60) {
      return 'just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    } else {
      return messageDate.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  };

  const renderMessage = (message: Message) => {
    const isUser = message.role === "user";
    const isSystem = message.role === "system";

    return (
      <div
        key={message.id}
        className={cn(
          "flex gap-3 p-4 transition-all duration-200 hover:bg-gray-50/50 dark:hover:bg-gray-800/50 message-entry",
          isUser && "bg-muted/50",
          isSystem && "bg-yellow-50 dark:bg-yellow-900/20"
        )}
      >
        <div className="flex-shrink-0">
          {isUser ? (
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <User className="w-4 h-4 text-primary-foreground" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
          )}
        </div>

        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm">
              {isUser ? "You" : isSystem ? "System" : "Assistant"}
            </span>
            <span className="text-xs text-muted-foreground transition-opacity hover:opacity-100 opacity-70" title={message.timestamp.toLocaleString()}>
              {formatTimestamp(message.timestamp)}
            </span>
          </div>

          <MessageRenderer
            content={message.content}
            className="max-w-none"
          />

          {message.sources && message.sources.length > 0 && (
            <div className="pt-2">
              <Collapsible>
                <CollapsibleTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 px-2"
                    onClick={() => toggleSources(message.id)}
                  >
                    <FileText className="w-4 h-4 mr-1" />
                    {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-2">
                  <div className="space-y-2">
                    {message.sources.map((source, idx) => (
                      <Card key={idx} className="p-3">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="font-medium text-sm">
                              {source.query || source.title || `Source ${idx + 1}`}
                            </div>
                            {source.type && (
                              <Badge variant="secondary" className="mt-1">
                                {source.type}
                              </Badge>
                            )}
                            {source.created_at && (
                              <div className="text-xs text-muted-foreground mt-1">
                                {new Date(source.created_at).toLocaleDateString()}
                              </div>
                            )}
                          </div>
                          {source.task_id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                              onClick={() => window.open(`/research/${source.task_id}`, '_blank')}
                            >
                              <ExternalLink className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </Card>
                    ))}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </div>
          )}

          {message.isStreaming && (
            <div className="flex items-center gap-2 text-muted-foreground mt-2">
              <div className="typing-indicator scale-75">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="text-xs animate-pulse">Processing...</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Research Chat</h2>
            <p className="text-sm text-muted-foreground">
              Ask questions about your research database
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={createNewSession}>
            New Chat
          </Button>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1">
        <div className="pb-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-96 text-center">
              <Bot className="w-12 h-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Start a Conversation</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Ask questions about your research data. I can help you find insights,
                connect information across different research tasks, and explore your
                knowledge base.
              </p>
              <div className="mt-6 space-y-2">
                <p className="text-xs text-muted-foreground">Try asking:</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  <Badge variant="secondary" className="cursor-pointer hover:bg-secondary/80"
                    onClick={() => setInput("What are the main findings from my recent research?")}>
                    Recent findings
                  </Badge>
                  <Badge variant="secondary" className="cursor-pointer hover:bg-secondary/80"
                    onClick={() => setInput("Summarize research about AI and machine learning")}>
                    AI & ML summary
                  </Badge>
                  <Badge variant="secondary" className="cursor-pointer hover:bg-secondary/80"
                    onClick={() => setInput("What connections exist between my research topics?")}>
                    Topic connections
                  </Badge>
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map(renderMessage)}
              {isLoading && (
                <div className="flex gap-3 p-4 bg-muted/30 message-entry">
                  <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center animate-pulse">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="typing-indicator text-muted-foreground">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span className="text-sm text-muted-foreground animate-pulse">Assistant is thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage();
          }}
          className="flex gap-2"
        >
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your research..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}