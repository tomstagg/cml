"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, ArrowLeft, ArrowUpDown, ArrowUp, ArrowDown, Star } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { searchApi, type FirmResult, type SearchResponse } from "@/lib/api";
import { trackResultsViewed } from "@/lib/analytics";
import { ComplaintsCell } from "./ComplaintsCell";
import { RegulatoryCell } from "./RegulatoryCell";
import { AppointModal } from "./AppointModal";
import { CallbackModal } from "./CallbackModal";
import { ReorderControl } from "./ReorderControl";
import { cn, formatCurrency } from "@/lib/utils";

type SortKey = "rank" | "price" | "reputation" | "complaints" | "regulatory" | "distance" | "offices";
type SortDir = "asc" | "desc";

const PAGE_SIZE = 10;

const SCORECARD_LABEL: Record<string, string> = {
  balanced: "Balanced",
  reputation: "Reputation priority",
  price: "Price priority",
  complaints: "Complaints history priority",
  regulatory: "Regulatory history priority",
  distance: "Distance priority",
  offices: "Number of offices priority",
};

export function ResultsClient({ sessionId }: { sessionId: string }) {
  const router = useRouter();
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [reordering, setReordering] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>("rank");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [page, setPage] = useState(1);
  const [appointFirm, setAppointFirm] = useState<FirmResult | null>(null);
  const [callbackFirm, setCallbackFirm] = useState<FirmResult | null>(null);

  useEffect(() => {
    loadResults();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadResults(opts?: { scorecard_preference?: string; include_distance?: boolean }) {
    const isInitial = !opts;
    if (!isInitial) setReordering(true);
    try {
      const res = await searchApi.getResults(sessionId, opts);
      setData(res);
      if (isInitial) {
        trackResultsViewed(sessionId, res.top_five_contactable.length, res.results.length);
      }
    } catch (err) {
      const status = (err as { status?: number }).status;
      if (status === 400) {
        toast.error("Please complete the questionnaire first.");
        router.push(`/chat?session=${sessionId}`);
      } else {
        toast.error("Failed to load results. Please try again.");
      }
    } finally {
      setLoading(false);
      setReordering(false);
    }
  }

  const includeDistance = data?.include_distance ?? false;

  const topFiveIds = useMemo(
    () => new Set((data?.top_five_contactable ?? []).map((f) => f.org_id)),
    [data],
  );

  const fullSorted = useMemo(() => {
    if (!data) return [];
    const rows = [...data.results];
    rows.sort((a, b) => sortValue(a, sortKey, b) * (sortDir === "asc" ? 1 : -1));
    return rows;
  }, [data, sortKey, sortDir]);

  const pageCount = Math.max(1, Math.ceil(fullSorted.length / PAGE_SIZE));
  const paged = useMemo(
    () => fullSorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [fullSorted, page],
  );

  function onHeaderClick(key: SortKey) {
    if (key === sortKey) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir(key === "rank" ? "asc" : key === "price" || key === "distance" ? "asc" : "desc");
    }
    setPage(1);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-64px)]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-3" />
          <p className="text-gray-500">Finding the best solicitors for you...</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const topFive = data.top_five_contactable;

  return (
    <div className="py-8 px-4 max-w-7xl mx-auto">
      <div className="mb-6">
        <button
          onClick={() => router.push(`/chat?session=${sessionId}&revise=1`)}
          className="btn-ghost text-sm mb-3"
        >
          <ArrowLeft className="w-4 h-4" /> Revise answers
        </button>
        <h1 className="text-h2 md:text-h2-md text-navy">Your conveyancing quotes</h1>
        <p className="text-sm text-gray-500 mt-2">
          {data.total} firm{data.total === 1 ? "" : "s"} found ·{" "}
          <span className="text-navy font-medium">
            {SCORECARD_LABEL[data.scorecard_preference] ?? "Balanced"}
          </span>
          {!includeDistance && " · Distance excluded"}
        </p>
      </div>

      <ReorderControl
        scorecard={data.scorecard_preference}
        includeDistance={includeDistance}
        hasPostcode={Boolean(data.postcode)}
        disabled={reordering}
        onChange={({ scorecard, includeDistance: nextIncludeDistance }) =>
          loadResults({
            scorecard_preference: scorecard,
            include_distance: nextIncludeDistance,
          })
        }
      />

      {data.total === 0 ? (
        <div className="text-center py-16 card">
          <p className="text-gray-500 mb-4">
            No firms found matching your criteria yet.
          </p>
        </div>
      ) : (
        <>
          {topFive.length > 0 && (
            <section className="mb-10">
              <h2 className="text-h4 text-navy mb-3">
                Top {topFive.length} contactable firm{topFive.length === 1 ? "" : "s"}
              </h2>
              <ResultsTable
                rows={topFive}
                topFiveIds={topFiveIds}
                includeDistance={includeDistance}
                tinted
                onAppoint={setAppointFirm}
                onCallback={setCallbackFirm}
              />
            </section>
          )}

          <section>
            <h2 className="text-h4 text-navy mb-3">Full market — {data.total} firms</h2>
            <ResultsTable
              rows={paged}
              topFiveIds={topFiveIds}
              includeDistance={includeDistance}
              sortable
              sortKey={sortKey}
              sortDir={sortDir}
              onSort={onHeaderClick}
              onAppoint={setAppointFirm}
              onCallback={setCallbackFirm}
            />
            {pageCount > 1 && (
              <Pagination page={page} pageCount={pageCount} onChange={setPage} />
            )}
          </section>
        </>
      )}

      <p className="text-xs text-gray-400 text-center mt-8 max-w-2xl mx-auto">
        All firms are checked against the SRA register. Quoted prices include VAT and stated
        included disbursements; excluded disbursements (e.g. Stamp Duty Land Tax) are payable in
        addition. Choose My Lawyer is not regulated by the SRA.
      </p>

      {appointFirm && (
        <AppointModal
          firm={appointFirm}
          sessionId={sessionId}
          onClose={() => setAppointFirm(null)}
        />
      )}
      {callbackFirm && (
        <CallbackModal
          firm={callbackFirm}
          sessionId={sessionId}
          onClose={() => setCallbackFirm(null)}
        />
      )}
    </div>
  );
}

