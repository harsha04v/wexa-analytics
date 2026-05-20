"use client";

import { useState } from "react";
import { dashboardApi } from "@/lib/api";
import toast from "react-hot-toast";
import { X } from "lucide-react";

const WIDGET_TYPES = [
  { value: "line_chart", label: "Line Chart", defaultConfig: { interval: "day" } },
  { value: "bar_chart", label: "Bar Chart", defaultConfig: { limit: 7 } },
  { value: "pie_chart", label: "Pie Chart", defaultConfig: { limit: 5 } },
  { value: "kpi_card", label: "KPI Card", defaultConfig: {} },
  { value: "table", label: "Table", defaultConfig: { limit: 10 } },
];

interface Props {
  dashboardId: string;
  onClose: () => void;
  onCreated: () => void;
}

export default function AddWidgetModal({ dashboardId, onClose, onCreated }: Props) {
  const [name, setName] = useState("");
  const [type, setType] = useState("line_chart");
  const [eventName, setEventName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const widgetDef = WIDGET_TYPES.find((w) => w.value === type)!;
      const config = {
        ...widgetDef.defaultConfig,
        ...(eventName ? { event_name: eventName } : {}),
      };
      await dashboardApi.createWidget(dashboardId, {
        name,
        widget_type: type,
        config,
        position: { x: 0, y: 0, w: type === "kpi_card" ? 3 : 6, h: type === "kpi_card" ? 2 : 4 },
      });
      toast.success("Widget added");
      onCreated();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to add widget");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Add Widget</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Widget Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="e.g. Events Over Time"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Widget Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              {WIDGET_TYPES.map((w) => (
                <option key={w.value} value={w.value}>
                  {w.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Event Name <span className="text-gray-400">(optional, filters data)</span>
            </label>
            <input
              type="text"
              value={eventName}
              onChange={(e) => setEventName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="e.g. page_view, signup"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Adding..." : "Add Widget"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
