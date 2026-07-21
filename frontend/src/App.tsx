import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ShieldCheck, Database as DatabaseIcon, Network, MessageSquare, FileText, Search, Tag, Users, BookOpen, Layers, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { cn } from './lib/utils';
import { TextEffect } from '../components/motion-primitives/text-effect';

const api = axios.create({ baseURL: 'http://127.0.0.1:8000/api' });

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  confidence?: string;
  route?: string;
  sources?: any[];
  tool_calls?: any[];
}

export default function App() {
  const [mode, setMode] = useState<'chat' | 'analysis'>('chat');
  
  // Chat State
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: 'Hello! I am your Hybrid GraphRAG Assistant. Ask me anything about your research papers, authors, or methodology.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Analysis State
  const [analysisQuery, setAnalysisQuery] = useState('');
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState('');

  const scrollRef = useRef<HTMLDivElement>(null);
  const vantaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let vantaEffect: any = null;
    if (vantaRef.current && (window as any).VANTA) {
      vantaEffect = (window as any).VANTA.NET({
        el: vantaRef.current,
        mouseControls: true,
        touchControls: true,
        gyroControls: false,
        minHeight: 200.00,
        minWidth: 200.00,
        scale: 1.00,
        scaleMobile: 1.00,
        color: 0xff3f81,
        backgroundColor: 0x23153c,
        points: 10,
        maxDistance: 20,
        spacing: 15,
        showDots: true
      });
    }
    return () => {
      if (vantaEffect) vantaEffect.destroy();
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await api.post('/chat', { message: userMsg });
      setMessages(prev => [...prev, { 
        id: (Date.now() + 1).toString(), 
        role: 'assistant', 
        content: res.data.answer,
        confidence: res.data.confidence,
        route: res.data.route,
        sources: res.data.sources,
        tool_calls: res.data.tool_calls
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        id: (Date.now() + 1).toString(), 
        role: 'assistant', 
        content: "I encountered an error connecting to the backend. Please ensure the FastAPI server is running." 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!analysisQuery.trim() || analysisLoading) return;
    
    setAnalysisLoading(true);
    setAnalysisError('');
    setAnalysisResult(null);
    
    try {
      const res = await api.get(`/analyze-paper?q=${encodeURIComponent(analysisQuery)}`);
      setAnalysisResult(res.data);
    } catch (err: any) {
      setAnalysisError(err.response?.data?.detail || "Failed to analyze paper.");
    } finally {
      setAnalysisLoading(false);
    }
  };

  const getRouteIcon = (route: string) => {
    if (route === 'GRAPH') return <Network className="w-3 h-3" />;
    if (route === 'VECTOR') return <DatabaseIcon className="w-3 h-3" />;
    if (route === 'HYBRID') return <ShieldCheck className="w-3 h-3" />;
    return <Bot className="w-3 h-3" />;
  };

  const getConfidenceColor = (conf: string) => {
    if (conf?.includes('HIGH')) return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
    if (conf?.includes('MEDIUM')) return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
    return 'bg-rose-500/10 text-rose-500 border-rose-500/20';
  };

  return (
    <div className="min-h-screen flex flex-col text-white relative overflow-hidden">
      {/* 3D Background */}
      <div ref={vantaRef} className="fixed inset-0 -z-10" />

      {/* Navbar directly integrated */}
      <header className="h-16 border-b border-surface flex items-center justify-between px-6 bg-surface/30 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-2 font-bold text-lg text-white">
          <DatabaseIcon className="text-pink-500 w-6 h-6" />
          <span>Hybrid GraphRAG</span>
        </div>
        
        {/* Mode Switcher */}
        <div className="flex items-center bg-black/50 p-1 rounded-xl border border-white/10 shadow-inner">
          <button
            onClick={() => setMode('chat')}
            className={cn("flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all", mode === 'chat' ? "bg-surface text-white shadow" : "text-white/50 hover:text-white")}
          >
            <MessageSquare className="w-4 h-4" />
            Chat
          </button>
          <button
            onClick={() => setMode('analysis')}
            className={cn("flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all", mode === 'analysis' ? "bg-cyan-900/30 text-cyan-400 shadow border border-cyan-500/20" : "text-white/50 hover:text-white")}
          >
            <FileText className="w-4 h-4" />
            Paper Analysis
          </button>
        </div>
        
        <div className="w-[150px]"></div> {/* Spacer for centering flex */}
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden relative z-10">
        {mode === 'chat' ? (
          <div className="flex-1 flex flex-col items-center p-4">
            <div className="w-full max-w-4xl flex-1 flex flex-col overflow-hidden">
              
              {/* Chat History */}
              <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map(msg => (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    key={msg.id} 
                    className={cn("flex gap-4 max-w-[85%]", msg.role === 'user' ? "ml-auto flex-row-reverse" : "")}
                  >
                    <div className={cn("w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg", msg.role === 'user' ? "bg-primary/20 text-primary" : "bg-accent/20 text-accent")}>
                      {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                    </div>
                    
                    <div className="space-y-2">
                      <div className={cn("p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap shadow-md min-h-[60px]", msg.role === 'user' ? "bg-pink-600 text-white rounded-tr-none" : "bg-black/50 border border-white/10 rounded-tl-none")}>
                        {msg.role === 'assistant' ? (
                          <TextEffect preset="fade-in-blur" speedReveal={1.1} speedSegment={0.3}>
                            {msg.content}
                          </TextEffect>
                        ) : (
                          msg.content
                        )}
                      </div>
                      
                      {msg.role === 'assistant' && msg.route && (
                        <div className="flex gap-2 items-center px-1">
                          <span className="flex items-center gap-1 text-[10px] uppercase font-bold tracking-wider px-2 py-1 rounded-full bg-surface border border-surface text-muted shadow-sm">
                            {getRouteIcon(msg.route)}
                            {msg.route}
                          </span>
                          <span className={cn("flex items-center gap-1 text-[10px] uppercase font-bold tracking-wider px-2 py-1 rounded-full border shadow-sm", getConfidenceColor(msg.confidence || 'LOW'))}>
                            {msg.confidence}
                          </span>
                        </div>
                      )}
                      
                      {msg.role === 'assistant' && msg.tool_calls && msg.tool_calls.length > 0 && (
                        <div className="flex flex-col gap-2 mt-2 pt-2 border-t border-surface/50">
                          <span className="text-[10px] font-bold text-muted uppercase tracking-wider">Graph RAG Activated - Tools Used:</span>
                          <div className="flex flex-wrap gap-2">
                            {msg.tool_calls.map((tc, idx) => (
                              <div key={idx} className="bg-background border border-surface rounded-md px-3 py-2 text-xs font-mono text-muted shadow-sm">
                                <span className="text-primary font-semibold">{tc.name}</span>
                                <span className="opacity-50 ml-1">({JSON.stringify(tc.args)})</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
                
                {loading && (
                   <motion.div 
                   initial={{ opacity: 0 }}
                   animate={{ opacity: 1 }}
                   className="flex gap-4 max-w-[85%]"
                 >
                   <div className="w-10 h-10 rounded-full bg-accent/20 text-accent flex items-center justify-center shrink-0 shadow-lg">
                     <Bot className="w-5 h-5 animate-pulse" />
                   </div>
                   <div className="p-4 rounded-2xl bg-surface border border-surface rounded-tl-none text-muted animate-pulse shadow-md">
                     Consulting the Graph & Vectors...
                   </div>
                 </motion.div>
                )}
              </div>

              {/* Input Form */}
              <div className="p-4 pb-8">
                <form onSubmit={handleSubmit} className="flex gap-2">
                  <input 
                    type="text" 
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    placeholder="Ask about papers, authors, methodologies..."
                    className="flex-1 bg-black/50 border border-white/20 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-pink-500/50 transition-all placeholder:text-white/50 shadow-inner"
                  />
                  <button 
                    type="submit" 
                    disabled={loading || !input.trim()}
                    className="bg-pink-600 hover:bg-pink-500 text-white p-3 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-pink-600/20"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </form>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center p-6 overflow-y-auto">
            <div className="w-full max-w-5xl space-y-8">
              
              {/* Analysis Search Bar */}
              <div className="flex flex-col items-center justify-center pt-8 pb-4 space-y-4">
                <div className="flex items-center gap-3 text-2xl font-bold text-white tracking-wide">
                  <Search className="w-8 h-8 text-cyan-400" />
                  Fuzzy Paper Lookup
                </div>
                <p className="text-white/50 text-sm max-w-md text-center">
                  Search for a paper by a fragment of its title (e.g. "unet", "residual net"). We will instantly resolve it, extract its methodologies, and find structurally similar papers.
                </p>
                <form onSubmit={handleAnalyze} className="w-full max-w-xl flex gap-2 mt-4 relative">
                  <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                    <Search className="w-4 h-4 text-white/40" />
                  </div>
                  <input 
                    type="text" 
                    value={analysisQuery}
                    onChange={e => setAnalysisQuery(e.target.value)}
                    placeholder="Type a fuzzy title..."
                    className="flex-1 bg-black/60 border border-cyan-500/30 rounded-full pl-11 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all placeholder:text-white/40 shadow-xl"
                  />
                  <button 
                    type="submit" 
                    disabled={analysisLoading || !analysisQuery.trim()}
                    className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 rounded-full font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-600/20 flex items-center gap-2"
                  >
                    {analysisLoading ? <Activity className="w-4 h-4 animate-spin" /> : "Analyze"}
                  </button>
                </form>
                {analysisError && <div className="text-rose-400 text-sm mt-2">{analysisError}</div>}
              </div>

              {/* Analysis Results Dashboard */}
              {analysisResult && (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >
                  {/* Title Card */}
                  <div className="bg-black/50 border border-white/10 rounded-2xl p-6 shadow-2xl backdrop-blur-sm">
                    <div className="flex items-start gap-4">
                      <div className="bg-cyan-500/20 p-3 rounded-xl border border-cyan-500/30">
                        <FileText className="w-6 h-6 text-cyan-400" />
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-white leading-snug">{analysisResult.target_paper?.title}</h2>
                        <div className="flex items-center gap-3 mt-2 text-sm text-white/60">
                          <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" /> ID: {analysisResult.target_paper?.paper_id}</span>
                          {analysisResult.target_paper?.year && (
                            <span className="flex items-center gap-1"><Activity className="w-3 h-3" /> Year: {analysisResult.target_paper?.year}</span>
                          )}
                          <span className="flex items-center gap-1 text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full border border-emerald-400/20">
                            Match Score: {analysisResult.target_paper?.score?.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Metadata Section */}
                    <div className="space-y-6">
                      <div className="bg-surface/50 border border-surface rounded-2xl p-5 shadow-lg">
                        <h3 className="text-sm font-bold text-muted uppercase tracking-widest flex items-center gap-2 mb-4">
                          <Users className="w-4 h-4" /> Extracted Authors
                        </h3>
                        <div className="flex flex-wrap gap-2">
                          {analysisResult.metadata?.authors?.length > 0 ? analysisResult.metadata.authors.map((a: string, i: number) => (
                            <span key={i} className="px-3 py-1.5 bg-black/40 border border-white/5 rounded-lg text-xs text-white/80">{a}</span>
                          )) : <span className="text-white/30 text-xs italic">None found</span>}
                        </div>
                      </div>
                      
                      <div className="bg-surface/50 border border-surface rounded-2xl p-5 shadow-lg">
                        <h3 className="text-sm font-bold text-muted uppercase tracking-widest flex items-center gap-2 mb-4">
                          <Tag className="w-4 h-4" /> Core Topics
                        </h3>
                        <div className="flex flex-wrap gap-2">
                          {analysisResult.metadata?.topics?.length > 0 ? analysisResult.metadata.topics.map((t: string, i: number) => (
                            <span key={i} className="px-3 py-1.5 bg-pink-500/10 border border-pink-500/20 text-pink-300 rounded-lg text-xs">{t}</span>
                          )) : <span className="text-white/30 text-xs italic">None found</span>}
                        </div>
                      </div>

                      <div className="bg-surface/50 border border-surface rounded-2xl p-5 shadow-lg">
                        <h3 className="text-sm font-bold text-muted uppercase tracking-widest flex items-center gap-2 mb-4">
                          <Layers className="w-4 h-4" /> GLiNER Methodologies
                        </h3>
                        <div className="flex flex-wrap gap-2">
                          {analysisResult.metadata?.methodologies?.length > 0 ? analysisResult.metadata.methodologies.map((m: string, i: number) => (
                            <span key={i} className="px-3 py-1.5 bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 rounded-lg text-xs">{m}</span>
                          )) : <span className="text-white/30 text-xs italic">None found</span>}
                        </div>
                      </div>
                    </div>

                    {/* Collaborative Filtering Section */}
                    <div className="bg-surface/50 border border-surface rounded-2xl p-5 shadow-lg flex flex-col">
                      <h3 className="text-sm font-bold text-muted uppercase tracking-widest flex items-center gap-2 mb-4">
                        <Network className="w-4 h-4" /> Similar Papers (Jaccard Match)
                      </h3>
                      <p className="text-xs text-white/40 mb-4">
                        Graph mathematically identified these papers based on structural overlap (shared methodologies, topics, and authors).
                      </p>
                      
                      <div className="space-y-3 flex-1">
                        {analysisResult.similar_papers?.length > 0 ? analysisResult.similar_papers.map((sp: any, i: number) => (
                          <div key={i} className="bg-black/40 border border-white/5 rounded-xl p-4 flex gap-4 items-center transition-all hover:bg-black/60 hover:border-white/10 group cursor-default">
                            <div className="w-10 h-10 rounded-full bg-surface flex items-center justify-center shrink-0 border border-white/5 font-bold text-muted group-hover:text-white transition-colors">
                              #{i + 1}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="text-sm font-medium text-white/90 truncate">{sp.title}</h4>
                              <div className="flex items-center gap-2 mt-1">
                                {sp.year && <span className="text-[10px] text-white/40">{sp.year}</span>}
                              </div>
                            </div>
                            <div className="flex flex-col items-end shrink-0">
                              <span className="text-xl font-bold text-cyan-400">{sp.shared_nodes}</span>
                              <span className="text-[9px] uppercase tracking-wider text-white/40">Shared Nodes</span>
                            </div>
                          </div>
                        )) : (
                          <div className="flex-1 flex items-center justify-center text-white/30 text-sm italic">
                            No highly similar papers found in the graph.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
