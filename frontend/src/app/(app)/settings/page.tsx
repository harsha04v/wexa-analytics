"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { useState } from "react";
import toast from "react-hot-toast";
import { Users, UserPlus } from "lucide-react";

export default function SettingsPage() {
  const { org } = useAuthStore();

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {org && (
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">Organization</h2>
          <div className="mt-4 space-y-2 text-sm">
            <p><span className="text-gray-500">Name:</span> {org.name}</p>
            <p><span className="text-gray-500">Slug:</span> {org.slug}</p>
            <p><span className="text-gray-500">Your Role:</span> <span className="capitalize">{org.role}</span></p>
          </div>
        </div>
      )}

      <MembersSection />
      <InviteSection />
    </div>
  );
}

function MembersSection() {
  const { data: members, isLoading } = useQuery({
    queryKey: ["members"],
    queryFn: () => authApi.members().then((r) => r.data),
  });

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <Users className="h-5 w-5" />
        Team Members
      </h2>
      <div className="mt-4 space-y-2">
        {isLoading ? (
          <div className="h-10 animate-pulse rounded bg-gray-100" />
        ) : (
          members?.map((m: any) => (
            <div key={m.id} className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3">
              <div>
                <p className="text-sm font-medium text-gray-900">{m.user_name}</p>
                <p className="text-xs text-gray-400">{m.user_email}</p>
              </div>
              <span className="rounded bg-gray-100 px-2 py-1 text-xs font-medium capitalize text-gray-600">
                {m.role}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function InviteSection() {
  const { org } = useAuthStore();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("analyst");
  const queryClient = useQueryClient();

  const inviteMutation = useMutation({
    mutationFn: () => authApi.invite({ email, role }),
    onSuccess: (res) => {
      toast.success(`Invitation sent. Token: ${res.data.token}`);
      setEmail("");
      queryClient.invalidateQueries({ queryKey: ["members"] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to invite");
    },
  });

  if (org?.role !== "owner" && org?.role !== "admin") return null;

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <UserPlus className="h-5 w-5" />
        Invite Member
      </h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          inviteMutation.mutate();
        }}
        className="mt-4 flex gap-3"
      >
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email address"
          required
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="admin">Admin</option>
          <option value="analyst">Analyst</option>
          <option value="viewer">Viewer</option>
        </select>
        <button
          type="submit"
          disabled={inviteMutation.isPending}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
        >
          Invite
        </button>
      </form>
    </div>
  );
}
