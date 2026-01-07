import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1'
});

export interface Incident {
  id: string;
  title: string;
  summary: string;
  severity: 'SEV1' | 'SEV2' | 'SEV3' | 'SEV4';
  status: 'OPEN' | 'INVESTIGATING' | 'MITIGATED' | 'RESOLVED';
  root_cause_analysis?: string;
  ai_summary?: string;
  ai_confidence?: number;
  resolution_eta?: string;
  remediation_steps?: string[];
  immediate_actions?: string[];
  prevention_measures?: string[];
  monitoring_recommendations?: string[];
  runbook_suggestions?: string[];
  similar_incidents?: string[];
  impact_assessment?: string;
  created_at: string;
  updated_at?: string;
  resolved_at?: string;
  service_id?: string;
  impact_scope?: string[];
  tags?: string[];
  source?: string;
}

export const getIncidents = async () => {
  const response = await api.get<Incident[]>('/incidents/');
  return response.data;
};

export const getIncident = async (id: string) => {
  const response = await api.get<Incident>(`/incidents/${id}`);
  return response.data;
};