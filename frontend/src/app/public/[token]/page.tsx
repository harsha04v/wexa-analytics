"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { dashboardApi } from "@/lib/api";
import WidgetRenderer from "@/components/WidgetRenderer";

export default function PublicDashboardPage() {
  const { token } = useParams<{ token: string }>();

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["public-dashboard", token],
    queryFn: () => dashboardApi.getPublic(token).then((r) => r.data),
    enabled: !!token,
  });

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Dashboard not found or not public</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">{dashboard.name}</h1>
          {dashboard.description && (
            <p className="mt-1 text-sm text-gray-500">{dashboard.description}</p>
          )}
          <p className="mt-2 text-xs text-gray-400">Public dashboard · Read only</p>
        </div>

        <div className="grid grid-cols-12 gap-4">
          {dashboard.widgets?.map((widget: any) => (
            <div
              key={widget.id}
              className="rounded-lg bg-white shadow-sm"
              style={{ gridColumn: `span ${widget.position?.w || 6}` }}
            >
              <div className="border-b border-gray-100 px-4 py-3">
                <h3 className="text-sm font-medium text-gray-700">{widget.name}</h3>
              </div>
              <div className="p-4">
                <WidgetRenderer widget={widget} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
