#!/usr/bin/env python3
"""Phase J6 end-to-end smoke test.

Drives the public + admin APIs through a complete user journey
(create session → 13 intake answers → results → re-rank → Proceed →
admin conflict-check → analytics export) so we can prove the
conveyancing pilot works end-to-end against any deployed environment.

Pre-requisites:
    The target DB has been bootstrapped with the WMCA dataset — i.e.
    `seed_synthetic.py` has been run, OR the three CSV importers plus
    `seed_price_cards.py` have been run against curated CSVs (see
    README "Ops data bootstrap"). Without enrolled, priced firms the
    results call returns an empty top-5 and the Proceed step fails.

Usage:
    docker-compose exec backend python scripts/smoke_test.py
    docker-compose exec backend python scripts/smoke_test.py \\
        --base-url https://api.choosemylawyer.co.uk \\
        --admin-key "$ADMIN_API_KEY"

Exit code is non-zero on any failure so this is suitable for CI.
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

# A "high-touch" intake (leasehold + mortgage + HtB ISA + shared ownership Y)
# exercises every conveyancing adjustment in the standard price card.
ANSWERS_HIGH_TOUCH: list[tuple[str, str]] = [
    ("purchase_price", "320000"),
    ("tenure", "leasehold"),
    ("property_postcode", "B17 9LJ"),
    ("mortgage", "yes"),
    ("new_build", "no"),
    ("help_to_buy_isa", "yes"),
    ("shared_ownership", "yes"),
    ("scorecard_preference", "balanced"),
    ("include_distance", "yes"),
    ("first_name", "Jane"),
    ("last_name", "Carter"),
    ("email", "jane@example.com"),
    ("phone", "07700 900123"),
]


class SmokeTest:
    def __init__(self, base_url: str, admin_key: str | None) -> None:
        self.base = base_url.rstrip("/")
        self.admin_key = admin_key
        self.client = httpx.Client(timeout=30.0)
        self.failures: list[str] = []
        self.warnings: list[str] = []

    # ---- assertion helpers ----------------------------------------------
    def ok(self, label: str) -> None:
        print(f"  ✓ {label}")

    def fail(self, label: str, detail: str = "") -> None:
        msg = f"{label}{f' — {detail}' if detail else ''}"
        self.failures.append(msg)
        print(f"  ✗ {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"  ! {msg}")

    def assert_status(self, label: str, response: httpx.Response, expected: int) -> bool:
        if response.status_code != expected:
            self.fail(
                label, f"expected {expected}, got {response.status_code}: {response.text[:200]}"
            )
            return False
        self.ok(f"{label} ({expected})")
        return True

    # ---- pipeline -------------------------------------------------------
    def step(self, label: str) -> None:
        print(f"\n── {label}")

    def run(self) -> int:
        self.step("1. Health check")
        r = self.client.get(f"{self.base}/health")
        if not self.assert_status("/health", r, 200):
            return self.summary()

        self.step("2. Create chat session")
        r = self.client.post(
            f"{self.base}/api/public/sessions",
            json={"practice_area": "residential_conveyancing"},
        )
        if not self.assert_status("POST /sessions", r, 201):
            return self.summary()
        session_id = r.json()["session_id"]
        print(f"  session_id = {session_id}")

        self.step("3. Submit 13 intake answers (balanced scorecard)")
        last: dict | None = None
        for qid, answer in ANSWERS_HIGH_TOUCH:
            r = self.client.post(
                f"{self.base}/api/public/sessions/{session_id}/answer",
                json={"question_id": qid, "answer": answer},
            )
            if r.status_code != 200:
                self.fail(f"answer {qid}", f"{r.status_code}: {r.text[:200]}")
                return self.summary()
            last = r.json()
        if last and last.get("is_complete"):
            self.ok("intake flagged complete")
        else:
            self.fail("intake should be complete after 13 answers")
            return self.summary()

        self.step("4. Get balanced results")
        r = self.client.get(f"{self.base}/api/public/search/{session_id}")
        if not self.assert_status("GET /search", r, 200):
            return self.summary()
        balanced = r.json()
        full_count = len(balanced["results"])
        top5_count = len(balanced["top_five_contactable"])
        print(f"  full market = {full_count} firms; top-5 contactable = {top5_count}")
        if full_count < 1:
            self.fail("full market has no firms — was the DB seeded?")
            return self.summary()
        if top5_count < 1:
            self.fail("no enrolled firms in top-5 — run seed_price_cards.py?")
            return self.summary()
        self.ok("≥1 enrolled firm contactable")

        # §8.13 — intervened firms must be excluded from results entirely.
        intervened_in_results = [f for f in balanced["results"] if f["sra_number"] == "9000015"]
        if intervened_in_results:
            self.fail("intervened firm 9000015 leaked into results", "should be filtered §8.13")
        else:
            self.ok("intervened firm 9000015 absent from results (§8.13)")

        balanced_full_set = {f["org_id"] for f in balanced["results"]}
        balanced_top1 = balanced["results"][0]

        self.step("5. Re-rank with reputation priority")
        r = self.client.patch(
            f"{self.base}/api/public/sessions/{session_id}/answer",
            json={"question_id": "scorecard_preference", "answer": "reputation"},
        )
        if not self.assert_status("PATCH scorecard=reputation", r, 200):
            return self.summary()
        r = self.client.get(f"{self.base}/api/public/search/{session_id}")
        if not self.assert_status("GET /search (reputation)", r, 200):
            return self.summary()
        prio = r.json()
        prio_full_set = {f["org_id"] for f in prio["results"]}
        if prio_full_set != balanced_full_set:
            self.fail(
                "full firm set changed across scorecards",
                f"balanced={len(balanced_full_set)} vs reputation={len(prio_full_set)}",
            )
        else:
            self.ok("full firm set unchanged across scorecards")
        prio_top1 = prio["results"][0]
        if prio_top1["org_id"] != balanced_top1["org_id"]:
            self.ok(
                f"top-1 reorders: balanced={balanced_top1['name']!r} → rep={prio_top1['name']!r}"
            )
        else:
            self.warn(f"top-1 unchanged ({balanced_top1['name']}) — could be coincidence")

        self.step("6. Complaints + regulatory source URLs render")
        sample = next(
            (
                f
                for f in balanced["results"]
                if f.get("complaints_sources") or f.get("regulatory_sources")
            ),
            None,
        )
        if sample is None:
            self.warn("no firm in results has decisions; check seed coverage")
        else:
            sources = (sample.get("complaints_sources") or []) + (
                sample.get("regulatory_sources") or []
            )
            if any(s.get("url") for s in sources):
                self.ok(f"{sample['name']!r} has source URLs")
            else:
                self.fail("decision rows present but no source URLs")

        self.step("7. POST Proceed appointment")
        self.client.patch(
            f"{self.base}/api/public/sessions/{session_id}/answer",
            json={"question_id": "scorecard_preference", "answer": "balanced"},
        )
        r = self.client.get(f"{self.base}/api/public/search/{session_id}")
        if not self.assert_status("GET /search (balanced re-fetch)", r, 200):
            return self.summary()
        target = r.json()["top_five_contactable"][0]
        appoint_body = {
            "session_id": session_id,
            "org_id": target["org_id"],
            "type": "appoint",
            "client_name": "Jane Carter",
            "client_email": "jane@example.com",
            "client_phone": "07700 900123",
            "quoted_price": (target.get("quote") or {}).get("total"),
            "consent_contacted": True,
            "consent_terms": True,
        }
        r = self.client.post(f"{self.base}/api/public/appointments", json=appoint_body)
        if not self.assert_status("POST /appointments", r, 201):
            return self.summary()
        appt = r.json()
        appt_id = appt["id"]
        print(f"  appointment_id = {appt_id} (firm = {target['name']!r})")

        self.step("8. Admin conflict-check (outcome=conflict)")
        if not self.admin_key:
            self.warn("skipped — set --admin-key or ADMIN_API_KEY env var")
        else:
            r = self.client.post(
                f"{self.base}/api/admin/appointments/{appt_id}/conflict-check",
                json={"outcome": "conflict"},
                headers={"X-Admin-Key": self.admin_key},
            )
            if self.assert_status("POST /admin/.../conflict-check", r, 200):
                if r.json().get("conflict_check_outcome") == "conflict":
                    self.ok("outcome=conflict recorded; user notification queued")
                else:
                    self.fail("conflict_check_outcome not recorded as 'conflict'")

        self.step("9. Public analytics event mirror")
        r = self.client.post(
            f"{self.base}/api/public/events",
            json={
                "event_type": "page_view",
                "session_id": session_id,
                "metadata": {"page": "/smoke-test"},
            },
        )
        if r.status_code == 202:
            self.ok("POST /events (202)")
        else:
            self.fail("POST /events", f"expected 202, got {r.status_code}: {r.text[:200]}")

        self.step("10. Admin analytics CSV export")
        if not self.admin_key:
            self.warn("skipped — set --admin-key or ADMIN_API_KEY env var")
        else:
            r = self.client.get(
                f"{self.base}/api/admin/analytics/export",
                headers={"X-Admin-Key": self.admin_key},
            )
            if self.assert_status("GET /admin/analytics/export", r, 200):
                ctype = r.headers.get("content-type", "")
                if "csv" in ctype:
                    self.ok(f"content-type = {ctype}")
                else:
                    self.fail("export not CSV", ctype)
                lines = r.text.strip().splitlines()
                if len(lines) >= 2:
                    self.ok(f"{len(lines) - 1} event rows in export")
                else:
                    self.warn("export contains only the header row")

        return self.summary()

    def summary(self) -> int:
        print()
        print("=" * 60)
        if self.warnings:
            print(f"warnings: {len(self.warnings)}")
            for w in self.warnings:
                print(f"  ! {w}")
        if self.failures:
            print(f"\nFAIL — {len(self.failures)} failure(s):")
            for f in self.failures:
                print(f"  ✗ {f}")
            return 1
        print("\nPASS — all automated smoke checks succeeded")
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SMOKE_BASE_URL", "http://localhost:8000"),
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--admin-key",
        default=os.environ.get("ADMIN_API_KEY"),
        help="X-Admin-Key for admin endpoints; reads ADMIN_API_KEY env var by default",
    )
    args = parser.parse_args()
    sys.exit(SmokeTest(args.base_url, args.admin_key).run())


if __name__ == "__main__":
    main()
