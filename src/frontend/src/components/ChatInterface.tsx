import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, CheckCircle2, X, Target } from 'lucide-react';
import { api } from '../services/api';
import type { Message } from '../types';

interface ChatInterfaceProps {
  sessionId: string;
}

interface ParsedAllocation {
  stocks: number;
  bonds: number;
  cash: number;
}

interface ExtendedMessage extends Message {
  allocationDismissed?: boolean;
}

export default function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ExtendedMessage[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m FinWhiz, your financial education assistant. How can I help you today?',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [applyingAllocation, setApplyingAllocation] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Parse generic allocation from AI response (stocks/bonds/cash %)
  const parseAllocation = (content: string): ParsedAllocation | null => {
    // Skip if already applied or dismissed
    if (content.includes('✓ Applied recommendation') || content.includes('✓ Applied asset allocation')) {
      return null;
    }

    // Try multiple patterns
    const patterns = [
      // Pattern 1: "60% stocks, 30% bonds, 10% cash"
      /(\d+)%?\s*(?:in\s+)?stocks?[,\s]+(\d+)%?\s*(?:in\s+)?bonds?[,\s]+(?:and\s+)?(\d+)%?\s*(?:in\s+)?(?:cash|money)/i,
      
      // Pattern 2: "stocks: 60%, bonds: 30%, cash: 10%"
      /stocks?:\s*(\d+)%?[,\s]+bonds?:\s*(\d+)%?[,\s]+(?:cash|money):\s*(\d+)%?/i,
    ];

    for (const pattern of patterns) {
      const match = content.match(pattern);
      if (match) {
        const stocks = parseInt(match[1]);
        const bonds = parseInt(match[2]);
        const cash = parseInt(match[3]);
        
        if (stocks + bonds + cash === 100 && stocks >= 0 && bonds >= 0 && cash >= 0) {
          return { stocks, bonds, cash };
        }
      }
    }

    // Fallback: Try to find individual percentages
    const stockMatch = content.match(/(\d+)%?\s*(?:in\s+)?stocks?/i);
    const bondMatch = content.match(/(\d+)%?\s*(?:in\s+)?bonds?/i);
    const cashMatch = content.match(/(\d+)%?\s*(?:in\s+)?(?:cash|money\s+market)/i);

    if (stockMatch && bondMatch && cashMatch) {
      const stocks = parseInt(stockMatch[1]);
      const bonds = parseInt(bondMatch[1]);
      const cash = parseInt(cashMatch[1]);

      if (stocks + bonds + cash === 100 && stocks >= 0 && bonds >= 0 && cash >= 0) {
        return { stocks, bonds, cash };
      }
    }

    return null;
  };

  // Parse asset-specific recommendations from AI response (AAPL: 25%, etc.)
  const parseAssetRecommendations = (content: string): Record<string, number> | null => {
    // Skip if already applied
    if (content.includes('✓ Applied asset allocation') || content.includes('✓ Applied recommendation')) {
      return null;
    }

    // Pattern: ticker followed by percentage (e.g., "AAPL: 25%" or "reduce AAPL to 25%")
    const tickerPattern = /([A-Z]{1,5}):?\s*(?:to\s+)?(\d+(?:\.\d+)?)%/g;
    const matches = [...content.matchAll(tickerPattern)];
    
    if (matches.length === 0) {
      return null;
    }

    const recommendations: Record<string, number> = {};
    for (const match of matches) {
      const ticker = match[1];
      const percentage = parseFloat(match[2]);
      
      // Only include valid tickers (1-5 uppercase letters) and valid percentages
      if (ticker.length <= 5 && percentage >= 0 && percentage <= 100) {
        recommendations[ticker] = percentage;
      }
    }

    // Only return if we found at least 2 asset recommendations
    return Object.keys(recommendations).length >= 2 ? recommendations : null;
  };

  const handleApplyAllocation = async (allocation: ParsedAllocation, messageIndex: number) => {
    const confirmed = window.confirm(
      `Apply this allocation?\n\n` +
      `Stocks: ${allocation.stocks}%\n` +
      `Bonds: ${allocation.bonds}%\n` +
      `Cash: ${allocation.cash}%\n\n` +
      `This will update your recommended allocation in the Portfolio tab.`
    );
    
    if (!confirmed) return;

    try {
      setApplyingAllocation(true);
      await api.saveCustomAllocation(sessionId, allocation);
      
      // Mark the original message as applied
      setMessages(prev => prev.map((msg, idx) => 
        idx === messageIndex 
          ? { ...msg, allocationDismissed: true }
          : msg
      ));

      // Add confirmation message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✓ Applied recommendation: ${allocation.stocks}% stocks, ${allocation.bonds}% bonds, ${allocation.cash}% cash. Check the Portfolio tab to see your updated allocation!`,
      }]);
      
    } catch (error) {
      console.error('Error applying allocation:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '✗ Sorry, I couldn\'t apply that allocation. Please try again.',
      }]);
    } finally {
      setApplyingAllocation(false);
    }
  };

  const handleApplyAssetRecommendation = async (recommendations: Record<string, number>, messageIndex: number) => {
    try {
      setApplyingAllocation(true);
      
      // Calculate specific targets
      const targetsResponse = await api.calculateAssetTargets(sessionId, recommendations);
      
      // Save to backend
      await api.saveAssetAllocationTarget(sessionId, {
        targets: targetsResponse.targets,
        cash_target_percent: 0,
        ai_rationale: messages[messageIndex].content.substring(0, 200) + '...'
      });
      
      // Mark as applied
      setMessages(prev => prev.map((msg, idx) => 
        idx === messageIndex 
          ? { ...msg, allocationDismissed: true }
          : msg
      ));

      // Add confirmation
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✓ Applied asset allocation targets. Check the Portfolio tab to see your target allocation plan with specific buy/sell actions!`,
      }]);
      
    } catch (error) {
      console.error('Error applying asset allocation:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '✗ Sorry, I couldn\'t apply that allocation. Please make sure you have uploaded your portfolio first.',
      }]);
    } finally {
      setApplyingAllocation(false);
    }
  };

  const handleDismissAllocation = (messageIndex: number) => {
    setMessages(prev => prev.map((msg, idx) => 
      idx === messageIndex 
        ? { ...msg, allocationDismissed: true }
        : msg
    ));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      await api.addMessage(sessionId, 'user', userMessage);
      const response = await api.query(userMessage, sessionId);

      const assistantMessage: ExtendedMessage = {
        role: 'assistant',
        content: response.answer,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      await api.addMessage(sessionId, 'assistant', response.answer);
    } catch (error) {
      console.error('Error querying LLM:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => {
          // Check for both types of recommendations
          const allocation = message.role === 'assistant' && !message.allocationDismissed 
            ? parseAllocation(message.content) 
            : null;
          
          const assetRecs = message.role === 'assistant' && !message.allocationDismissed
            ? parseAssetRecommendations(message.content)
            : null;
          
          return (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className="max-w-[80%]">
                <div
                  className={`rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
                
                {/* Show appropriate apply buttons */}
                {!message.allocationDismissed && message.role === 'assistant' && (
                  <>
                    {/* Generic allocation (stocks/bonds/cash) - only if no asset-specific recs */}
                    {allocation && !assetRecs && (
                      <div className="mt-2 flex items-center gap-2">
                        <button
                          onClick={() => handleApplyAllocation(allocation, index)}
                          disabled={applyingAllocation}
                          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {applyingAllocation ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              Applying...
                            </>
                          ) : (
                            <>
                              <CheckCircle2 className="w-4 h-4" />
                              Apply This Allocation
                            </>
                          )}
                        </button>
                        
                        <button
                          onClick={() => handleDismissAllocation(index)}
                          className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                          <X className="w-4 h-4" />
                          Not Now
                        </button>
                      </div>
                    )}

                    {/* Asset-specific recommendations (AAPL: 25%, etc.) */}
                    {assetRecs && (
                      <div className="mt-2 flex items-center gap-2">
                        <button
                          onClick={() => handleApplyAssetRecommendation(assetRecs, index)}
                          disabled={applyingAllocation}
                          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {applyingAllocation ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              Applying...
                            </>
                          ) : (
                            <>
                              <Target className="w-4 h-4" />
                              Apply Asset Targets
                            </>
                          )}
                        </button>
                        
                        <button
                          onClick={() => handleDismissAllocation(index)}
                          className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                          <X className="w-4 h-4" />
                          Not Now
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <Loader2 className="w-5 h-5 text-gray-600 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about investing, taxes, retirement planning..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
}