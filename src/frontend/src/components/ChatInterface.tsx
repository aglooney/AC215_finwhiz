import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, ExternalLink } from 'lucide-react';
import type { Message, Source } from '../types';
import { api } from '../services/api';

interface ChatInterfaceProps {
  sessionId: string;
}

export default function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hello! I'm FinWhiz, your financial education assistant. I can help you understand financial concepts, analyze your documents, and answer questions about investing, taxes, and retirement planning. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

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
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
              <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {sources.length > 0 && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <p className="text-sm font-semibold text-gray-700 mb-2">Sources:</p>
          <div className="flex flex-wrap gap-2">
            {sources.map((source, index) => (
              <a
                key={source.id}
                href={source.url || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs bg-white border border-gray-300 rounded-full px-3 py-1 hover:bg-primary-50 hover:border-primary-300 transition-colors"
              >
                <span className="font-medium">[{index + 1}]</span>
                <span>{source.label}</span>
                {source.url && <ExternalLink className="w-3 h-3" />}
              </a>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about finance..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
}
