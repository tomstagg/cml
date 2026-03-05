"use client";

import { useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";
import { firmProfileApi } from "@/lib/api";
import { getStoredToken } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

type Profile = {
  id: string;
  sra_number: string;
  name: string;
  auth_status: string;
  website_url: string | null;
  phone: string | null;
  email: string | null;
  enrolled: boolean;
  offices: { id: string; address_line1: string | null; city: string | null; postcode: string; is_primary: boolean }[];
};

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [website, setWebsite] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");

  useEffect(() => {
    const token = getStoredToken();
    if (!token) { router.push("/login"); return; }
    firmProfileApi.get(token)
      .then((data) => {
        const p = data as Profile;
        setProfile(p);
        setWebsite(p.website_url ?? "");
        setPhone(p.phone ?? "");
        setEmail(p.email ?? "");
      })
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    const token = getStoredToken();
    if (!token) return;
    setSaving(true);
    try {
      const updated = await firmProfileApi.update(token, {
        website_url: website || undefined,
        phone: phone || undefined,
        email: email || undefined,
      });
      setProfile(updated as Profile);
      toast.success("Profile saved");
    } catch {
      toast.error("Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Firm Profile</h1>

      <div className="card p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-4">Firm Details</h2>
        <dl className="space-y-3">
          <div>
            <dt className="text-sm text-gray-500">Firm Name</dt>
            <dd className="font-medium text-gray-900">{profile.name}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">SRA Number</dt>
            <dd className="font-medium text-gray-900">{profile.sra_number}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">SRA Status</dt>
            <dd className="font-medium text-gray-900 capitalize">{profile.auth_status}</dd>
          </div>
        </dl>
      </div>

      <div className="card p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-4">Contact Information</h2>
        <div className="space-y-4">
          <div>
            <label className="label">Website URL</label>
            <input
              type="url"
              className="input"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="https://www.yourfirm.co.uk"
            />
          </div>
          <div>
            <label className="label">Phone</label>
            <input
              type="tel"
              className="input"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="01234 567890"
            />
          </div>
          <div>
            <label className="label">Email (for client notifications)</label>
            <input
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="enquiries@yourfirm.co.uk"
            />
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-gray-100">
          <button onClick={handleSave} disabled={saving} className="btn-primary">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Save className="w-4 h-4" /> Save Changes</>}
          </button>
        </div>
      </div>

      {profile.offices.length > 0 && (
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Offices</h2>
          <div className="space-y-3">
            {profile.offices.map((office) => (
              <div key={office.id} className="text-sm text-gray-600">
                <p>{office.address_line1}</p>
                <p>{office.city}, {office.postcode}</p>
                {office.is_primary && <span className="text-xs text-brand-600">Primary office</span>}
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-3">
            To update office addresses, contact us at hello@choosemylawyer.co.uk
          </p>
        </div>
      )}
    </div>
  );
}
