"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ingestionApi } from "@/lib/api";
import { useState, useRef } from "react";
import toast from "react-hot-toast";
import { Upload, Key, Plus, Trash2, Copy } from "lucide-react";

export default function IngestionPage() {
  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Data Ingestion</h1>
      <ApiKeysSection />
      <CsvUploadSection />
      <JobsSection />
    </div>
  );
}

function ApiKeysSection() {
  const queryClient = useQueryClient();
  const { data: keys, isLoading } = useQuery({
    queryKey: ["api-keys"],
    queryFn: () => ingestionApi.listApiKeys().then((r) => r.data),
  });

  const [name, setName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () => ingestionApi.createApiKey({ name }),
    onSuccess: (res) => {
      setNewKey(res.data.raw_key);
      setName("");
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("API key created");
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (id: string) => ingestionApi.revokeApiKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("API key revoked");
    },
  });

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <Key className="h-5 w-5" />
        API Keys
      </h2>
      <p className="mt-1 text-sm text-gray-500">Manage API keys for event ingestion</p>

      {newKey && (
        <div className="mt-4 rounded-lg bg-green-50 border border-green-200 p-4">
          <p className="text-sm font-medium text-green-800">New API Key (copy now — shown only once):</p>
          <div className="mt-2 flex items-center gap-2">
            <code className="flex-1 rounded bg-green-100 px-3 py-2 text-xs font-mono break-all">{newKey}</code>
            <button
              onClick={() => {
                navigator.clipboard.writeText(newKey);
                toast.success("Copied!");
              }}
              className="rounded p-2 text-green-700 hover:bg-green-100"
            >
              <Copy className="h-4 w-4" />
            </button>
          </div>
          <button onClick={() => setNewKey(null)} className="mt-2 text-xs text-green-600 hover:underline">
            Dismiss
          </button>
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          createMutation.mutate();
        }}
        className="mt-4 flex gap-3"
      >
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Key name (e.g. Production)"
          required
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
        >
          <Plus className="h-4 w-4" />
          Create
        </button>
      </form>

      <div className="mt-4 space-y-2">
        {isLoading ? (
          <div className="h-10 animate-pulse rounded bg-gray-100" />
        ) : keys?.length === 0 ? (
          <p className="text-sm text-gray-400">No API keys yet</p>
        ) : (
          keys?.map((key: any) => (
            <div key={key.id} className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3">
              <div>
                <p className="text-sm font-medium text-gray-900">{key.name}</p>
                <p className="text-xs text-gray-400">
                  Prefix: {key.key_prefix}... · Created: {new Date(key.created_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => revokeMutation.mutate(key.id)}
                className="rounded p-1.5 text-red-500 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function CsvUploadSection() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const queryClient = useQueryClient();

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await ingestionApi.uploadCsv(file);
      toast.success(`Uploaded: ${res.data.processed} events processed, ${res.data.failed} failed`);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <Upload className="h-5 w-5" />
        CSV Upload
      </h2>
      <p className="mt-1 text-sm text-gray-500">
        Upload a CSV file with columns: <code className="text-xs bg-gray-100 px-1 rounded">event_name</code>,{" "}
        <code className="text-xs bg-gray-100 px-1 rounded">timestamp</code> (optional), plus any property columns.
      </p>
      <div className="mt-4">
        <input ref={fileRef} type="file" accept=".csv" onChange={handleUpload} className="hidden" />
        <button
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className="flex items-center gap-2 rounded-lg border-2 border-dashed border-gray-300 px-6 py-4 text-sm text-gray-600 hover:border-blue-400 hover:text-blue-600 disabled:opacity-50"
        >
          <Upload className="h-5 w-5" />
          {uploading ? "Uploading..." : "Choose CSV file"}
        </button>
      </div>
    </div>
  );
}

function JobsSection() {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => ingestionApi.listJobs().then((r) => r.data),
  });

  const statusColor: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    processing: "bg-blue-100 text-blue-800",
    completed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
  };

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Ingestion Jobs</h2>
      <div className="mt-4 space-y-2">
        {isLoading ? (
          <div className="h-10 animate-pulse rounded bg-gray-100" />
        ) : jobs?.length === 0 ? (
          <p className="text-sm text-gray-400">No ingestion jobs yet</p>
        ) : (
          jobs?.map((job: any) => (
            <div key={job.id} className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${statusColor[job.status] || ""}`}>
                    {job.status}
                  </span>
                  <span className="text-sm font-medium text-gray-900 uppercase">{job.job_type}</span>
                </div>
                <p className="mt-1 text-xs text-gray-400">
                  {job.processed_records}/{job.total_records} processed · {job.failed_records} failed ·{" "}
                  {new Date(job.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
