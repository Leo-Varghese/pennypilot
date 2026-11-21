"use client";

import {useEffect,useState} from "react";
import {CalendarDays,CheckCircle2,Plus,ShoppingBag,Trash2} from "lucide-react";
import {request} from "@/lib/api";
import {money,day} from "@/lib/format";
import type {Account,Category} from "@/lib/types";
import {Empty,Field,Modal} from "./ui";

type PlannedPurchase={id:string;name:string;planned_amount:string;currency:string;category_id:string|null;merchant:string;priority:number;target_date:string|null;notes:string;status:string;transaction_id:string|null};
type PlannedSuggestion={name:string;merchant:string;category_id:string|null;planned_amount:string;priority:number;source:string};
type Editor={name:string;planned_amount:string;category_id:string;merchant:string;priority:string;target_date:string;notes:string};
const empty:Editor={name:"",planned_amount:"",category_id:"",merchant:"",priority:"2",target_date:"",notes:""};

export function PlannedPurchases({accounts,categories,currency}:{accounts:Account[];categories:Category[];currency:string}){
 const [items,setItems]=useState<PlannedPurchase[]>([]),[status,setStatus]=useState("planned"),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 const [editor,setEditor]=useState<Editor|null>(null),[editing,setEditing]=useState<PlannedPurchase|null>(null),[buying,setBuying]=useState<PlannedPurchase|null>(null);
 const [suggestions,setSuggestions]=useState<PlannedSuggestion[]>([]),[suggestionLoading,setSuggestionLoading]=useState(false);

 async function load(){setBusy(true);setError("");try{setItems(await request<PlannedPurchase[]>(`/planned-purchases?status=${status}&currency=${currency}`));}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 useEffect(()=>{void load();},[status,currency]);

 useEffect(()=>{
   const term=editor?.name.trim()||"";
   if(!editor||term.length<2){setSuggestions([]);setSuggestionLoading(false);return;}
   const controller=new AbortController();
   const timer=window.setTimeout(async()=>{
     setSuggestionLoading(true);
     try{
       const result=await request<{items:PlannedSuggestion[]}>(`/planned-purchases/suggestions?q=${encodeURIComponent(term)}&limit=6`,{signal:controller.signal});
       setSuggestions(result.items);
     }catch(err){
       if(!(err instanceof DOMException&&err.name==="AbortError"))setSuggestions([]);
     }finally{
       if(!controller.signal.aborted)setSuggestionLoading(false);
     }
   },300);
   return()=>{window.clearTimeout(timer);controller.abort();};
 },[editor?.name]);

 function begin(item?:PlannedPurchase){setError("");setSuggestions([]);setEditing(item||null);setEditor(item?{name:item.name,planned_amount:item.planned_amount,category_id:item.category_id||"",merchant:item.merchant,priority:String(item.priority),target_date:item.target_date||"",notes:item.notes}:{...empty});}
 function applySuggestion(item:PlannedSuggestion){if(!editor)return;setEditor({...editor,name:item.name,merchant:item.merchant,category_id:item.category_id||"",planned_amount:item.planned_amount,priority:String(item.priority)});setSuggestions([]);}

 async function save(){
   if(!editor)return;
   setBusy(true);setError("");
   try{
     await request(`/planned-purchases${editing?`/${editing.id}`:""}`,{method:editing?"PUT":"POST",body:JSON.stringify({...editor,planned_amount:editor.planned_amount,currency,category_id:editor.category_id||null,priority:Number(editor.priority),target_date:editor.target_date||null})});
     setEditor(null);setEditing(null);setSuggestions([]);await load();
   }catch(e){setError((e as Error).message);}
   finally{setBusy(false);}
 }
 async function remove(item:PlannedPurchase){if(!confirm(`Delete planned purchase "${item.name}"?`))return;try{await request(`/planned-purchases/${item.id}`,{method:"DELETE"});await load();}catch(e){setError((e as Error).message);}}
 async function purchase(form:HTMLFormElement){if(!buying)return;const data=new FormData(form);setBusy(true);setError("");try{await request(`/planned-purchases/${buying.id}/purchase`,{method:"POST",body:JSON.stringify({account_id:data.get("account_id"),purchased_on:data.get("purchased_on"),payment_method:data.get("payment_method"),actual_amount:data.get("actual_amount")||null})});setBuying(null);await load();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 const total=items.filter(x=>x.status==="planned").reduce((sum,x)=>sum+Number(x.planned_amount),0);

 return <>
  <section className="planned-hero"><div><p className="eyebrow">PLAN BEFORE YOU SPEND</p><h2>Planned purchases</h2><p>Save purchases you may make later. Planned items do not affect expenses, account balances, budgets, or savings until marked as purchased.</p></div><button className="primary" onClick={()=>begin()}><Plus size={17}/> Add planned purchase</button></section>
  <div className="stats planned-stats"><section className="card stat"><p>Current planned total</p><strong>{money(total,currency)}</strong><small>Not included in actual spending</small></section><section className="card stat"><p>Active planned items</p><strong>{items.filter(x=>x.status==="planned").length}</strong><small>Wishlist and intended purchases</small></section></div>
  <div className="row wrap"><Field label="View"><select value={status} onChange={e=>setStatus(e.target.value)}><option value="planned">Planned</option><option value="purchased">Purchased</option><option value="cancelled">Cancelled</option><option value="all">All</option></select></Field></div>
  {error&&!editor&&!buying&&<p className="error" role="alert">{error}</p>}{busy&&!items.length&&<p className="banner">Loading planned purchases...</p>}
  <div className="planned-grid">{items.map(item=><article className="card planned-card" key={item.id}><div className="row between"><span className={`planned-priority p${item.priority}`}>Priority {item.priority}</span><span className="pill">{item.status}</span></div><div className="planned-icon"><ShoppingBag size={24}/></div><h3>{item.name}</h3><strong className="planned-price">{money(item.planned_amount,item.currency)}</strong><p className="muted">{item.merchant||"Merchant not decided"}</p>{item.target_date&&<p className="row"><CalendarDays size={15}/> Target: {day(item.target_date)}</p>}<p>{categories.find(c=>c.id===item.category_id)?.name||"Uncategorised"}</p>{item.notes&&<small>{item.notes}</small>}{item.status==="planned"&&<div className="row wrap planned-actions"><button className="primary" onClick={()=>{setError("");setBuying(item);}}><CheckCircle2 size={15}/> Mark purchased</button><button onClick={()=>begin(item)}>Edit</button><button className="icon danger" aria-label="Delete planned purchase" onClick={()=>void remove(item)}><Trash2 size={15}/></button></div>}{item.status==="purchased"&&<small>Converted to an actual transaction.</small>}</article>)}</div>
  {!busy&&!items.length&&<Empty text="No planned purchases in this view. Add an item without affecting your financial totals."/>}

  {editor&&<Modal title={editing?"Edit planned purchase":"Add planned purchase"} onClose={()=>{setEditor(null);setEditing(null);setSuggestions([]);setError("");}}><form onSubmit={e=>{e.preventDefault();void save();}}><div className="form-grid"><div className="planned-name-field"><Field label="Item name"><input autoComplete="off" value={editor.name} maxLength={120} onChange={e=>setEditor({...editor,name:e.target.value})}/></Field>{(suggestionLoading||suggestions.length>0)&&<div className="planned-suggestions" role="listbox" aria-label="Planned purchase suggestions">{suggestionLoading&&<small>Checking your previous entries...</small>}{suggestions.map((item,index)=><button type="button" key={`${item.name}-${item.merchant}-${index}`} onClick={()=>applySuggestion(item)}><span><strong>{item.name}</strong><small>{item.merchant||item.source} Â· {money(item.planned_amount,currency)}</small></span><span>Use</span></button>)}</div>}</div><Field label={`Expected price (${currency})`}><input type="number" min="0.01" step="0.01" value={editor.planned_amount} onChange={e=>setEditor({...editor,planned_amount:e.target.value})}/></Field><Field label="Category"><select value={editor.category_id} onChange={e=>setEditor({...editor,category_id:e.target.value})}><option value="">Uncategorised</option>{categories.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></Field><Field label="Merchant or store"><input value={editor.merchant} maxLength={160} onChange={e=>setEditor({...editor,merchant:e.target.value})}/></Field><Field label="Priority"><select value={editor.priority} onChange={e=>setEditor({...editor,priority:e.target.value})}><option value="1">1 - High</option><option value="2">2 - Medium</option><option value="3">3 - Low</option></select></Field><Field label="Target date"><input type="date" value={editor.target_date} onChange={e=>setEditor({...editor,target_date:e.target.value})}/></Field></div><Field label="Notes"><textarea value={editor.notes} maxLength={2000} onChange={e=>setEditor({...editor,notes:e.target.value})}/></Field>{error&&<p className="error" role="alert">{error}</p>}<button type="submit" className="primary full" disabled={busy||!editor.name.trim()||Number(editor.planned_amount)<=0}>{busy?"Saving...":"Save planned purchase"}</button></form></Modal>}

  {buying&&<Modal title={`Purchase ${buying.name}`} onClose={()=>{setBuying(null);setError("");}}><p className="muted">This creates a real expense transaction. The planned item itself never affected totals.</p><form onSubmit={e=>{e.preventDefault();void purchase(e.currentTarget);}}><div className="form-grid"><Field label="Pay from account"><select name="account_id" required><option value="">Choose account</option>{accounts.filter(a=>a.currency===buying.currency).map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select></Field><Field label="Actual price"><input name="actual_amount" type="number" min="0.01" step="0.01" defaultValue={buying.planned_amount}/></Field><Field label="Purchase date"><input name="purchased_on" type="date" defaultValue={new Date().toISOString().slice(0,10)} required/></Field><Field label="Payment method"><select name="payment_method" defaultValue="upi"><option value="upi">UPI</option><option value="cash">Cash</option><option value="debit_card">Debit card</option><option value="credit_card">Credit card</option><option value="wallet">Wallet</option><option value="bank_transfer">Bank transfer</option><option value="other">Other</option></select></Field></div>{error&&<p className="error" role="alert">{error}</p>}<button className="primary full" disabled={busy}>{busy?"Creating transaction...":"Create expense and mark purchased"}</button></form></Modal>}
 </>;
}