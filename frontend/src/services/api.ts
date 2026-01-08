import axios from 'axios';

// --- CONFIGURATION ---
// Determine the API URL based on the environment
// FIX: Prioritize the Azure URL in production, even if a local .env file exists
const isProd = import.meta.env.PROD;
const envUrl = import.meta.env.VITE_API_URL;
// If in PROD and envUrl is localhost, ignore it to prevent CORS errors
const safeUrl = (isProd && envUrl?.includes('localhost')) ? undefined : envUrl;

export const API_URL = safeUrl || (isProd ? 'https://nexus-backend.nicesea-d905a880.centralindia.azurecontainerapps.io' : 'http://localhost:8000');

// 1. Configure global axios defaults (for AuthContext and other direct usages)
axios.defaults.baseURL = API_URL;

// 2. Create specific instance for data services
const api = axios.create({
  baseURL: `${API_URL}/api/v1`
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