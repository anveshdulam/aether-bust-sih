import React, { useState, useRef, useEffect } from 'react';
import { X, Send, Bot, User, Loader2, Zap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAppStore } from '../../store/useAppStore';

interface Message {
  role: 'user' | 'model';
  content: string;
  id: string;
  toolCalls?: { name: string; status: string }[];
}

export function ChatWidget() {
  const { isChatOpen, setIsChatOpen, runId, leadTime, viewState, variable } = useAppStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  if (!isChatOpen) {
    return (
      <button
        onClick={() => setIsChatOpen(true)}
        className="absolute bottom-12 right-6 w-12 h-12 bg-accent hover:bg-accent/80 text-white rounded-full shadow-popover flex items-center justify-center z-50 transition-colors"
        title="Open AETHER Support"
      >
        <Bot size={24} />
      </button>
    );
  }

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      id: Date.now().toString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Prepare current UI snapshot
    const uiSnapshot = {
      run_id: runId,
      lead_time_day: leadTime,
      variable: variable,
      center_lat: viewState.latitude,
      center_lon: viewState.longitude,
      zoom: viewState.zoom,
    };

    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
          ui_snapshot: uiSnapshot,
        }),
      });

      if (!response.ok) throw new Error('Failed to fetch chat stream');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      const botMessageId = (Date.now() + 1).toString();
      let accumulatedText = '';
      let toolCalls: { name: string; status: string }[] = [];

      setMessages((prev) => [
        ...prev,
        { role: 'model', content: '', id: botMessageId, toolCalls: [] },
      ]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value, { stream: true });
        const lines = chunkText.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataString = line.substring(6);
            if (!dataString.trim()) continue;
            
            try {
              const data = JSON.parse(dataString);

              if (data.type === 'token') {
                accumulatedText += data.content;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === botMessageId
                      ? { ...m, content: accumulatedText }
                      : m
                  )
                );
              } else if (data.type === 'tool_start') {
                toolCalls.push({ name: data.name, status: 'running' });
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === botMessageId
                      ? { ...m, toolCalls: [...toolCalls] }
                      : m
                  )
                );
              } else if (data.type === 'tool_end') {
                toolCalls = toolCalls.map((tc) =>
                  tc.name === data.name ? { ...tc, status: 'done' } : tc
                );
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === botMessageId
                      ? { ...m, toolCalls: [...toolCalls] }
                      : m
                  )
                );
              } else if (data.type === 'ui_action') {
                // Execute client-side UI action
                if (data.action === 'set_day' && data.params.day) {
                  useAppStore.getState().setLeadTime(data.params.day);
                } else if (data.action === 'set_layer' && data.params.layer) {
                  useAppStore.getState().setActiveRaster(data.params.layer);
                } else if (data.action === 'fly_to' && data.params.lat && data.params.lon) {
                  useAppStore.getState().setViewState({
                    ...viewState,
                    latitude: data.params.lat,
                    longitude: data.params.lon,
                    zoom: data.params.zoom || 6.0
                  });
                } else if (data.action === 'select_point' && data.params.lat && data.params.lon) {
                  useAppStore.getState().setSelectedCell([data.params.lat, data.params.lon]);
                }
              } else if (data.type === 'error') {
                accumulatedText += `\n\n**Error:** ${data.content}`;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === botMessageId
                      ? { ...m, content: accumulatedText }
                      : m
                  )
                );
              } else if (data.type === 'done') {
                break;
              }
            } catch (e) {
              console.error('Failed to parse SSE JSON:', dataString);
            }
          }
        }
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'model',
          content: 'Sorry, I encountered an error connecting to the AETHER backend.',
          id: Date.now().toString(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="absolute bottom-24 right-6 w-96 max-h-[calc(100vh-8rem)] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl shadow-black/50 flex flex-col z-50 overflow-hidden transform transition-all duration-300">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-700 to-blue-600 border-b border-blue-800">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-sm">
              <Bot size={22} className="text-blue-600" />
            </div>
            <div className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-400 border-2 border-blue-600 rounded-full" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white leading-tight">AETHER Support</h3>
            <p className="text-xs text-blue-100/80">Typically replies instantly</p>
          </div>
        </div>
        <button
          onClick={() => setIsChatOpen(false)}
          className="p-1.5 hover:bg-white/20 rounded-full transition-colors text-white/80 hover:text-white"
        >
          <X size={20} />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5 bg-slate-50 min-h-[300px] max-h-[500px]">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-3 mt-4">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-2">
              <Bot size={32} className="text-blue-600" />
            </div>
            <h4 className="text-slate-800 font-medium">How can we help?</h4>
            <p className="text-sm text-slate-500 max-w-[220px]">
              Ask me to analyze regions, compare days, or explain forecast busts.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.role === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            {msg.role === 'model' && msg.toolCalls && msg.toolCalls.length > 0 && (
              <div className="flex flex-col space-y-1 mb-1 ml-1">
                {msg.toolCalls.map((tc, idx) => (
                  <div key={idx} className="flex items-center space-x-2 text-xs text-slate-500">
                    {tc.status === 'running' ? (
                      <Loader2 size={12} className="animate-spin text-blue-500" />
                    ) : (
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    )}
                    <span className="italic">Running {tc.name}...</span>
                  </div>
                ))}
              </div>
            )}
            
            <div className={`flex ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'} items-end space-x-2 space-x-reverse`}>
              {msg.role === 'model' && (
                <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mb-1 ml-1">
                   <Bot size={14} className="text-white" />
                </div>
              )}
              <div
                className={`max-w-[260px] p-3.5 shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-2xl rounded-tr-sm'
                    : 'bg-white text-slate-700 rounded-2xl rounded-tl-sm border border-slate-200/60'
                }`}
              >
                {msg.role === 'user' ? (
                  <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                ) : (
                  <div className="text-sm prose prose-slate prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex items-start ml-1 mt-2">
            <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mr-2">
              <Bot size={14} className="text-white" />
            </div>
            <div className="bg-white p-3.5 rounded-2xl rounded-tl-sm border border-slate-200/60 shadow-sm flex items-center space-x-1.5">
              <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" />
              <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Tool Chips (Quick Actions) */}
      <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 flex flex-col gap-2">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Suggested Questions</p>
        <div className="flex flex-col gap-2">
          <button
            onClick={() => setInput('Find the highest risk hotspot for Day 7')}
            className="text-sm px-4 py-2.5 rounded-xl bg-white text-slate-600 hover:text-blue-600 hover:bg-blue-50 transition-colors border border-slate-200 shadow-sm text-left font-medium flex items-center space-x-2"
          >
            <span>🔍</span>
            <span>Find Day 7 Hotspots</span>
          </button>
          <button
            onClick={() => {
              if (viewState.latitude && viewState.longitude) {
                setInput(`Why is it flagging a bust at ${viewState.latitude.toFixed(2)}N, ${viewState.longitude.toFixed(2)}E on Day ${leadTime}?`);
              } else {
                setInput(`Why is it flagging a bust here on Day ${leadTime}?`);
              }
            }}
            className="text-sm px-4 py-2.5 rounded-xl bg-white text-slate-600 hover:text-blue-600 hover:bg-blue-50 transition-colors border border-slate-200 shadow-sm text-left font-medium flex items-center space-x-2"
          >
            <span>🧠</span>
            <span>Explain this region</span>
          </button>
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-slate-100">
        <div className="flex items-end space-x-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="flex-1 bg-slate-50 border border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 rounded-xl text-sm text-slate-800 resize-none py-3 px-4 outline-none transition-all"
            rows={1}
            style={{
              height: Math.min(120, Math.max(44, input.split('\n').length * 20 + 24)) + 'px'
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="p-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-100 disabled:text-slate-400 text-white rounded-xl shadow-sm transition-colors flex-shrink-0"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
