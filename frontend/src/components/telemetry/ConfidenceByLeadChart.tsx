import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useConsoleStore } from '../../store/useConsoleStore';

interface ConfidenceByLeadChartProps {
  data: { lead_time: number; confidence: number }[];
}

export const ConfidenceByLeadChart: React.FC<ConfidenceByLeadChartProps> = ({ data }) => {
  const { setLeadTime } = useConsoleStore();

  return (
    <div className="h-48 w-full mt-4">
      <div className="text-sm font-semibold text-text-primary mb-2">Confidence Horizon</div>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} onClick={(e) => e?.activeLabel && setLeadTime(Number(e.activeLabel))}>
          <CartesianGrid strokeDasharray="3 3" stroke="#233049" vertical={false} />
          <XAxis 
            dataKey="lead_time" 
            tick={{ fill: '#9FB0C9', fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: '#233049' }}
            tickFormatter={(val) => `D${val}`}
          />
          <YAxis 
            domain={[0, 100]} 
            tick={{ fill: '#9FB0C9', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            width={24}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1A2740', border: '1px solid #33507A', borderRadius: '4px' }}
            itemStyle={{ color: '#E6EDF7' }}
            labelStyle={{ color: '#9FB0C9' }}
            formatter={(value: number) => [`${value.toFixed(1)}%`, 'Confidence']}
            labelFormatter={(label) => `Day ${label}`}
          />
          <Line 
            type="monotone" 
            dataKey="confidence" 
            stroke="#2F81F7" 
            strokeWidth={2}
            dot={{ r: 3, fill: '#121C2E', stroke: '#2F81F7', strokeWidth: 2 }}
            activeDot={{ r: 5, fill: '#58A6FF', stroke: '#0B1220' }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
