"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight } from "lucide-react";

const chips = [
  "I'm buying a property",
  "I'm selling",
  "Remortgage",
  "Talk to a real solicitor",
];

export function HeroSearch() {
  const router = useRouter();
  const [value, setValue] = useState("");

  // Stash the typed intent so a future chat update can surface it; the structured
  // intake doesn't read this yet.
  function go(starter: string) {
    if (typeof window !== "undefined" && starter.trim()) {
      window.sessionStorage.setItem("chat:starter", starter.trim());
    }
    router.push("/chat");
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          go(value);
        }}
        className="relative"
      >
        <label htmlFor="hero-search" className="sr-only">
          What can we help you with today?
        </label>
        <input
          id="hero-search"
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="What can we help you with today?"
          className="w-full h-16 rounded-full bg-white text-navy placeholder:text-ink-muted pl-6 pr-36 sm:pr-44 text-base shadow-soft focus:outline-none focus:ring-2 focus:ring-purple focus:ring-offset-2 focus:ring-offset-navy"
        />
        <button
          type="submit"
          className="btn-primary absolute right-2 top-1/2 -translate-y-1/2 h-12 px-5 sm:px-6 text-sm"
        >
          Find a lawyer
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
      <div className="mt-5 flex flex-wrap justify-center gap-2">
        {chips.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => go(c)}
            className="chip"
          >
            {c}
          </button>
        ))}
      </div>
    </div>
  );
}
