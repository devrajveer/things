"use client";

import React, { useState, useEffect } from "react";
import { Activity, Clock, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";

interface WidgetProps {
  projectId: string;
  streamId: string;
  title: string;
  unit?: string;
}

export function ValueWidget({ projectId, streamId, title, unit }: WidgetProps) {
  const [value, setValue] = useState<any>(null);
  const [time, setTime] = useState<string | null>(null);

  useEffect(() => {
    // Initial fetch from stream table
    const fetchLast = async () => {
      try {
        const streams = await api.get(`/v1/projects/${projectId}/streams`);
        const s = streams.data.find((x: any) => x.id === streamId);
        if (s) {
          setValue(s.last_value);
          setTime(s.last_value_at);
        }
      } catch (err) {}
    };
    fetchLast();

    // Listen for real-time updates
    const eventSource = new EventSource(`http://localhost:3001/v1/realtime/projects/${projectId}`);
    eventSource.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.data.stream_id === streamId) {
        const dp = payload.data;
        setValue(dp.value_num ?? dp.value_bool ?? dp.value_str ?? dp.value_json);
        setTime(dp.ts);
      }
    };
    return () => eventSource.close();
  }, [projectId, streamId]);

  return (
    <div className="h-full flex flex-col justify-between">
      <div className="flex items-center justify-between text-muted-foreground">
        <span className="text-xs font-bold uppercase tracking-wider">{title}</span>
        <Activity className="w-4 h-4" />
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-4xl font-bold tracking-tight">
          {typeof value === 'number' ? value.toFixed(2) : (value ?? "--")}
        </span>
        <span className="text-lg text-muted-foreground font-medium">{unit}</span>
      </div>
      <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
        <Clock className="w-3 h-3" />
        {time ? new Date(time).toLocaleTimeString() : "No data"}
      </div>
    </div>
  );
}

export function ChartWidget({ projectId, streamId, title, unit }: WidgetProps) {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await api.get(`/v1/projects/${projectId}/analytics/history?stream_id=${streamId}&interval=1 minute`);
        setData(res.data.map((d: any) => ({
          time: new Date(d.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          val: d.avg
        })));
      } catch (err) {}
    };
    fetchHistory();
  }, [projectId, streamId]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">{title}</span>
        <div className="px-2 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-bold">LIVE</div>
      </div>
      <div className="flex-1 min-h-0 -ml-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
            <XAxis 
              dataKey="time" 
              axisLine={false} 
              tickLine={false} 
              tick={{fill: '#888', fontSize: 10}}
              minTickGap={30}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{fill: '#888', fontSize: 10}}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
              itemStyle={{ color: '#3b82f6' }}
            />
            <Area 
              type="monotone" 
              dataKey="val" 
              stroke="#3b82f6" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorVal)" 
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
