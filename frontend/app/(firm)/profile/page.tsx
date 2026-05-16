"use client";

import { useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";
import { firmProfileApi } from "@/lib/api";
import { getStoredToken } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

type Profile = {
  id: string;
  cml_firm_id: string;
  sra_number: string;
  name: string;
  trading_name: string;
  phone: string | null;
  referral_email: string | null;
  enrolled: boolean;
  active_in_pilot: boolean;
  offices: {
    id: string;
    address_line1: string | null;
    city: string | null;
    postcode: string;
    is_primary: boolean;
    office_type: string | null;
  }[];
};

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [phone, setPhone] = useState("");
  const [referralEmail, setReferralEmail] = useState("");

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      router.push("/login");
      return;
    }
    firmProfileApi
      .get(token)
      .then((data) => {
        const p = data as Profile;
        setProfile(p);
        setPhone(p.phone ?? "");
        setReferralEmail(p.referral_email ?? "");
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
        phone: phone || undefined,
        referral_email: referralEmail || undefined,
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
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-8 h-8 text-navy animate-spin" />
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-navy mb-6">Firm Details</h1>

      <div className="card p-6 mb-6">
        <h2 className="font-semibold text-navy mb-4">Firm</h2>
        <dl className="space-y-3">
          <div>
            <dt className="text-sm text-gray-500">Trading Name</dt>
            <dd className="font-medium text-navy">{profile.trading_name}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Legal Name</dt>
            <dd className="font-medium text-navy">{profile.name}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">CML Firm ID</dt>
            <dd className="font-medium text-navy">{profile.cml_firm_id}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">SRA Number</dt>
            <dd className="font-medium text-navy">{profile.sra_number}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Pilot Status</dt>
            <dd className="font-medium text-navy">
              {profile.active_in_pilot ? "Active in pilot" : "Not in pilot"}
            </dd>
          </div>
        </dl>
      </div>

      <div className="card p-6 mb-6">
        <h2 className="font-semibold text-navy mb-4">Contact Information</h2>
        <div className="space-y-4">
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
            <label className="label">Referral email</label>
            <p className="text-xs text-gray-500 mb-1">
              Proceed and Callback notifications are sent to this address.
            </p>
            <input
              type="email"
              className="input"
              value={referralEmail}
              onChange={(e) => setReferralEmail(e.target.value)}
              placeholder="enquiries@yourfirm.co.uk"
            />
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-gray-100">
          <button onClick={handleSave} disabled={saving} className="btn-gradient">
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Save className="w-4 h-4" /> Save Changes
              </>
            )}
          </button>
        </div>
      </div>

      {profile.offices.length > 0 && (
        <div className="card p-6">
          <h2 className="font-semibold text-navy mb-4">Offices</h2>
          <div className="space-y-3">
            {profile.offices.map((office) => (
              <div key={office.id} className="text-sm text-gray-600">
                <p>{office.address_line1}</p>
                <p>
                  {office.city}, {office.postcode}
                </p>
                {office.is_primary && (
                  <span className="text-xs text-purple">
                    Primary office{office.office_type ? ` · ${office.office_type}` : ""}
                  </span>
                )}
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
