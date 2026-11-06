"use client";

import { useMemo, useState } from "react";
import { Bot, LoaderCircle, MessageCircle, Send, ShieldCheck, X } from "lucide-react";
import type { Dashboard } from "@/lib/types";
import { request } from "@/lib/api";

type Msg = { role: "user" | "assistant"; content: string };
type AIResponse = { answer: string; remaining_this_hour: number; model: string };

export function PennyPilotAI({ data }: { data: Dashboard | null }) {
  const [open,setOpen]=useState(false), [thinking,setThinking]=useState(false);
  const [question,setQuestion]=useState(""), [error,setError]=useState("");
  const [remaining,setRemaining]=useState<number|null>(null);
  const [messages,setMessages]=useState<Msg[]>([{role:"assistant",content:"I am ready. Ask about the financial period currently visible in PennyPilot."}]);

  const summary=useMemo(()=>data?{
    period:data.period, comparison_period:data.comparison_period, currency:data.currency, timezone:data.timezone,
    totals:data.totals, previous:data.previous, net_worth:data.net_worth, budget_remaining:data.budget_remaining,
    categories:data.categories.slice(0,8).map(x=>({name:x.name,amount:x.amount,previous:x.previous,change:x.change})),
    merchants:data.merchants.slice(0,5), income_sources:data.income_sources.slice(0,5),
    budgets:data.budgets.slice(0,5).map(b=>({name:b.name,start_date:b.start_date,end_date:b.end_date,allocated:b.allocated,spent:b.spent,remaining:b.remaining,allocations:b.allocations.slice(0,8).map(a=>({category:a.category,available:a.available,spent:a.spent,remaining:a.remaining,alert:a.alert}))})),
    goals:data.goals.slice(0,5).map(g=>({name:g.name,target_amount:g.target_amount,current_amount:g.current_amount,progress:g.progress,target_date:g.target_date,monthly_needed:g.monthly_needed})),
    upcoming:data.upcoming.slice(0,5).map(x=>({name:x.name,kind:x.kind,amount:x.amount,next_due:x.next_due,status:"projected, not paid"})),
    definitions:data.definitions
  }:null,[data]);

  async function ask(text?:string){
    const q=(text??question).trim(); if(!q||thinking)return;
    if(!summary){setError("Dashboard data is still loading.");return;}
    setThinking(true);setError("");setQuestion("");setMessages(m=>[...m,{role:"user",content:q}]);
    try{
      const result=await request<AIResponse>("/ai/coach",{method:"POST",body:JSON.stringify({question:q,summary})});
      setMessages(m=>[...m,{role:"assistant",content:result.answer}]);setRemaining(result.remaining_this_hour);
    }catch(e){setError(e instanceof Error?e.message:"PennyPilot AI could not respond.");}
    finally{setThinking(false);}
  }

  return <>
    <button type="button" className="ppai-launch" onClick={()=>setOpen(true)}><MessageCircle size={19}/> Ask PennyPilot AI</button>
    {open&&<div className="ppai-shade"><section className="ppai-panel" role="dialog" aria-modal="true" aria-label="PennyPilot AI Coach">
      <header className="ppai-head"><div><h2><Bot size={21}/> PennyPilot AI Coach</h2><p>Fast, read-only financial explanation assistant</p></div><button type="button" className="icon" aria-label="Close AI Coach" onClick={()=>setOpen(false)}><X size={20}/></button></header>
      <div className="ppai-safe"><ShieldCheck size={17}/> Only a limited aggregated summary is sent for this response. Credentials, receipts, notes, and raw transactions are excluded.</div>
      <div className="ppai-quick"><button type="button" onClick={()=>void ask("Summarize the selected period and comparison period.")}>Summarize</button><button type="button" onClick={()=>void ask("Which categories increased and what do the records show?")}>Spending changes</button><button type="button" onClick={()=>void ask("Which budgets need attention?")}>Budget warnings</button></div>
      <div className="ppai-chat" aria-live="polite">{messages.map((m,i)=><article key={i} className={`ppai-msg ${m.role}`}><b>{m.role==="assistant"?"PennyPilot AI":"You"}</b><p>{m.content}</p></article>)}{thinking&&<p className="ppai-thinking"><LoaderCircle className="ppai-spin" size={16}/> Analysing recorded aggregates...</p>}</div>
      {remaining!==null&&<small className="ppai-remaining">{remaining} AI questions remaining in this application hour.</small>}
      {error&&<p className="error" role="alert">{error}</p>}
      <form className="ppai-form" onSubmit={e=>{e.preventDefault();void ask();}}><label htmlFor="ppai-q">Ask about this period</label><div><textarea id="ppai-q" maxLength={500} value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Where did I spend the most?"/><button className="primary" disabled={!question.trim()||thinking} aria-label="Send"><Send size={18}/></button></div></form>
      <footer>AI can make mistakes. Confirm important figures on the dashboard. Free usage is limited and may be unavailable when the shared quota is reached.</footer>
    </section></div>}
  </>;
}