function sortValue(a: FirmResult, key: SortKey, b: FirmResult): number {
  switch (key) {
    case "rank":
      return a.rank - b.rank;
    case "price":
      return (a.quote?.total ?? Infinity) - (b.quote?.total ?? Infinity);
    case "reputation":
      return (a.factor_scores?.reputation ?? -Infinity) - (b.factor_scores?.reputation ?? -Infinity);
    case "complaints":
      return (a.factor_scores?.complaints ?? -Infinity) - (b.factor_scores?.complaints ?? -Infinity);
    case "regulatory":
      return (a.factor_scores?.regulatory ?? -Infinity) - (b.factor_scores?.regulatory ?? -Infinity);
    case "distance":
      return (a.distance_km ?? Infinity) - (b.distance_km ?? Infinity);
    case "offices":
      return a.office_count - b.office_count;
  }
}

type TableProps = {
  rows: FirmResult[];
  topFiveIds: Set<string>;
  includeDistance: boolean;
  tinted?: boolean;
  sortable?: boolean;
  sortKey?: SortKey;
  sortDir?: SortDir;
  onSort?: (key: SortKey) => void;
  onAppoint: (firm: FirmResult) => void;
  onCallback: (firm: FirmResult) => void;
};

function ResultsTable({
  rows,
  topFiveIds,
  includeDistance,
  tinted,
  sortable,
  sortKey,
  sortDir,
  onSort,
  onAppoint,
  onCallback,
}: TableProps) {
  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-navy text-white">
          <tr>
            <Th align="left">Rank</Th>
            <Th align="left">Firm</Th>
            <Th sortable={sortable} sortKey="reputation" current={sortKey} dir={sortDir} onSort={onSort}>
              Reputation
            </Th>
            <Th sortable={sortable} sortKey="complaints" current={sortKey} dir={sortDir} onSort={onSort}>
              Complaints
            </Th>
            <Th sortable={sortable} sortKey="regulatory" current={sortKey} dir={sortDir} onSort={onSort}>
              Regulatory
            </Th>
            <Th sortable={sortable} sortKey="price" current={sortKey} dir={sortDir} onSort={onSort} align="right">
              Price
            </Th>
            {includeDistance && (
              <Th sortable={sortable} sortKey="distance" current={sortKey} dir={sortDir} onSort={onSort} align="right">
                Distance
              </Th>
            )}
            <Th sortable={sortable} sortKey="offices" current={sortKey} dir={sortDir} onSort={onSort} align="right">
              Offices
            </Th>
            <Th align="right">Action</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((firm) => {
            const isTopFive = topFiveIds.has(firm.org_id);
            return (
              <tr
                key={firm.org_id}
                className={cn(
                  "border-t border-gray-100 align-top",
                  tinted ? "bg-[#EAF8FB]" : "bg-white",
                )}
              >
                <td className="py-3 px-3 font-semibold text-navy">{firm.rank}</td>
                <td className="py-3 px-3">
                  <div className="font-medium text-navy">{firm.trading_name}</div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {firm.city || firm.postcode || "—"}
                  </div>
                </td>
                <td className="py-3 px-3">
                  <ReputationCell firm={firm} />
                </td>
                <td className="py-3 px-3">
                  <ComplaintsCell
                    score={firm.factor_scores?.complaints ?? 100}
                    sourceUrl={firm.complaints_url}
                    compact
                  />
                </td>
                <td className="py-3 px-3">
                  <RegulatoryCell
                    score={firm.factor_scores?.regulatory ?? 100}
                    sourceUrl={firm.regulatory_url}
                    compact
                  />
                </td>
                <td className="py-3 px-3 text-right">
                  {firm.quote ? (
                    <span className="font-semibold text-navy">
                      {formatCurrency(Math.ceil(firm.quote.total))}
                    </span>
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                {includeDistance && (
                  <td className="py-3 px-3 text-right text-navy">
                    {firm.distance_km !== null ? `${firm.distance_km} km` : "—"}
                  </td>
                )}
                <td className="py-3 px-3 text-right text-navy">{firm.office_count}</td>
                <td className="py-3 px-3 text-right">
                  {firm.enrolled && isTopFive ? (
                    <div className="flex flex-col gap-1.5 items-end">
                      <button
                        onClick={() => onAppoint(firm)}
                        className="bg-gradient-to-br from-purple to-teal text-white text-xs font-medium px-3 py-1.5 rounded-full hover:opacity-90"
                      >
                        Proceed
                      </button>
                      <button
                        onClick={() => onCallback(firm)}
                        className="text-xs text-navy border border-navy/30 px-3 py-1 rounded-full hover:bg-navy/5"
                      >
                        Request callback
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs text-gray-400 italic">
                      {firm.enrolled ? "Not in top 5" : "Not enrolled"}
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Th({
  children,
  align = "left",
  sortable,
  sortKey,
  current,
  dir,
  onSort,
}: {
  children: React.ReactNode;
  align?: "left" | "right" | "center";
  sortable?: boolean;
  sortKey?: SortKey;
  current?: SortKey;
  dir?: SortDir;
  onSort?: (key: SortKey) => void;
}) {
  const alignCls =
    align === "right" ? "text-right" : align === "center" ? "text-center" : "text-left";

  if (!sortable || !sortKey || !onSort) {
    return (
      <th className={cn("py-3 px-3 font-medium text-xs uppercase tracking-wide", alignCls)}>
        {children}
      </th>
    );
  }

  const active = current === sortKey;
  const Icon = active ? (dir === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;
  return (
    <th className={cn("py-3 px-3 font-medium text-xs uppercase tracking-wide", alignCls)}>
      <button
        onClick={() => onSort(sortKey)}
        className={cn(
          "inline-flex items-center gap-1 hover:text-teal",
          align === "right" && "ml-auto",
          active && "text-teal",
        )}
      >
        {children}
        <Icon className="w-3 h-3" />
      </button>
    </th>
  );
}

function ReputationCell({ firm }: { firm: FirmResult }) {
  if (firm.google_rating === null || firm.google_rating === undefined) {
    return <span className="text-xs text-gray-400">No reviews</span>;
  }
  const ratingNode = (
    <div className="flex items-center gap-1">
      <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
      <span className="text-sm font-medium text-navy">{firm.google_rating.toFixed(1)}</span>
    </div>
  );
  return (
    <div className="flex flex-col items-start gap-0.5">
      {firm.google_reviews_url ? (
        <a
          href={firm.google_reviews_url}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:underline"
        >
          {ratingNode}
        </a>
      ) : (
        ratingNode
      )}
      {firm.google_review_count !== null && (
        <span className="text-xs text-gray-500">
          {firm.google_review_count} review{firm.google_review_count === 1 ? "" : "s"}
        </span>
      )}
    </div>
  );
}

function Pagination({
  page,
  pageCount,
  onChange,
}: {
  page: number;
  pageCount: number;
  onChange: (n: number) => void;
}) {
  const pages = pageNumbers(page, pageCount);
  return (
    <nav className="flex items-center justify-center gap-2 mt-6" aria-label="Pagination">
      <button
        onClick={() => onChange(Math.max(1, page - 1))}
        disabled={page === 1}
        className="text-sm px-3 py-1.5 rounded-full border border-gray-200 text-navy disabled:opacity-40"
      >
        Prev
      </button>
      {pages.map((p, i) =>
        p === "…" ? (
          <span key={`ellipsis-${i}`} className="text-gray-400 px-1">
            …
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p)}
            className={cn(
              "w-8 h-8 rounded-full text-sm font-medium",
              p === page
                ? "bg-navy text-white"
                : "text-navy hover:bg-gray-100",
            )}
          >
            {p}
          </button>
        ),
      )}
      <button
        onClick={() => onChange(Math.min(pageCount, page + 1))}
        disabled={page === pageCount}
        className="text-sm px-3 py-1.5 rounded-full border border-gray-200 text-navy disabled:opacity-40"
      >
        Next
      </button>
    </nav>
  );
}

function pageNumbers(page: number, total: number): (number | "…")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const out: (number | "…")[] = [1];
  if (page > 3) out.push("…");
  for (let p = Math.max(2, page - 1); p <= Math.min(total - 1, page + 1); p++) {
    out.push(p);
  }
  if (page < total - 2) out.push("…");
  out.push(total);
  return out;
}
