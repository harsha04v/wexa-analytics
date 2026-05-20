"use client";

import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import Link from "next/link";
import { Plus } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";

export default function DashboardListPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["dashboards"],
    queryFn: () => dashboardApi.list().then((r) => r.data),
  });

  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await dashboardApi.create({ name });
      setName("");
      setCreating(false);
      refetch();
      toast.success("Dashboard created");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to create dashboard");
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboards</h1>
        <button
          onClick={() => setCreating(!creating)}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          New Dashboard
        </button>
      </div>

      {creating && (
        <form onSubmit={handleCreate} className="mb-6 flex gap-3 rounded-lg bg-white p-4 shadow-sm">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Dashboard name"
            required
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
          <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
            Create
          </button>
          <button type="button" onClick={() => setCreating(false)} className="rounded-lg border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">
            Cancel
          </button>
        </form>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 rounded-lg bg-white shadow-sm animate-pulse" />
          ))}
        </div>
      ) : data?.length === 0 ? (
        <div className="rounded-lg bg-white p-12 text-center shadow-sm">
          <p className="text-gray-500">No dashboards yet. Create your first one!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.map((d: any) => (
            <Link
              key={d.id}
              href={`/dashboard/${d.id}`}
              className="rounded-lg bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="text-lg font-semibold text-gray-900">{d.name}</h3>
              <p className="mt-1 text-sm text-gray-500">{d.description || "No description"}</p>
              <div className="mt-4 flex items-center gap-4 text-xs text-gray-400">
                <span>{d.widget_count} widgets</span>
                {d.is_public && (
                  <span className="rounded bg-green-100 px-2 py-0.5 text-green-700">Public</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
