import { useState } from 'react';
import { Play, CheckCircle, XCircle, Loader2, ShieldAlert } from 'lucide-react';
import axios from 'axios';

interface ActionPanelProps {
  incidentId: string;
  suggestedActions: any[];
  remediationSteps?: string[];
}

export function ActionPanel({ incidentId, suggestedActions, remediationSteps }: ActionPanelProps) {
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());

  const handleExecute = async (actionId: string) => {
    try {
      setExecutingId(actionId);
      // For demo purposes, just simulate execution
      console.log(`Executing action: ${actionId}`);
      
      // Simulate execution time
      setTimeout(() => {
        setExecutingId(null);
        setCompletedIds(prev => new Set(prev).add(actionId));
      }, 2000);
      
    } catch (error) {
      console.error("Execution failed", error);
      setExecutingId(null);
    }
  };

  // Use remediation steps from RCA if available
  const actions = remediationSteps && remediationSteps.length > 0
    ? remediationSteps.map((step, idx) => ({ id: `step-${idx}`, title: step, description: "AI-recommended remediation" }))
    : suggestedActions;

  // If no AI actions yet
  if (!actions || actions.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mt-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-2">Remediation Plan</h3>
        <p className="text-slate-500 text-sm">Waiting for RCA to generate options...</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mt-6">
      <div className="flex items-center gap-2 mb-4">
        <ShieldAlert className="text-blue-400" />
        <h3 className="text-lg font-semibold text-blue-100">Recommended Actions</h3>
      </div>

      <div className="space-y-3">
        {actions.map((action, idx) => {
          const isExecuting = executingId === action.id;
          const isDone = completedIds.has(action.id);

          return (
            <div key={idx} className="bg-slate-950 border border-slate-800 rounded-lg p-4 flex justify-between items-center group hover:border-blue-500/50 transition-colors">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-200">{action.title || "Restart Service Node"}</span>
                  <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded">High Confidence</span>
                </div>
                <p className="text-sm text-slate-500 mt-1">{action.description || "Safely drains connections and restarts the pod."}</p>
              </div>

              {isDone ? (
                <div className="flex items-center gap-2 text-green-500 bg-green-950/20 px-4 py-2 rounded-lg border border-green-900">
                  <CheckCircle size={18} />
                  <span className="text-sm font-medium">Executed</span>
                </div>
              ) : (
                <button
                  onClick={() => handleExecute(action.id || "mock-id")}
                  disabled={isExecuting}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    isExecuting 
                      ? 'bg-blue-900/50 text-blue-300 cursor-not-allowed' 
                      : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20'
                  }`}
                >
                  {isExecuting ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play size={18} fill="currentColor" />
                      Execute
                    </>
                  )}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
