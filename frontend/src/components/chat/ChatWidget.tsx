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

  if (!isChatOpen) return null;

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
    <div className="absolute top-20 right-4 w-96 max-h-[calc(100vh-6rem)] bg-[#0A0E17]/90 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden transform transition-all duration-300">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10 bg-white/5">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Zap size={18} className="text-blue-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white tracking-wide">AETHER Analyst</h3>
            <p className="text-xs text-emerald-400 font-mono">Online</p>
          </div>
        </div>
        <button
          onClick={() => setIsChatOpen(false)}
          className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-white"
        >
          <X size={18} />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[500px]">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-50">
            <Bot size={48} className="text-slate-400" />
            <p className="text-sm text-slate-400 max-w-[200px]">
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
              <div className="flex flex-col space-y-1 mb-2">
                {msg.toolCalls.map((tc, idx) => (
                  <div key={idx} className="flex items-center space-x-2 text-xs text-slate-400 bg-white/5 px-2 py-1 rounded-md">
                    {tc.status === 'running' ? (
                      <Loader2 size={12} className="animate-spin text-blue-400" />
                    ) : (
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    )}
                    <span className="font-mono">Call {tc.name}()</span>
                  </div>
                ))}
              </div>
            )}
            
            <div
              className={`max-w-[85%] p-3 rounded-2xl ${
                msg.role === 'user'
                  ? 'bg-blue-600/80 text-white rounded-br-sm'
                  : 'bg-white/10 text-slate-200 rounded-bl-sm border border-white/5'
              }`}
            >
              {msg.role === 'user' ? (
                <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
              ) : (
                <div className="text-sm prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex items-start">
            <div className="bg-white/10 p-3 rounded-2xl rounded-bl-sm border border-white/5 flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Tool Chips (Quick Actions) */}
      <div className="px-3 pb-2 pt-1 bg-white/5 border-t border-white/10 flex gap-2 overflow-x-auto custom-scrollbar whitespace-nowrap">
        <button
          onClick={() => setInput('Find the highest risk hotspot for Day 7')}
          className="text-xs px-3 py-1.5 rounded-full bg-blue-500/20 text-blue-300 hover:bg-blue-500/40 transition-colors border border-blue-500/30"
        >
          🔍 Find Day 7 Hotspots
        </button>
        <button
          onClick={() => {
            if (viewState.latitude && viewState.longitude) {
              setInput(`Why is it flagging a bust at ${viewState.latitude.toFixed(2)}N, ${viewState.longitude.toFixed(2)}E on Day ${leadTime}?`);
            } else {
              setInput(`Why is it flagging a bust here on Day ${leadTime}?`);
            }
          }}
          className="text-xs px-3 py-1.5 rounded-full bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/40 transition-colors border border-emerald-500/30"
        >
          🧠 Explain this region
        </button>
        <button
          onClick={() => setInput('Show me the error magnitude layer instead of probability')}
          className="text-xs px-3 py-1.5 rounded-full bg-purple-500/20 text-purple-300 hover:bg-purple-500/40 transition-colors border border-purple-500/30"
        >
          🗺️ Show Error Map
        </button>
      </div>

      {/* Input Area */}
      <div className="p-3 bg-white/5">
        <div className="flex items-end space-x-2 bg-black/30 p-2 rounded-xl border border-white/10 focus-within:border-blue-500/50 transition-colors">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask AETHER..."
            className="flex-1 bg-transparent border-none focus:ring-0 text-sm text-white resize-none max-h-32 min-h-[40px] py-2 px-2 custom-scrollbar outline-none"
            rows={1}
            style={{
              height: Math.min(120, Math.max(40, input.split('\n').length * 20 + 20)) + 'px'
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="p-2 bg-blue-600 hover:bg-blue-500 disabled:bg-white/10 disabled:text-slate-500 text-white rounded-lg transition-colors flex-shrink-0"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
