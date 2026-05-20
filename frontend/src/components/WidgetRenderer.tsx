"use client";

import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4"];

interface WidgetProps {
  widget: {
    id: string;
    widget_type: string;
    config: Record<string, any>;
  };
}

export default function WidgetRenderer({ widget }: WidgetProps) {
  switch (widget.widget_type) {
    case "line_chart":
      return <LineChartWidget config={widget.config} />;
    case "bar_chart":
      return <BarChartWidget config={widget.config} />;
    case "pie_chart":
      return <PieChartWidget config={widget.config} />;
    case "kpi_card":
      return <KpiWidget config={widget.config} />;
    case "table":
      return <TableWidget config={widget.config} />;
    default:
      return <p className="text-sm text-gray-400">Unknown widget type</p>;
  }
}

function LineChartWidget({ config }: { config: Record<string, any> }) {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics", "time-series", config],
    queryFn: () =>
      dashboardApi
        .timeSeries({
          event_name: config.event_name || "",
          interval: config.interval || "day",
        })
        .then((r) => r.data),
  });

  if (isLoading) return <Skeleton />;
  if (!data?.data?.length) return <Empty />;

  const formatted = data.data.map((d: any) => ({
    ...d,
    label: new Date(d.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={formatted}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function BarChartWidget({ config }: { config: Record<string, any> }) {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics", "top-events", config],
    queryFn: () =>
      dashboardApi.topEvents({ limit: String(config.limit || 7) }).then((r) => r.data),
  });

  if (isLoading) return <Skeleton />;
  if (!data?.data?.length) return <Empty />;

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data.data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="event_name" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function PieChartWidget({ config }: { config: Record<string, any> }) {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics", "top-events-pie", config],
    queryFn: () =>
      dashboardApi.topEvents({ limit: String(config.limit || 5) }).then((r) => r.data),
  });

  if (isLoading) return <Skeleton />;
  if (!data?.data?.length) return <Empty />;

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie data={data.data} dataKey="count" nameKey="event_name" cx="50%" cy="50%" outerRadius={80}>
          {data.data.map((_: any, i: number) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

function KpiWidget({ config }: { config: Record<string, any> }) {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics", "kpi", config],
    queryFn: () =>
      dashboardApi.kpi({ event_name: config.event_name || "" }).then((r) => r.data),
  });

  if (isLoading) return <Skeleton />;

  return (
    <div className="flex flex-col items-center justify-center py-4">
      <p className="text-4xl font-bold text-gray-900">
        {data?.total_events?.toLocaleString() || 0}
      </p>
      <p className="mt-1 text-sm text-gray-500">
        {config.event_name || "All Events"}
      </p>
    </div>
  );
}

function TableWidget({ config }: { config: Record<string, any> }) {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics", "top-events-table", config],
    queryFn: () =>
      dashboardApi.topEvents({ limit: String(config.limit || 10) }).then((r) => r.data),
  });

  if (isLoading) return <Skeleton />;
  if (!data?.data?.length) return <Empty />;

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-100">
          <th className="pb-2 text-left text-xs font-medium text-gray-500">Event</th>
          <th className="pb-2 text-right text-xs font-medium text-gray-500">Count</th>
        </tr>
      </thead>
      <tbody>
        {data.data.map((row: any, i: number) => (
          <tr key={i} className="border-b border-gray-50">
            <td className="py-2 text-gray-700">{row.event_name}</td>
            <td className="py-2 text-right text-gray-900 font-medium">{row.count.toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Skeleton() {
  return <div className="h-48 w-full animate-pulse rounded bg-gray-100" />;
}

function Empty() {
  return (
    <div className="flex h-48 items-center justify-center text-sm text-gray-400">
      No data available
    </div>
  );
}
