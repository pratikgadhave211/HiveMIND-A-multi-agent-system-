import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Send, CheckCircle2, Loader2, ChevronDown, DollarSign, AlertTriangle, ShieldAlert, Zap, Brain, Plus, MessageSquare, Trash2 } from 'lucide-react';
import ResearchBoard from './components/ResearchBoard';
import TypewriterEffect from './components/TypewriterEffect';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

const AGENT_LABELS = {
  intent_router: 'Intent Router',
  fast_search: 'Fast Search',
  query_analyzer: 'Query Analyzer',
  knowledge_analyzer: 'Knowledge Analyzer',
  answer_contract_builder: 'Answer Contract',
  execution_planner: 'Execution Planner',
  retrieval_manager: 'Retrieval Manager',
  compare_router: 'Compare Router',
  knowledge_gateway: 'Knowledge Gateway',
  query_rewriter: 'Query Rewriter',
  query_router: 'Query Router',
  context_assembly: 'Context Assembly',
  orchestrator: 'Orchestrator',
  url_deduplicator: 'URL Deduplicator',
  page_fetcher: 'Page Fetcher',
  chunking_engine: 'Chunking Engine',
  reranker: 'Cross-Encoder Reranker',
  synthesizer: 'Synthesizer',
  critics: 'Critics',
  evidence_verifier: 'Evidence Verifier',
  citations: 'Citation Builder',
  response_composer: 'Response Composer',
  markdown_renderer: 'Markdown Renderer',
  fact_checks: 'Fact Checker',
  finalize: 'Finalizer',
  news_agent: 'News Agent',
  shopping_agent: 'Shopping Agent',
  general_agent: 'General Agent',
  live_score_agent: 'Live Score Agent',
  finance_agent: 'Finance Agent',
  coding_agent: 'Coding Agent',
};

const AGENT_ICONS = {
  intent_router: '🎯',
  query_analyzer: '🔬',
  knowledge_analyzer: '📚',
  answer_contract_builder: '📋',
  execution_planner: '⚡',
  orchestrator: '🧠',
  url_deduplicator: '🔗',
  page_fetcher: '📄',
  chunking_engine: '✂️',
  reranker: '📊',
  synthesizer: '🧪',
  critics: '🔍',
  evidence_verifier: '🛡️',
  citations: '📎',
  response_composer: '✍️',
  markdown_renderer: '🎨',
  fact_checks: '✅',
  finalize: '🏁',
  news_agent: '📰',
  shopping_agent: '🛍️',
  fast_search: '⚡',
  general_agent: '🌐',
  live_score_agent: '⚽',
  finance_agent: '💹',
  coding_agent: '💻',
  retrieval_manager: '📥',
  compare_router: '🔀',
  knowledge_gateway: '🚪',
  query_rewriter: '✏️',
  query_router: '🧭',
  context_assembly: '🧩',
};

