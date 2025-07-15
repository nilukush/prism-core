'use client'

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts'

const data = [
  {
    name: 'Mon',
    total: 145,
  },
  {
    name: 'Tue',
    total: 238,
  },
  {
    name: 'Wed',
    total: 187,
  },
  {
    name: 'Thu',
    total: 296,
  },
  {
    name: 'Fri',
    total: 341,
  },
  {
    name: 'Sat',
    total: 214,
  },
  {
    name: 'Sun',
    total: 176,
  },
]

export function Overview() {
  return (
    <ResponsiveContainer width="100%" height="350">
      <BarChart data={data}>
        <XAxis
          dataKey="name"
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `${value}`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--background))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '6px',
          }}
          labelStyle={{ color: 'hsl(var(--foreground))' }}
        />
        <Bar
          dataKey="total"
          fill="hsl(var(--primary))"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}