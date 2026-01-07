import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Brain, 
  Zap, 
  Shield, 
  Clock, 
  TrendingUp, 
  Users, 
  Bell, 
  Settings, 
  Download, 
  Filter,
  Search,
  Calendar,
  BarChart3,
  PieChart,
  LineChart,
  Globe,
  Smartphone,
  Headphones,
  FileText,
  Database,
  Cpu,
  HardDrive,
  Network,
  Eye,
  Target,
  Workflow
} from 'lucide-react';

interface EnterpriseFeature {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  status: 'active' | 'beta' | 'coming_soon';
  category: 'ai' | 'automation' | 'analytics' | 'integration' | 'security';
  metrics?: {
    usage: number;
    performance: number;
    satisfaction: number;
  };
}

const enterpriseFeatures: EnterpriseFeature[] = [
  {
    id: 'ai-rca',
    name: 'AI Root Cause Analysis',
    description: '6-second AI-powered incident analysis with 94% accuracy',
    icon: <Brain className="h-5 w-5" />,
    status: 'active',
    category: 'ai',
    metrics: { usage: 100, performance: 94, satisfaction: 96 }
  },
  {
    id: 'auto-remediation',
    name: 'Autonomous Remediation',
    description: 'Automated incident resolution with approval workflows',
    icon: <Zap className="h-5 w-5" />,
    status: 'active',
    category: 'automation',
    metrics: { usage: 87, performance: 91, satisfaction: 93 }
  },
  {
    id: 'predictive-analytics',
    name: 'Predictive Analytics',
    description: 'ML-powered incident prediction and prevention',
    icon: <TrendingUp className="h-5 w-5" />,
    status: 'active',
    category: 'analytics',
    metrics: { usage: 76, performance: 88, satisfaction: 89 }
  },
  {
    id: 'real-time-collab',
    name: 'Real-time Collaboration',
    description: 'Live incident war rooms with video conferencing',
    icon: <Users className="h-5 w-5" />,
    status: 'active',
    category: 'integration',
    metrics: { usage: 82, performance: 95, satisfaction: 97 }
  },
  {
    id: 'smart-notifications',
    name: 'Smart Notifications',
    description: 'AI-driven notification routing and escalation',
    icon: <Bell className="h-5 w-5" />,
    status: 'active',
    category: 'automation',
    metrics: { usage: 95, performance: 92, satisfaction: 94 }
  },
  {
    id: 'security-scanner',
    name: 'Security Vulnerability Scanner',
    description: 'Automated security incident detection and response',
    icon: <Shield className="h-5 w-5" />,
    status: 'active',
    category: 'security',
    metrics: { usage: 89, performance: 96, satisfaction: 95 }
  },
  {
    id: 'performance-monitoring',
    name: 'Performance Monitoring',
    description: 'Real-time system performance and health tracking',
    icon: <Cpu className="h-5 w-5" />,
    status: 'active',
    category: 'analytics',
    metrics: { usage: 91, performance: 93, satisfaction: 92 }
  },
  {
    id: 'mobile-app',
    name: 'Mobile Response App',
    description: 'iOS/Android app for on-the-go incident management',
    icon: <Smartphone className="h-5 w-5" />,
    status: 'active',
    category: 'integration',
    metrics: { usage: 67, performance: 85, satisfaction: 88 }
  },
  {
    id: 'voice-assistant',
    name: 'Voice Assistant Integration',
    description: 'Voice-activated incident reporting and status updates',
    icon: <Headphones className="h-5 w-5" />,
    status: 'beta',
    category: 'ai',
    metrics: { usage: 23, performance: 78, satisfaction: 82 }
  },
  {
    id: 'advanced-analytics',
    name: 'Advanced Analytics Suite',
    description: 'Custom dashboards, reports, and business intelligence',
    icon: <BarChart3 className="h-5 w-5" />,
    status: 'active',
    category: 'analytics',
    metrics: { usage: 78, performance: 89, satisfaction: 91 }
  },
  {
    id: 'global-deployment',
    name: 'Global Multi-Region Deployment',
    description: 'Worldwide incident response with regional failover',
    icon: <Globe className="h-5 w-5" />,
    status: 'active',
    category: 'integration',
    metrics: { usage: 85, performance: 97, satisfaction: 96 }
  },
  {
    id: 'compliance-reporting',
    name: 'Compliance & Audit Reporting',
    description: 'SOC 2, GDPR, HIPAA compliance with automated reports',
    icon: <FileText className="h-5 w-5" />,
    status: 'active',
    category: 'security',
    metrics: { usage: 73, performance: 94, satisfaction: 93 }
  }
];

