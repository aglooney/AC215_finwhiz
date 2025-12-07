import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message, Source } from '../types';
import { api } from '../services/api';

interface ChatInterfaceProps {
  sessionId: string;
}

export default function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `# Welcome to FinWhiz!

I'm your **AI-powered financial education assistant**. I'm here to help you navigate the complex world of personal finance.

## What I can help you with:

- **Investment Strategies** - Learn about stocks, bonds, ETFs, and portfolio diversification
- **Tax Planning** - Understand tax-advantaged accounts like 401(k)s and IRAs
- **Retirement Planning** - Calculate savings goals and plan for your future
- *Document Analysis* - Upload your financial documents for personalized insights

## Getting Started:

1. Ask me any financial question
2. Upload documents (tax forms, statements, etc.)
3. Get personalized, easy-to-understand answers

**Try asking**: "What's the difference between a Roth IRA and Traditional IRA?" or "How should I diversify my portfolio?"

Let me know how I can help you today!`,
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [sourcesExpanded, setSourcesExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load message history from backend when component mounts
  useEffect(() => {
    const loadMessageHistory = async () => {
      try {
        console.log('Loading message history for session:', sessionId);
        const context = await api.getSessionContext(sessionId);
        console.log('Session context:', context);

        if (context.recent_messages && context.recent_messages.length > 0) {
          const historicalMessages = context.recent_messages.map((msg: any) => ({
            role: msg.role as 'user' | 'assistant',
            content: msg.content,
          }));

          // Preserve welcome message, add historical messages after it
          setMessages((prev) => [prev[0], ...historicalMessages]);
          console.log('Loaded', historicalMessages.length, 'historical messages');
        }
      } catch (error) {
        console.error('Failed to load message history:', error);
      }
    };

    loadMessageHistory();
  }, [sessionId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setSources([]); // Clear previous sources
    setSourcesExpanded(false);

    try {
      console.log('Sending message to session:', sessionId);
      console.log('Message content:', input);

      // Log message to agent
      await api.addMessage(sessionId, 'user', input);
      console.log('Message logged to agent');

      // Query LLM
      console.log('Querying LLM with session:', sessionId);
      const response = await api.query(input, sessionId);
      console.log('LLM Response:', response);

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setSources(response.sources);

      // Log assistant response
      await api.addMessage(sessionId, 'assistant', response.answer);
      console.log('Assistant response logged');
    } catch (error: any) {
      console.error('Error querying LLM:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });

      let errorMsg = 'Sorry, I encountered an error processing your request. Please try again.';
      if (error.response?.data?.detail) {
        errorMsg += ` (${error.response.data.detail})`;
      }

      const errorMessage: Message = {
        role: 'assistant',
        content: errorMsg,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0"
      >
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-primary-700 text-white'
                  : 'bg-cream-50 border border-cream-300 text-gray-900'
              }`}
            >
              <div className={`text-sm prose prose-sm max-w-none prose-headings:mt-3 prose-headings:mb-2 prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 ${
                message.role === 'user' ? 'prose-invert' : ''
              }`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-cream-50 border border-cream-300 rounded-2xl px-4 py-3">
              <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Collapsible Sources Section - Much more compact */}
      {sources.length > 0 && (
        <div className="border-t border-cream-300 bg-cream-50 flex-shrink-0">
          <button
            onClick={() => setSourcesExpanded(!sourcesExpanded)}
            className="w-full px-4 py-2 flex items-center justify-between text-sm font-medium text-gray-700 hover:bg-cream-100 transition-colors"
          >
            <span className="flex items-center gap-2">
              <span className="font-semibold">Sources</span>
              <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">
                {sources.length}
              </span>
            </span>
            {sourcesExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {sourcesExpanded && (
            <div className="px-4 pb-3 max-h-32 overflow-y-auto">
              <div className="flex flex-wrap gap-1.5">
                {sources.map((source, index) => (
                  <a
                    key={source.id}
                    href={source.url || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs bg-white border border-cream-400 rounded-full px-2.5 py-1 hover:bg-primary-50 hover:border-primary-400 hover:text-primary-700 transition-colors"
                  >
                    <span className="font-medium text-primary-600">[{index + 1}]</span>
                    <span className="truncate max-w-[120px]">{source.label}</span>
                    {source.url && <ExternalLink className="w-3 h-3 flex-shrink-0" />}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="border-t border-cream-300 p-4 bg-white flex-shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about finance..."
            className="flex-1 px-4 py-3 border border-cream-400 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-cream-50"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-primary-700 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
}
