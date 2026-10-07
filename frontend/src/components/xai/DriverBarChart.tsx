import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface DriverAttribution {
  channel_code: string;
  channel_name: string;
  score: number;
  sign: "+" | "-";
}

interface DriverBarChartProps {
  drivers: DriverAttribution[];
}

export const DriverBarChart: React.FC<DriverBarChartProps> = ({ drivers }) => {
  return (
    <div className="h-48 w-full mt-2">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={drivers} layout="vertical" margin={{ left: 20 }}>
          <XAxis type="number" stroke="#262f3b" tick={{ fill: '#9aa5b4', fontSize: 11 }} />
          <YAxis 
            type="category" 
            dataKey="channel_code" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#9aa5b4', fontSize: 11 }}
            width={50}
          />
          <Tooltip 
            cursor={{ fill: '#1b222c' }}
            contentStyle={{ backgroundColor: '#151b23', border: '1px solid #262f3b', borderRadius: '4px' }}
            formatter={(value: number, _name: string, props: any) => [`${props.payload.sign}${value.toFixed(3)}`, props.payload.channel_name]}
          />
          <Bar dataKey="score" radius={[0, 2, 2, 0]}>
            {drivers.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.sign === '+' ? '#ef4444' : '#38bdf8'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
