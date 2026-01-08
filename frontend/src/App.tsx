import { useQuery } from '@tanstack/react-query';
import { getIncidents, type Incident } from './services/api';
import { AlertCircle, CheckCircle, Activity, Server, ShieldCheck, BarChart3 } from 'lucide-react';
import { useState } from 'react';
import { ActionPanel } from './components/ActionPanel';
import { MetricsGraph } from './components/MetricsGraph';
import { ChatPanel } from './components/ChatPanel';
import Dashboard from './components/Dashboard';
import { LoginForm } from './components/LoginForm';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import axios from 'axios';
interface Action {
  id: string;
  title: string;
  description: string;
  confidence: number;
}

// Fetch actions for a specific incident
const getActions = async (incidentId: string): Promise<Action[]> => {
  const res = await axios.get(`/api/v1/incidents/${incidentId}/actions`);
  return res.data;
};

function AppContent() {
  // Use 'user' to avoid unused variable warning if needed, or remove it
  const { isAuthenticated, loading } = useAuth(); 
  const [currentView, setCurrentView] = useState<'incidents' | 'dashboard'>('dashboard');
  
  const { data: incidents, isLoading, error } = useQuery({ 
    queryKey: ['incidents'], 
    queryFn: getIncidents,
    refetchInterval: 2000, 
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    retry: 3,
    enabled: isAuthenticated,
    staleTime: 0 
  });

  const [selectedId, setSelectedId] = useState<string | null>(null);
  
  // Fetch actions when an incident is selected
  const { data: actions } = useQuery({
    queryKey: ['actions', selectedId],
    queryFn: () => getActions(selectedId!),
    enabled: !!selectedId && isAuthenticated,
    refetchInterval: 2000,
    refetchIntervalInBackground: true,
    retry: 2,
    staleTime: 0
  });

  // Also refetch the selected incident details more frequently
  const { data: selectedIncidentDetails } = useQuery({
    queryKey: ['incident', selectedId],
    queryFn: () => axios.get(`/api/v1/incidents/${selectedId}`).then(res => res.data),
    enabled: !!selectedId && isAuthenticated,
    refetchInterval: 2000,
    refetchIntervalInBackground: true,
    retry: 2,
    staleTime: 0
  });

  const selectedIncident = selectedIncidentDetails || incidents?.find((i: Incident) => i.id === selectedId);

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center text-slate-500 bg-slate-950">
        Initializing NEXUS Console...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center text-red-400 bg-slate-950">
        <div className="text-center">
          <AlertCircle size={48} className="mx-auto mb-4" />
          <p>Failed to load NEXUS Console</p>
          <p className="text-sm text-slate-500 mt-2">Targeting Backend: {API_URL}</p>
        </div>
      </div>
    );
  }

  if (isLoading) return <div className="h-screen flex items-center justify-center text-slate-500 bg-slate-950">Initializing NEXUS Console...</div>;

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 p-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <Activity className="text-blue-500" size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">NEXUS</h1>
            <p className="text-xs text-slate-400">Autonomous Incident Response</p>
          </div>
        </div>
        <div className="flex gap-4 text-sm font-mono">
          <button
            onClick={() => setCurrentView('dashboard')}
            className={`px-3 py-1 rounded-full border transition-colors ${
              currentView === 'dashboard'
                ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:border-slate-600'
            }`}
          >
            <BarChart3 className="inline w-4 h-4 mr-1" />
            Dashboard
          </button>
          <button
            onClick={() => setCurrentView('incidents')}
            className={`px-3 py-1 rounded-full border transition-colors ${
              currentView === 'incidents'
                ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:border-slate-600'
            }`}
          >
            <Activity className="inline w-4 h-4 mr-1" />
            Incidents
          </button>
          <span className="flex items-center gap-2 px-3 py-1 bg-green-500/10 text-green-400 rounded-full border border-green-500/20">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            SYSTEM ONLINE
          </span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {currentView === 'dashboard' ? (
          <Dashboard />
        ) : (
          <div className="flex h-full">
            {/* Sidebar: Incident List */}
            <aside className="w-96 border-r border-slate-800 bg-slate-900/50 flex flex-col">
              <div className="p-4 border-b border-slate-800">
                <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Live Incidents</h2>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {incidents?.sort((a: Incident, b: Incident) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).map((inc: Incident) => (
                  <div 
                    key={inc.id}
                    onClick={() => setSelectedId(inc.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all hover:scale-[1.02] ${
                      selectedId === inc.id 
                        ? 'bg-blue-600/10 border-blue-500 shadow-lg shadow-blue-900/20' 
                        : 'bg-slate-800/40 border-slate-800 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <span className={`px-2 py-1 text-[10px] font-bold rounded border ${
                        inc.severity === 'SEV1' 
                          ? 'bg-red-500/10 text-red-400 border-red-500/20' 
                          : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                      }`}>
                        {inc.severity}
                      </span>
                      <span className="text-xs text-slate-500 font-mono">
                        {new Date(inc.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <h3 className="font-semibold text-slate-200 text-sm leading-snug">{inc.title}</h3>
                    <p className="text-xs text-slate-400 mt-2 line-clamp-2">{inc.summary}</p>
                  </div>
                ))}
                {incidents?.length === 0 && (
                  <div className="text-center p-8 text-slate-600 text-sm italic">
                    No active incidents. System nominal.
                  </div>
                )}
              </div>
            </aside>

            {/* Main Panel: Detail View */}
            <section className="flex-1 overflow-y-auto bg-slate-950 p-8">
              {selectedIncident ? (
                <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  
                  {/* Header Card */}
                  <div className="flex justify-between items-start border-b border-slate-800 pb-6">
                    <div>
                      <h1 className="text-3xl font-bold text-white mb-2">{selectedIncident.title}</h1>
                      <div className="flex items-center gap-4 text-slate-400 text-sm">
                        <span className="flex items-center gap-1"><Server size={14}/> {selectedIncident.service_id}</span>
                        <span className="text-slate-600">|</span>
                        <span>ID: <span className="font-mono text-slate-500">{selectedIncident.id.split('-')[0]}...</span></span>
                      </div>
                    </div>
                    {selectedIncident.status === 'OPEN' ? (
                      <div className="flex items-center gap-2 text-red-400 bg-red-950/30 px-4 py-1.5 rounded-full border border-red-900/50 shadow-red-900/20 shadow-lg">
                        <AlertCircle size={18} /> <span className="font-semibold">Active Incident</span>
                      </div>
                    ) : selectedIncident.status === 'INVESTIGATING' ? (
                      <div className="flex items-center gap-2 text-blue-400 bg-blue-950/30 px-4 py-1.5 rounded-full border border-blue-900/50 shadow-blue-900/20 shadow-lg">
                        <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                        <span className="font-semibold">Investigating</span>
                      </div>
                    ) : selectedIncident.status === 'RESOLVED' ? (
                      <div className="flex items-center gap-2 text-green-400 bg-green-950/30 px-4 py-1.5 rounded-full border border-green-900/50">
                        <CheckCircle size={18} /> <span className="font-semibold">Resolved</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-yellow-400 bg-yellow-950/30 px-4 py-1.5 rounded-full border border-yellow-900/50">
                        <AlertCircle size={18} /> <span className="font-semibold">{selectedIncident.status}</span>
                      </div>
                    )}
                  </div>

                  {/* AI Analysis Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    
                    {/* Left Col: RCA */}
                    <div className="lg:col-span-2 space-y-6">
                      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                          <ShieldCheck size={100} />
                        </div>
                        <h3 className="text-lg font-semibold text-purple-200 mb-4 flex items-center gap-2">
                          <div className="w-2 h-2 bg-purple-500 rounded-full shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
                          Root Cause Analysis
                        </h3>
                        
                        {selectedIncident.ai_summary || selectedIncident.root_cause_analysis ? (
                          <div className="space-y-4">
                            <div className="bg-slate-950/50 p-4 rounded-lg border border-slate-800/50">
                              <h4 className="text-sm font-semibold text-slate-300 mb-2">Root Cause</h4>
                              <p className="text-slate-300 leading-relaxed text-sm">
                                {selectedIncident.ai_summary || selectedIncident.root_cause_analysis}
                              </p>
                            </div>
                            
                            {selectedIncident.immediate_actions && selectedIncident.immediate_actions.length > 0 && (
                              <div className="bg-slate-950/50 p-4 rounded-lg border border-slate-800/50">
                                <h4 className="text-sm font-semibold text-orange-400 mb-2">Immediate Actions</h4>
                                <ul className="space-y-1">
                                  {selectedIncident.immediate_actions.map((action: string, idx: number) => (
                                    <li key={idx} className="text-slate-300 text-sm flex items-start gap-2">
                                      <span className="text-orange-400 mt-1">•</span>
                                      <span>{action}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {selectedIncident.ai_confidence && (
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-slate-500">AI Confidence</span>
                                <span className="text-green-400 font-semibold">
                                  {Math.round(selectedIncident.ai_confidence * 100)}%
                                </span>
                              </div>
                            )}
                            
                            {selectedIncident.resolution_eta && (
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-slate-500">Estimated Resolution</span>
                                <span className="text-blue-400 font-semibold">{selectedIncident.resolution_eta}</span>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="flex flex-col items-center justify-center py-10 gap-3 text-slate-500">
                            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                            <p className="text-sm font-mono animate-pulse">Running diagnostics...</p>
                          </div>
                        )}
                      </div>

                      {/* REMEDIATION ACTIONS */}
                      <ActionPanel 
                        incidentId={selectedIncident.id} 
                        suggestedActions={actions || []} 
                        remediationSteps={selectedIncident.remediation_steps}
                      />
                    </div>

                    {/* Right Col: Metadata & Metrics */}
                    <div className="space-y-6">

                       {/* New Metrics Graph */}
                       <MetricsGraph />

                       <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-5">
                          <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">Impact Scope</h4>
                          <div className="flex flex-wrap gap-2">
                            {selectedIncident.impact_scope?.map((scope: string) => (
                              <span key={scope} className="px-2 py-1 bg-slate-800 text-slate-300 text-xs rounded border border-slate-700">
                                {scope}
                              </span>
                            ))}
                            {!selectedIncident.impact_scope?.length && <span className="text-slate-600 text-sm">-</span>}
                          </div>
                       </div>
                    </div>

                  </div>

                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-600">
                  <div className="p-6 bg-slate-900/50 rounded-full mb-6">
                    <Activity size={48} className="opacity-20" />
                  </div>
                  <p className="text-lg font-medium text-slate-500">Select an incident to begin response</p>
                </div>
              )}
            </section>
          </div>
        )}
      </main>

      {/* Chat Panel */}
      {selectedIncident && currentView === 'incidents' && <ChatPanel incidentId={selectedIncident.id} />}

    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;