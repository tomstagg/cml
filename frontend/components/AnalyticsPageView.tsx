"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { trackPageView } from "@/lib/analytics";

// Mounted once in the root layout so every public page fires page_view
// without each page component having to opt in.
export function AnalyticsPageView() {
  const pathname = usePathname();
  const lastPath = useRef<string | null>(null);

  useEffect(() => {
    if (!pathname || lastPath.current === pathname) return;
    lastPath.current = pathname;
    const referrer = typeof document !== "undefined" ? document.referrer || undefined : undefined;
    trackPageView(pathname, referrer);
  }, [pathname]);

  return null;
}