function getLabel(node) {
  return AGENT_LABELS[node] || node.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
function getIcon(node) {
  return AGENT_ICONS[node] || '⚙️';
}

export default function App() {
  const [input, setInput] = useState('');
  const [expandedStepKeys, setExpandedStepKeys] = useState({});
  const toggleStep = (key) => setExpandedStepKeys(prev => ({ ...prev, [key]: !prev[key] }));
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem('chat_sessions');
    if (!saved) return [];

    // Sanitize loaded sessions: any 'running' messages or steps from past sessions are permanently broken, so mark them as error
    const parsed = JSON.parse(saved);
    return parsed.map(session => ({
      ...session,
      messages: session.messages.map(msg => ({
        ...msg,
        status: msg.status === 'running' ? 'error' : msg.status,
        steps: msg.steps ? msg.steps.map(s => ({ ...s, status: s.status === 'running' ? 'error' : s.status })) : []
      }))
    }));
  });
  const [activeSessionId, setActiveSessionId] = useState(() => {
    return localStorage.getItem('active_session_id') || Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  });
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('chat_sessions');
    const active = localStorage.getItem('active_session_id');
    if (saved && active) {
      const parsed = JSON.parse(saved);
      const session = parsed.find(s => s.id === active);
      if (session) {
        return session.messages.map(msg => ({
          ...msg,
          status: msg.status === 'running' ? 'error' : msg.status,
          steps: msg.steps ? msg.steps.map(s => ({ ...s, status: s.status === 'running' ? 'error' : s.status })) : []
        }));
      }
    }
    return [];
  });
  const [loading, setLoading] = useState(false);
  const [searchMode, setSearchMode] = useState('simple');
  const threadId = activeSessionId;
  const messagesEndRef = useRef(null);
  const stopProcessRef = useRef(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    if (file.type !== 'application/pdf') {
      alert("Only PDF files are supported!");
      return;
    }
    
    const formData = new FormData();
    formData.append("file", file);
    
    setIsUploading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        alert(data.message + ` (${data.chunks_processed} chunks)`);
      } else {
        alert("Upload failed: " + (data.detail || "Unknown error"));
      }
    } catch (error) {
      console.error(error);
      alert("Error uploading file");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleStop = () => {
    if (stopProcessRef.current) {
      stopProcessRef.current();
      stopProcessRef.current = null;
    }
  };

  const deleteChat = (id, e) => {
    if (e) e.stopPropagation();
    const newSessions = sessions.filter(s => s.id !== id);
    setSessions(newSessions);
    setDeleteConfirmId(null);
    if (activeSessionId === id) {
      if (newSessions.length > 0) {
        switchChat(newSessions[0].id);
      } else {
        createNewChat();
      }
    }
  };

  useEffect(() => {
    setSessions(prev => {
      const existing = prev.find(s => s.id === activeSessionId);
      let newTitle = existing?.title || 'New Conversation';
      if (!existing && messages.length > 0 && messages[0].role === 'user') {
        newTitle = messages[0].content.substring(0, 30) + (messages[0].content.length > 30 ? '...' : '');
      } else if (existing && messages.length > 0 && existing.title === 'New Conversation' && messages[0].role === 'user') {
        newTitle = messages[0].content.substring(0, 30) + (messages[0].content.length > 30 ? '...' : '');
      }

      // SAFETY CHECK: Prevent wiping out a session's messages if a state synchronization issue causes `messages` to be temporarily empty.
      if (existing && messages.length === 0 && existing.messages.length > 0) {
        return prev;
      }

      const updatedSession = { id: activeSessionId, title: newTitle, messages: messages };

      if (!existing) {
        if (messages.length === 0) return prev;
        return [updatedSession, ...prev];
      }
      return prev.map(s => s.id === activeSessionId ? updatedSession : s);
    });
  }, [messages, activeSessionId]);

  useEffect(() => {
    localStorage.setItem('chat_sessions', JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    localStorage.setItem('active_session_id', activeSessionId);
  }, [activeSessionId]);

  const createNewChat = () => {
    const newId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    setActiveSessionId(newId);
    setMessages([]);
    // NOTE: Do NOT reset searchMode here — mode is per-message, not per-session
  };
  const switchChat = async (id) => {
    if (loading) return;

    // Switch UI immediately
    setActiveSessionId(id);
    const session = sessions.find(s => s.id === id);
    let currentMessages = session ? session.messages : [];

    // If local messages are empty, try fetching from the backend database!
    if (currentMessages.length === 0) {
      setMessages([]);
      setLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/history/${id}`);
        const data = await response.json();

        if (data && data.user_query && data.final_report) {
          const userMsg = { id: Date.now().toString(), role: 'user', content: data.user_query };
          const botMsg = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: data.final_report,
            status: 'done',
            steps: [], // Historic steps are skipped
            claims: data.claims || [],
            cost: 0,
            startTime: Date.now(),
          };
          currentMessages = [userMsg, botMsg];
        }
      } catch (err) {
        console.error("Failed to fetch history:", err);
      }
      setLoading(false);
    }

    setMessages(currentMessages);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || loading) return;

    const query = input;
    const userMsg = { id: Date.now().toString(), role: 'user', content: query, mode: searchMode };
    const botMsgId = (Date.now() + 1).toString();
    const botMsg = {
      id: botMsgId,
      role: 'assistant',
      content: '',
      status: 'running',
      // steps: [{node, label, icon, timeTaken: null|number, status: 'running'|'done'}]
      steps: [],
      claims: [],
      cost: 0,
      startTime: Date.now(),
    };

    setMessages(prev => [...prev, userMsg, botMsg]);
    setInput('');
    setLoading(true);

    const es = new EventSource(`${API_BASE_URL}/api/stream?message=${encodeURIComponent(query)}&mode=${searchMode}&thread_id=${threadId}`);

    stopProcessRef.current = () => {
      es.close();
      setLoading(false);
      setMessages(prev => prev.map(msg =>
        msg.id === botMsgId ? { ...msg, status: 'error', content: 'Stopped by user.' } : msg
      ));
    };

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'ping') return;

        if (data.type === 'node_start') {
          // Node just began — add it with spinner
          const { node } = data;
          setMessages(prev => prev.map(msg => {
            if (msg.id !== botMsgId) return msg;
            // Don't duplicate
            if (msg.steps.find(s => s.node === node && s.status === 'running')) return msg;
            return {
              ...msg,
              steps: [...msg.steps, { node, label: getLabel(node), icon: getIcon(node), timeTaken: null, status: 'running' }]
            };
          }));

        } else if (data.type === 'agent_update') {
          // Node finished — flip it to done with elapsed time
          const { node, time_taken } = data;
          setMessages(prev => prev.map(msg => {
            if (msg.id !== botMsgId) return msg;

            let steps = msg.steps.map(s =>
              s.node === node
                ? { ...s, timeTaken: time_taken ?? 0, status: 'done', output: data.node_output }
                : s
            );
            // Fallback: node_start was missed
            if (!steps.find(s => s.node === node)) {
              steps = [...steps, { node, label: getLabel(node), icon: getIcon(node), timeTaken: time_taken ?? 0, status: 'done', output: data.node_output }];
            }

            const updated = { ...msg, steps, cost: msg.cost + 0.04 };
            if (data.content) updated.content = data.content;
            if (data.claims) updated.claims = data.claims;
            return updated;
          }));

        } else if (data.type === 'done') {
          setMessages(prev => prev.map(msg =>
            msg.id === botMsgId
              ? { ...msg, status: 'done', steps: msg.steps.map(s => ({ ...s, status: 'done' })) }
              : msg
          ));
          es.close();
          setLoading(false);

        } else if (data.type === 'error') {
          setMessages(prev => prev.map(msg =>
            msg.id === botMsgId
              ? {
                ...msg,
                status: 'error',
                content: data.message || 'An error occurred.',
                steps: msg.steps.map(s => ({ ...s, status: s.status === 'running' ? 'error' : s.status }))
              }
              : msg
          ));
          es.close();
          setLoading(false);
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    };

    es.onerror = () => {
      setMessages(prev => prev.map(msg =>
        msg.id === botMsgId
          ? {
            ...msg,
            status: 'error',
            content: 'Connection to server lost.',
            steps: msg.steps.map(s => ({ ...s, status: s.status === 'running' ? 'error' : s.status }))
          }
          : msg
      ));
      es.close();
      setLoading(false);
    };
  };

  const renderTrustBadge = (score) => {
    if (score >= 80) return <span className="bg-neutral-900 text-white text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1 w-max"><CheckCircle2 className="w-3 h-3" /> HIGH ({score})</span>;
    if (score >= 50) return <span className="bg-amber-500 text-white text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1 w-max"><AlertTriangle className="w-3 h-3" /> MED ({score})</span>;
    return <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1 w-max"><ShieldAlert className="w-3 h-3" /> LOW ({score})</span>;
  };

  return (
    <div className="flex h-screen bg-[var(--color-bg-base)] font-sans">
      {/* Sidebar */}
      <div className="w-64 hivemind-sidebar text-white flex flex-col shrink-0 hidden md:flex">
        <div className="p-4 border-b border-[var(--color-border-subtle)]">
          <button
            onClick={createNewChat}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 hivemind-new-chat-btn py-2 px-4 rounded-lg font-medium disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map(s => (
            <div key={s.id} className="relative group">
              <button
                onClick={() => switchChat(s.id)}
                disabled={loading}
                className={`w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 text-sm hivemind-sidebar-btn ${activeSessionId === s.id ? 'bg-[var(--color-bg-elevated)] text-[var(--color-ai-accent)] font-medium border-l-2 border-[var(--color-ai-accent)]' : 'text-[var(--color-text-secondary)] hover:text-white'} disabled:opacity-50`}
              >
                <MessageSquare className="w-4 h-4 shrink-0" />
                <span className="truncate pr-6">{s.title}</span>
              </button>
              {!loading && (
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteConfirmId(s.id); }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-white hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col h-screen relative min-w-0">
        <header className="hivemind-header p-4 text-white flex items-center justify-center shrink-0">
          <div className="flex items-center gap-3">
            <span className="hivemind-emoji">🐝</span>
            <div>
              <h1 className="hivemind-title">HiveMind</h1>
              <p className="hivemind-subtitle">A Multi-Agent System</p>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-8 flex justify-center">
          <div className="w-full max-w-3xl space-y-6">
            <AnimatePresence initial={false}>
              {messages.length === 0 ? (
                <motion.div
                  key="empty-state"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.3 }}
                  className="flex flex-col items-center justify-center h-full text-[var(--color-text-secondary)] mt-24"
                >
                  <span className="text-5xl mb-4 hivemind-emoji">🐝</span>
                  <p className="text-lg font-medium text-[var(--color-text-primary)]">Ready for your query</p>
                  <p className="text-sm text-[var(--color-text-muted)]">The hive is standing by.</p>
                </motion.div>
              ) : (
                messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, ease: 'easeOut' }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[88%] rounded-2xl px-5 py-4 ${msg.role === 'user'
                        ? 'bg-[var(--color-bubble-user)] text-[var(--color-text-primary)] shadow-sm rounded-tr-none'
                        : 'bg-[var(--color-bubble-ai)] border border-neutral-800 shadow-sm rounded-tl-none text-[var(--color-text-primary)]'
                      }`}>
                      {msg.role === 'user' ? (
                        <div>
                          <p className="text-[15px] leading-relaxed">{msg.content}</p>
                          {msg.mode && (
                            <span className={`inline-flex items-center gap-1 mt-1.5 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ${msg.mode === 'complex' ? 'bg-purple-500/20 text-purple-300' : 'bg-neutral-700/50 text-gray-400'}`}>
                              {msg.mode === 'complex' ? '🧠 Deep Research' : '⚡ Normal'}
                            </span>
                          )}
                        </div>
                      ) : (
                        <div className="space-y-4">

                          {/* ---- Agent Steps Accordion ---- */}
                          <div className="bg-[var(--color-bg-surface)] rounded-xl border border-neutral-800 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                            <details open={msg.status === 'running'}>
                              <summary className="flex items-center justify-between px-4 py-3 cursor-pointer select-none list-none group">
                                <div className="flex items-center gap-2">
                                  {msg.status === 'running'
                                    ? <Loader2 className="w-4 h-4 text-[var(--color-ai-accent)] animate-spin" />
                                    : <CheckCircle2 className="w-4 h-4 text-[var(--color-success)]" />}
                                  <span className="text-sm font-semibold text-white">
                                    {msg.status === 'running'
                                      ? `Running — ${msg.steps.filter(s => s.status === 'done').length} agents done`
                                      : `${msg.steps.length} agents · ${((Date.now() - msg.startTime) / 1000).toFixed(1)}s total`}
                                  </span>
                                </div>
                                <ChevronDown className="w-4 h-4 text-white transition-transform" />
                              </summary>

                              {/* Step rows */}
                              <div className="border-t border-neutral-800 divide-y divide-slate-100">
                                {msg.steps.length === 0 && msg.status === 'running' && (
                                  <div className="flex items-center gap-2.5 px-4 py-3 text-sm text-gray-300">
                                    <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-300" />
                                    <span>Starting…</span>
                                  </div>
                                )}
                                {msg.steps.map((step, idx) => {
                                  const stepKey = `${msg.id}-${step.node}-${idx}`;
                                  const isExpanded = expandedStepKeys[stepKey];
                                  return (
                                    <div key={idx} className="border-b border-neutral-800 last:border-0">
                                      <div
                                        onClick={() => step.output && toggleStep(stepKey)}
                                        className={`flex items-center justify-between px-4 py-2.5 text-sm transition-colors ${step.status === 'running' ? 'bg-neutral-900' : ''
                                          } ${step.output ? 'cursor-pointer hover:bg-neutral-900/50' : ''}`}
                                      >
                                        <div className="flex items-center gap-2.5">
                                          <span className="text-base leading-none w-5 text-center">{step.icon}</span>
                                          <span className={`font-medium ${step.status === 'running' ? 'text-[var(--color-ai-accent)]' : 'text-white'}`}>
                                            {step.label}
                                          </span>
                                        </div>
                                        <div className="flex items-center gap-2 ml-4 shrink-0">
                                          {step.status === 'running' ? (
                                            <>
                                              <span className="text-xs text-[var(--color-ai-accent)] font-semibold animate-pulse">running…</span>
                                              <div className="w-3.5 h-3.5 rounded-full border-2 border-[var(--color-ai-accent)] border-t-transparent animate-spin" />
                                            </>
                                          ) : (
                                            <>
                                              <span className="text-xs text-white">{step.timeTaken}s</span>
                                              <CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-success)]" />
                                            </>
                                          )}
                                        </div>
                                      </div>
                                      <AnimatePresence>
                                        {isExpanded && step.output && (
                                          <motion.div
                                            key="step-output"
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="px-4 pb-3 pt-2 bg-black text-[11px] font-mono text-gray-300 overflow-x-auto whitespace-pre-wrap border-t border-neutral-800"
                                          >
                                            {typeof step.output === 'string' ? step.output : JSON.stringify(step.output, null, 2)}
                                          </motion.div>
                                        )}
                                      </AnimatePresence>
                                    </div>
                                  );
                                })}
                              </div>

                              {/* Cost */}
                              {msg.cost > 0 && (
                                <div className="border-t border-neutral-800 flex items-center justify-between px-4 py-2 text-xs font-semibold text-gray-300 bg-black">
                                  <span>Estimated cost</span>
                                  <span className="flex items-center gap-0.5"><DollarSign className="w-3 h-3" />{msg.cost.toFixed(2)}</span>
                                </div>
                              )}
                            </details>
                          </div>

                          {/* ---- Final Report ---- */}
                          {msg.content ? (
                            <motion.div
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className="prose prose-sm max-w-none border-t border-neutral-800 pt-4 text-[var(--color-text-primary)]"
                            >
                              <TypewriterEffect content={msg.content} isRunning={msg.status === 'running'} />
                              {msg.status === 'running' && (
                                <span className="inline-block w-2 h-4 ml-1 bg-[var(--color-ai-accent)] animate-pulse align-middle" />
                              )}
                            </motion.div>
                          ) : msg.status === 'running' && (
                            <div className="flex items-center gap-1.5 pt-6 pb-2 border-t border-neutral-800">
                              <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1 }} className="w-2 h-2 rounded-full bg-[var(--color-ai-accent)] opacity-60" />
                              <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} className="w-2 h-2 rounded-full bg-[var(--color-ai-accent)] opacity-60" />
                              <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} className="w-2 h-2 rounded-full bg-[var(--color-ai-accent)] opacity-60" />
                            </div>
                          )}

                          {/* ---- Claims / Citations ---- */}
                          {msg.claims && msg.claims.length > 0 && (
                            <motion.div
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="mt-4 border-t border-neutral-800 pt-4 space-y-3"
                            >
                              <h4 className="text-[11px] font-bold text-white uppercase tracking-widest">Verified Claims</h4>
                              <div className="flex flex-col gap-3">
                                {msg.claims.map((c, i) => (
                                  <div key={i} className="bg-black border border-neutral-800 rounded-xl p-3.5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--color-success)] opacity-80" />
                                    <div className="pl-2">
                                      <p className="text-sm font-medium text-white leading-snug">{c.claim}</p>
                                      <div className="mt-2.5 flex items-center justify-between">
                                        {renderTrustBadge(c.trust_score)}
                                        {c.citations?.length > 0 && (
                                          <div className="flex gap-2 flex-wrap justify-end">
                                            {c.citations.map((url, j) => {
                                              let domain = url;
                                              try {
                                                domain = new URL(url).hostname.replace('www.', '');
                                              } catch (e) { }
                                              return (
                                                <a key={j} href={url} target="_blank" rel="noreferrer"
                                                  className="text-[10px] font-medium px-2 py-1 bg-neutral-900 text-gray-300 rounded-full hover:bg-[var(--color-ai-accent)] hover:text-white transition-colors flex items-center gap-1">
                                                  🔗 {domain}
                                                </a>
                                              );
                                            })}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </motion.div>
                          )}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>
        </main>

        <footer className="p-4 hivemind-footer flex flex-col items-center justify-center gap-3">
          {/* Mode Toggle */}
          <div className="w-full max-w-3xl flex justify-center">
            <div className="hivemind-mode-toggle p-1 rounded-xl flex items-center">
              <button
                onClick={() => {
                  if (searchMode !== 'simple') {
                    setSearchMode('simple');
                  }
                }}
                disabled={loading}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${searchMode === 'simple' ? 'hivemind-mode-active' : 'text-[var(--color-text-muted)] hover:text-white'
                  }`}
              >
                <Zap className="w-4 h-4" />
                Normal Search
              </button>
              <button
                onClick={() => {
                  if (searchMode !== 'complex') {
                    setSearchMode('complex');
                  }
                }}
                disabled={loading}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${searchMode === 'complex' ? 'hivemind-mode-active' : 'text-[var(--color-text-muted)] hover:text-white'
                  }`}
              >
                <Brain className="w-4 h-4" />
                Deep Research
              </button>
            </div>
          </div>

          <div className="w-full max-w-3xl relative">
            <motion.div
              initial={false}
              animate={{ boxShadow: input.trim() ? '0 4px 14px 0 rgba(255, 179, 0, 0.15)' : '0 2px 5px 0 rgba(0, 0, 0, 0.1)' }}
              className="relative w-full rounded-xl hivemind-input flex items-center"
            >
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: "none" }}
                accept="application/pdf"
                onChange={handleFileUpload}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="ml-2 p-2 text-gray-400 hover:text-white transition-colors flex-shrink-0"
                title="Upload PDF"
              >
                {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
              </button>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder={searchMode === 'simple' ? "Ask a quick factual question..." : "Enter a deep research topic..."}
                className="w-full bg-transparent pl-2 pr-14 py-3 focus:outline-none text-[15px] flex-1"
                disabled={loading}
              />
              {loading ? (
                <button
                  onClick={handleStop}
                  className="absolute right-2 top-1.5 bottom-1.5 bg-red-500 text-white rounded-lg px-3 flex items-center justify-center hover:bg-red-600 transition-colors"
                  title="Stop processing"
                >
                  <div className="w-3.5 h-3.5 bg-black rounded-[2px]" />
                </button>
              ) : (
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="absolute right-2 top-1.5 bottom-1.5 hivemind-send-btn rounded-lg px-3 flex items-center justify-center disabled:opacity-50 disabled:bg-[var(--color-bg-elevated)]"
                >
                  <Send className="w-5 h-5" />
                </button>
              )}
            </motion.div>
          </div>
        </footer>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center hivemind-modal-overlay">
          <div className="hivemind-modal rounded-xl shadow-xl max-w-sm w-full p-6 m-4 animate-in fade-in zoom-in duration-200">
            <h3 className="text-lg font-bold text-white mb-2">Delete Conversation</h3>
            <p className="text-[var(--color-text-secondary)] mb-6 text-sm">Are you sure you want to delete this chat? This action cannot be undone.</p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="px-4 py-2 rounded-lg font-medium text-white bg-[var(--color-bg-elevated)] hover:bg-[var(--color-bg-card)] transition-colors"
              >
                No
              </button>
              <button
                onClick={(e) => deleteChat(deleteConfirmId, e)}
                className="px-4 py-2 rounded-lg font-medium text-white hivemind-delete-btn transition-colors"
              >
                Yes, Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
