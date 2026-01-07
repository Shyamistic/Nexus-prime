import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const data = [
  { time: '09:20', latency: 120 },
  { time: '09:21', latency: 132 },
  { time: '09:22', latency: 145 },
  { time: '09:23', latency: 130 },
  { time: '09:24', latency: 2800 }, // The Spike
  { time: '09:25', latency: 3200 },
  { time: '09:26', latency: 3100 },
  { time: '09:27', latency: 3400 },
  { time: '09:28', latency: 3050 },
  { time: '09:29', latency: 2900 },
];

export function MetricsGraph() {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
      <h3 className="text-xs font-bold text-slate-500 uppercase mb-4">Live Latency (ms) - checkout-service-v2</h3>
      <div style={{ width: '100%', height: '280px', minHeight: '280px' }}>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="time" stroke="#475569" fontSize={12} />
            <YAxis stroke="#475569" fontSize={12} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }}
              itemStyle={{ color: '#f8fafc' }}
            />
            <ReferenceLine y={2000} label="SLO Limit" stroke="red" strokeDasharray="3 3" />
            <Line 
              type="monotone" 
              dataKey="latency" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={{ fill: '#3b82f6' }} 
              activeDot={{ r: 8 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}