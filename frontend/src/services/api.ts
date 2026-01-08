/// <reference types="vite/client" />
import axios from 'axios';

// Determine API URL - Azure in production, localhost in dev
const isProd = import.meta.env.PROD;

// HARDCODE Azure URL for production to ensure it's always used
let API_URL: string;

if (isProd) {
  // Production: always use Azure backend
  API_URL = 'https://nexus-backend.nicesea-d905a880.centralindia.azurecontainerapps.io';
  console.log('🌐 PRODUCTION: Using Azure backend:', API_URL);
} else {
  // Development: use localhost
  API_URL = 'http://127.0.0.1:8000';
  console.log('🔧 DEVELOPMENT: Using local backend:', API_URL);
}

// Configure global axios defaults
axios.defaults.baseURL = API_URL;

// Create API instance with /api/v1 prefix
const api = axios.create({
  baseURL: `${API_URL}/api/v1`
});

// Add request interceptor to include token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export { API_URL, api as default };

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
