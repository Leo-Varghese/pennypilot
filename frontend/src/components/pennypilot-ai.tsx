"use client";

import { useMemo, useRef, useState } from "react";
import { Bot, LoaderCircle, MessageCircle, Send, ShieldCheck, X } from "lucide-react";
import type { MLCEngine } from "@mlc-ai/web-llm";
import type { Dashboard } from "@/lib/types";

const SYSTEM = `You are PennyPilot AI Coach, a read-only personal finance explanation assistant.
Use only the supplied PennyPilot summary. Never invent transactions, explanations, merchants, or causes.
Distinguish recorded facts from general suggestions. Never claim to change data.
Never request passwords, tokens, card numbers, UPI PINs, or credentials.
Do not provide personalized investment, tax, legal, credit, or lending advice.
Mention the comparison period when discussing changes. Transfers, adjustments, goals, and projected bills are not expenses.
Keep answers concise, practical, and in Indian English. State when data is insufficient.`;

type Msg = { role: "user" | "assistant"; content: string };

export function PennyPilotAI({ data }: { data: Dashboard | null }) {
  const engine = useRef<MLCEngine | null>(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Msg[]>([{ role: "assistant", content: "Load the free local model, then ask about the period visible in PennyPilot." }]);

  const context = useMemo(() => data ? {
    period: data.period,
    comparison_period: data.comparison_period,
    currency: data.currency,
    timezone: data.timezone,
    totals: data.totals,
    previous: data.previous,
    net_worth: data.net_worth,
    budget_remaining: data.budget_remaining,
    categories: data.categories.slice(0, 8),
    merchants: data.merchants.slice(0, 5),
    budgets: data.budgets.slice(0, 5).map(b => ({ name:b.name, start_date:b.start_date, end_date:b.end_date, allocated:b.allocated, spent:b.spent, remaining:b.remaining, allocations:b.allocations.slice(0,8) })),
    goals: data.goals.slice(0, 5).map(g => ({ name:g.name, target_amount:g.target_amount, current_amount:g.current_amount, progress:g.progress, target_date:g.target_date, monthly_needed:g.monthly_needed })),
    upcoming: data.upcoming.slice(0, 5).map(x => ({ name:x.name, kind:x.kind, amount:x.amount, next_due:x.next_due, status:"projected, not paid" })),
    definitions: data.definitions,
  } : null, [data]);

  async function loadModel() {
    if (engine.current) return engine.current;
    if (!("gpu" in navigator)) throw new Error("This device does not support WebGPU. Use a current Chrome or Edge browser with hardware acceleration enabled.");
    setLoading(true); setError(""); setStatus("Finding a lightweight local model...");
    try {
      const webllm = await import("@mlc-ai/web-llm");
      const ids = webllm.prebuiltAppConfig.model_list.map(m => m.model_id);
      const id = ids.find(x => x.includes("Qwen2.5-1.5B-Instruct")) || ids.find(x => x.includes("SmolLM2") && x.includes("1.7B") && x.includes("Instruct")) || ids.find(x => x.includes("Qwen") && x.includes("Instruct"));
      if (!id) throw new Error("No compatible lightweight model is available in this WebLLM release.");
      engine.current = await webllm.CreateMLCEngine(id, { initProgressCallback: p => setStatus(`${p.text}${typeof p.progress === "number" ? ` ${Math.round(p.progress*100)}%` : ""}`) });
      setStatus(`Ready: ${id}`);
      return engine.current;
    } finally { setLoading(false); }
  }

  async function ask(text?: string) {
    const q=(text ?? question).trim(); if (!q || thinking) return;
    if (!context) { setError("Dashboard data is still loading."); return; }
    setThinking(true); setError(""); setQuestion(""); setMessages(m => [...m,{role:"user",content:q}]);
    try {
      const local = await loadModel();
      const reply = await local.chat.completions.create({
        messages:[{role:"system",content:SYSTEM},{role:"user",content:`PennyPilot summary:
${JSON.stringify(context)}

Question: ${q}`}],
        temperature:0.2, top_p:0.8, max_tokens:400,
      });
      setMessages(m => [...m,{role:"assistant",content:reply.choices[0]?.message?.content?.trim() || "No explanation was generated."}]);
    } catch (e) { setError(e instanceof Error ? e.message : "The local AI failed to respond."); }
    finally { setThinking(false); }
  }

  return <>
    <button type="button" className="ppai-launch" onClick={()=>setOpen(true)}><MessageCircle size={19}/> Ask PennyPilot AI</button>
    {open && <div className="ppai-shade"><section className="ppai-panel" role="dialog" aria-modal="true" aria-label="PennyPilot AI Coach">
      <header className="ppai-head"><div><h2><Bot size={21}/> PennyPilot AI Coach</h2><p>Free, read-only, on-device assistant</p></div><button type="button" className="icon" aria-label="Close AI Coach" onClick={()=>setOpen(false)}><X size={20}/></button></header>
      <div className="ppai-safe"><ShieldCheck size={17}/> Financial summary stays in this browser. No paid AI API is used.</div>
      {!engine.current && <div className="ppai-load"><button type="button" className="primary" disabled={loading} onClick={()=>loadModel().catch(e=>setError(e.message))}>{loading?<LoaderCircle className="ppai-spin" size={17}/>:<Bot size={17}/>} {loading?"Loading local AI...":"Load free local AI"}</button><small>{status || "First use downloads and caches the model on this device."}</small></div>}
      <div className="ppai-quick"><button type="button" onClick={()=>ask("Summarize the selected period and comparison period.")}>Summarize</button><button type="button" onClick={()=>ask("Which categories increased and what do the records show?")}>Spending changes</button><button type="button" onClick={()=>ask("Which budgets need attention?")}>Budget warnings</button></div>
      <div className="ppai-chat" aria-live="polite">{messages.map((m,i)=><article key={i} className={`ppai-msg ${m.role}`}><b>{m.role==="assistant"?"PennyPilot AI":"You"}</b><p>{m.content}</p></article>)}{thinking&&<p className="ppai-thinking"><LoaderCircle className="ppai-spin" size={16}/> Analysing recorded data...</p>}</div>
      {error&&<p className="error" role="alert">{error}</p>}
      <form className="ppai-form" onSubmit={e=>{e.preventDefault();void ask();}}><label htmlFor="ppai-q">Ask about this period</label><div><textarea id="ppai-q" maxLength={500} value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Where did I spend the most?"/><button className="primary" disabled={!question.trim()||thinking} aria-label="Send"><Send size={18}/></button></div></form>
      <footer>AI can make mistakes. Confirm important figures on the dashboard.</footer>
    </section></div>}
  </>;
}
