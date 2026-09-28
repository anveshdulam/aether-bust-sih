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
          <XAxis type="number" hide />
          <YAxis 
            type="category" 
            dataKey="channel_code" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#9FB0C9', fontSize: 11 }}
            width={50}
          />
          <Tooltip 
            cursor={{ fill: '#1A2740' }}
            contentStyle={{ backgroundColor: '#121C2E', border: '1px solid #33507A', borderRadius: '2px' }}
            formatter={(value: number, _name: string, props: any) => [`${props.payload.sign}${value.toFixed(3)}`, props.payload.channel_name]}
          />
          <Bar dataKey="score" radius={[0, 2, 2, 0]}>
            {drivers.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.sign === '+' ? '#E4572E' : '#2F81F7'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