const EnterpriseFeatures: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'usage' | 'performance'>('usage');

  const categories = [
    { id: 'all', name: 'All Features', count: enterpriseFeatures.length },
    { id: 'ai', name: 'AI & ML', count: enterpriseFeatures.filter(f => f.category === 'ai').length },
    { id: 'automation', name: 'Automation', count: enterpriseFeatures.filter(f => f.category === 'automation').length },
    { id: 'analytics', name: 'Analytics', count: enterpriseFeatures.filter(f => f.category === 'analytics').length },
    { id: 'integration', name: 'Integration', count: enterpriseFeatures.filter(f => f.category === 'integration').length },
    { id: 'security', name: 'Security', count: enterpriseFeatures.filter(f => f.category === 'security').length }
  ];

  const filteredFeatures = enterpriseFeatures
    .filter(feature => 
      (selectedCategory === 'all' || feature.category === selectedCategory) &&
      (searchTerm === '' || feature.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
       feature.description.toLowerCase().includes(searchTerm.toLowerCase()))
    )
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'usage') return (b.metrics?.usage || 0) - (a.metrics?.usage || 0);
      if (sortBy === 'performance') return (b.metrics?.performance || 0) - (a.metrics?.performance || 0);
      return 0;
    });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'beta': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'coming_soon': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'ai': return 'bg-purple-500/20 text-purple-400';
      case 'automation': return 'bg-green-500/20 text-green-400';
      case 'analytics': return 'bg-blue-500/20 text-blue-400';
      case 'integration': return 'bg-orange-500/20 text-orange-400';
      case 'security': return 'bg-red-500/20 text-red-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-card p-6 rounded-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Enterprise Features</h2>
            <p className="text-slate-300">Advanced capabilities powering autonomous incident response</p>
          </div>
          <div className="flex items-center space-x-3">
            <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
              {enterpriseFeatures.filter(f => f.status === 'active').length} Active
            </Badge>
            <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
              {enterpriseFeatures.filter(f => f.status === 'beta').length} Beta
            </Badge>
            <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
              {enterpriseFeatures.filter(f => f.status === 'coming_soon').length} Coming Soon
            </Badge>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Search className="h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search features..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="glass px-3 py-2 rounded-lg text-white placeholder-slate-400 border-white/20 focus:border-white/40"
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="glass px-3 py-2 rounded-lg text-white border-white/20 focus:border-white/40"
            >
              <option value="usage">Sort by Usage</option>
              <option value="performance">Sort by Performance</option>
              <option value="name">Sort by Name</option>
            </select>
          </div>
        </div>
      </div>

      {/* Category Filters */}
      <div className="flex flex-wrap gap-3">
        {categories.map(category => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`glass-card px-4 py-2 rounded-lg border transition-all ${
              selectedCategory === category.id 
                ? 'border-blue-400/50 bg-blue-500/20' 
                : 'border-white/20 hover:border-white/30'
            }`}
          >
            <span className="text-white font-medium">{category.name}</span>
            <Badge className="ml-2 bg-white/20 text-white">{category.count}</Badge>
          </button>
        ))}
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredFeatures.map(feature => (
          <Card key={feature.id} className="glass-card border-white/10 hover:border-white/20 transition-all">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 glass rounded-lg">
                    {feature.icon}
                  </div>
                  <div>
                    <CardTitle className="text-white text-lg">{feature.name}</CardTitle>
                    <Badge className={`mt-1 ${getCategoryColor(feature.category)}`}>
                      {feature.category.toUpperCase()}
                    </Badge>
                  </div>
                </div>
                <Badge className={getStatusColor(feature.status)}>
                  {feature.status.replace('_', ' ').toUpperCase()}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300 text-sm mb-4">{feature.description}</p>
              
              {feature.metrics && feature.status === 'active' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">Usage Rate</span>
                    <span className="text-white font-medium">{feature.metrics.usage}%</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all"
                      style={{ width: `${feature.metrics.usage}%` }}
                    ></div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mt-3">
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-400">{feature.metrics.performance}%</div>
                      <div className="text-xs text-slate-400">Performance</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-400">{feature.metrics.satisfaction}%</div>
                      <div className="text-xs text-slate-400">Satisfaction</div>
                    </div>
                  </div>
                </div>
              )}
              
              {feature.status === 'beta' && (
                <div className="glass p-3 rounded-lg mt-3">
                  <p className="text-xs text-yellow-400">
                    🧪 Beta Feature - Available for testing with limited functionality
                  </p>
                </div>
              )}
              
              {feature.status === 'coming_soon' && (
                <div className="glass p-3 rounded-lg mt-3">
                  <p className="text-xs text-blue-400">
                    🚀 Coming Soon - Expected in next major release
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Feature Summary */}
      <Card className="glass-card border-white/10">
        <CardHeader>
          <CardTitle className="text-white flex items-center">
            <TrendingUp className="h-5 w-5 mr-2 text-green-400" />
            Platform Performance Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-400">94.2%</div>
              <div className="text-sm text-slate-400">Average Performance</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">87.3%</div>
              <div className="text-sm text-slate-400">Feature Adoption</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-400">92.8%</div>
              <div className="text-sm text-slate-400">User Satisfaction</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-400">99.97%</div>
              <div className="text-sm text-slate-400">Platform Uptime</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EnterpriseFeatures;