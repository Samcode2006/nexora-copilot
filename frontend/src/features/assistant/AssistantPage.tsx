import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot,
  Send,
  ArrowRight
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, Button } from '../../components/common/UIComponents';

export const AssistantPage: React.FC = () => {
  const { assistantMessages, sendMessageToAssistant } = useApp();
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [assistantMessages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    sendMessageToAssistant(inputText.trim());
    setInputText('');
  };

  const handleQuickReply = (text: string) => {
    sendMessageToAssistant(text);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      {/* Header Banner */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-lg bg-[#263747] text-white flex items-center justify-center font-bold shadow-xs">
            <Bot className="w-5 h-5 text-steel-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-charcoal-900 tracking-tight">Nexora Placement Assistant</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                Context-Aware Co-pilot
              </span>
            </div>
            <p className="text-xs text-charcoal-600 mt-0.5">
              Ask about your match scores, interview prep for active rounds, or pending document approvals.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <Link to="/app/approvals">
            <Button variant="outline" size="sm">
              Approval Centre →
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Conversation Container */}
      <Panel className="flex flex-col h-[560px] bg-white overflow-hidden">
        {/* Messages History */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {assistantMessages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${
                msg.sender === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.sender === 'assistant' && (
                <div className="w-7 h-7 rounded bg-[#263747] text-white flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                  <Bot className="w-4 h-4 text-steel-400" />
                </div>
              )}

              <div
                className={`max-w-xl p-3.5 rounded-lg leading-relaxed whitespace-pre-wrap ${
                  msg.sender === 'user'
                    ? 'bg-[#263747] text-white rounded-br-none shadow-xs'
                    : 'bg-canvas-50 border border-charcoal-200 text-charcoal-900 rounded-bl-none'
                }`}
              >
                <p>{msg.content}</p>

                {/* Deep Action Link if present */}
                {msg.actionLink && (
                  <div className="mt-3 pt-2 border-t border-charcoal-200/60">
                    <Link to={msg.actionLink.to}>
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-white border border-charcoal-300 rounded font-semibold text-steel-700 hover:text-steel-900 shadow-subtle transition-colors text-[11px]">
                        <span>{msg.actionLink.label}</span>
                        <ArrowRight className="w-3 h-3" />
                      </span>
                    </Link>
                  </div>
                )}

                {/* Quick suggestions if present */}
                {msg.quickReplies && (
                  <div className="mt-3 pt-2.5 border-t border-charcoal-200/60 flex flex-wrap gap-1.5">
                    {msg.quickReplies.map((qr) => (
                      <button
                        key={qr}
                        type="button"
                        onClick={() => handleQuickReply(qr)}
                        className="px-2.5 py-1 bg-white border border-charcoal-200 hover:border-steel-400 rounded text-[11px] font-medium text-charcoal-800 hover:text-steel-700 transition-colors"
                      >
                        {qr} →
                      </button>
                    ))}
                  </div>
                )}

                <span
                  className={`block text-[10px] mt-1.5 text-right ${
                    msg.sender === 'user' ? 'text-slate-300' : 'text-charcoal-600'
                  }`}
                >
                  {msg.timestamp}
                </span>
              </div>

              {msg.sender === 'user' && (
                <div className="w-7 h-7 rounded bg-steel-600 text-white flex items-center justify-center shrink-0 mt-0.5 font-bold text-xs">
                  A
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="px-5 py-2.5 bg-canvas-50 border-t border-charcoal-200 flex items-center gap-2 overflow-x-auto text-[11px]">
          <span className="text-charcoal-600 font-semibold shrink-0">Try asking:</span>
          <button
            onClick={() => handleQuickReply('Review Vercel tailored resume')}
            className="px-2 py-0.5 bg-white border border-charcoal-200 hover:border-steel-400 rounded text-charcoal-700 hover:text-charcoal-900 whitespace-nowrap transition-colors"
          >
            Review Vercel resume
          </button>
          <button
            onClick={() => handleQuickReply('How should I prepare for Stripe Round 2?')}
            className="px-2 py-0.5 bg-white border border-charcoal-200 hover:border-steel-400 rounded text-charcoal-700 hover:text-charcoal-900 whitespace-nowrap transition-colors"
          >
            Stripe Round 2 Prep
          </button>
          <button
            onClick={() => handleQuickReply('Explain my missing skills for Datadog')}
            className="px-2 py-0.5 bg-white border border-charcoal-200 hover:border-steel-400 rounded text-charcoal-700 hover:text-charcoal-900 whitespace-nowrap transition-colors"
          >
            Datadog Gaps
          </button>
          <button
            onClick={() => handleQuickReply('What are my upcoming deadlines?')}
            className="px-2 py-0.5 bg-white border border-charcoal-200 hover:border-steel-400 rounded text-charcoal-700 hover:text-charcoal-900 whitespace-nowrap transition-colors"
          >
            Deadlines Summary
          </button>
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSend} className="p-3 border-t border-charcoal-200 bg-white flex items-center gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask anything about your placement applications, mock prep, or documents..."
            className="flex-1 bg-canvas-50 border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500 focus:bg-white transition-colors"
          />
          <Button
            type="submit"
            variant="primary"
            size="md"
            disabled={!inputText.trim()}
            icon={<Send className="w-3.5 h-3.5" />}
          >
            Send
          </Button>
        </form>
      </Panel>
    </div>
  );
};
