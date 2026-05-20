"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import toast from "react-hot-toast";
import { ArrowLeft, Plus, Share2, Trash2 } from "lucide-react";
import WidgetRenderer from "@/components/WidgetRenderer";
import AddWidgetModal from "@/components/AddWidgetModal";

export default function DashboardDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [showAddWidget, setShowAddWidget] = useState(false);

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["dashboard", id],
    queryFn: () => dashboardApi.get(id).then((r) => r.data),
    enabled: !!id,
  });

  const deleteMutation = useMutation({
    mutationFn: () => dashboardApi.delete(id),
    onSuccess: () => {
      toast.success("Dashboard deleted");
      router.push("/dashboard");
    },
  });

  const togglePublicMutation = useMutation({
    mutationFn: () => dashboardApi.togglePublic(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", id] });
      toast.success("Sharing updated");
    },
  });

  const deleteWidgetMutation = useMutation({
    mutationFn: (widgetId: string) => dashboardApi.deleteWidget(id, widgetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", id] });
      toast.success("Widget removed");
    },
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-6" />
        <div className="grid grid-cols-12 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="col-span-6 h-64 bg-white rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="p-6">
        <p className="text-gray-500">Dashboard not found</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/dashboard")} className="rounded-lg p-2 hover:bg-gray-100">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{dashboard.name}</h1>
            {dashboard.description && (
              <p className="text-sm text-gray-500">{dashboard.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddWidget(true)}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            Add Widget
          </button>
          <button
            onClick={() => togglePublicMutation.mutate()}
            className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-sm ${
              dashboard.is_public
                ? "border-green-300 bg-green-50 text-green-700"
                : "border-gray-300 text-gray-600 hover:bg-gray-50"
            }`}
          >
            <Share2 className="h-4 w-4" />
            {dashboard.is_public ? "Public" : "Private"}
          </button>
          <button
            onClick={() => {
              if (confirm("Delete this dashboard?")) deleteMutation.mutate();
            }}
            className="rounded-lg border border-red-300 p-2 text-red-600 hover:bg-red-50"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {dashboard.is_public && dashboard.share_token && (
        <div className="mb-4 rounded-lg bg-blue-50 p-3 text-sm text-blue-700">
          Public link:{" "}
          <code className="rounded bg-blue-100 px-2 py-0.5 text-xs">
            {window.location.origin}/public/{dashboard.share_token}
          </code>
        </div>
      )}

      {/* Widgets Grid */}
      {dashboard.widgets?.length === 0 ? (
        <div className="rounded-lg bg-white p-12 text-center shadow-sm">
          <p className="text-gray-500">No widgets yet. Add your first widget!</p>
        </div>
      ) : (
        <div className="grid grid-cols-12 gap-4">
          {dashboard.widgets?.map((widget: any) => (
            <div
              key={widget.id}
              className="rounded-lg bg-white shadow-sm"
              style={{
                gridColumn: `span ${widget.position?.w || 6}`,
              }}
            >
              <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
                <h3 className="text-sm font-medium text-gray-700">{widget.name}</h3>
                <button
                  onClick={() => deleteWidgetMutation.mutate(widget.id)}
                  className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-500"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
              <div className="p-4">
                <WidgetRenderer widget={widget} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Widget Modal */}
      {showAddWidget && (
        <AddWidgetModal
          dashboardId={id}
          onClose={() => setShowAddWidget(false)}
          onCreated={() => {
            queryClient.invalidateQueries({ queryKey: ["dashboard", id] });
            setShowAddWidget(false);
          }}
        />
      )}
    </div>
  );
}
