import { create } from "zustand";

interface User {
  id: string;
  email: string;
  full_name: string;
}

interface Org {
  id: string;
  name: string;
  slug: string;
  role: string;
}

interface AuthState {
  user: User | null;
  org: Org | null;
  orgs: Org[];
  setUser: (user: User | null) => void;
  setOrg: (org: Org | null) => void;
  setOrgs: (orgs: Org[]) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  org: null,
  orgs: [],
  setUser: (user) => set({ user }),
  setOrg: (org) => {
    if (org) localStorage.setItem("org_id", org.id);
    else localStorage.removeItem("org_id");
    set({ org });
  },
  setOrgs: (orgs) => set({ orgs }),
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("org_id");
    set({ user: null, org: null, orgs: [] });
  },
}));
