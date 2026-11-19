"use client";
import {useEffect,useState} from "react";
import {useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {z} from "zod";
import {formatInTimeZone,fromZonedTime} from "date-fns-tz";
import {Account,Category,Transaction} from "@/lib/types";
import {request} from "@/lib/api";
import {Modal,Field} from "./ui";
const schema=z.object({kind:z.enum(["income","expense","transfer","refund","adjustment"]),amount:z.string().regex(/^\d{1,18}(\.\d{1,2})?$/,"Use a positive amount with up to 2 decimals").refine(v=>Number(v)>0),occurred_at:z.string().min(1),account_id:z.string().min(1,"Choose an account"),destination_id:z.string(),category_id:z.string(),merchant:z.string().max(160),payment_method:z.string(),location:z.string().max(200),purpose:z.string().max(300),notes:z.string().max(5000),tags:z.string(),adjustment_direction:z.string()});
type Values=z.infer<typeof schema>;
type TransactionSuggestion={merchant:string;category_id:string|null;payment_method:string;purpose:string;kind:string;uses:number;last_used:string};
export function TransactionForm({accounts,categories,zone,existing,onClose,onSaved}:{accounts:Account[];categories:Category[];zone:string;existing?:Transaction;onClose:()=>void;onSaved:()=>void}){
 const [error,setError]=useState("");
 const [suggestions,setSuggestions]=useState<TransactionSuggestion[]>([]);
 const [suggestionLoading,setSuggestionLoading]=useState(false);
 const {register,watch,setValue,handleSubmit,formState:{errors,isSubmitting}}=useForm<Values>({resolver:zodResolver(schema),defaultValues:{kind:(existing?.kind as Values["kind"])||"expense",amount:existing?.amount||"",occurred_at:formatInTimeZone(existing?.occurred_at||new Date(),zone,"yyyy-MM-dd'T'HH:mm"),account_id:existing?.account_id||accounts[0]?.id||"",destination_id:existing?.destination_id||"",category_id:existing?.category_id||"",merchant:existing?.merchant||"",payment_method:existing?.payment_method||"upi",location:existing?.location||"",purpose:existing?.purpose||"",notes:existing?.notes||"",tags:existing?.tags.join(", ")||"",adjustment_direction:String(existing?.adjustment_direction||1)}});
 const kind=watch("kind");
 const merchant=watch("merchant");
 useEffect(()=>{
   const term=merchant.trim();
   if(term.length<2||kind==="transfer"){setSuggestions([]);setSuggestionLoading(false);return;}
   const controller=new AbortController();
   const timer=window.setTimeout(async()=>{
     setSuggestionLoading(true);
     try{
       const result=await request<{items:TransactionSuggestion[]}>(`/transactions/suggestions?q=${encodeURIComponent(term)}&limit=5`,{signal:controller.signal});
       setSuggestions(result.items);
     }catch(error){if(!(error instanceof DOMException&&error.name==="AbortError"))setSuggestions([]);}
     finally{if(!controller.signal.aborted)setSuggestionLoading(false);}
   },300);
   return()=>{window.clearTimeout(timer);controller.abort();};
 },[merchant,kind]);
 function applySuggestion(item:TransactionSuggestion){
   setValue("merchant",item.merchant,{shouldDirty:true});
   if(item.category_id)setValue("category_id",item.category_id,{shouldDirty:true});
   if(item.payment_method)setValue("payment_method",item.payment_method,{shouldDirty:true});
   if(item.purpose)setValue("purpose",item.purpose,{shouldDirty:true});
   if(["income","expense","refund","adjustment"].includes(item.kind))setValue("kind",item.kind as Values["kind"],{shouldDirty:true});
   setSuggestions([]);
 }
 async function submit(v:Values){setError("");try{const account=accounts.find(a=>a.id===v.account_id);if(!account)throw new Error("Create an account first");await request(`/transactions${existing?`/${existing.id}`:""}`,{method:existing?"PUT":"POST",body:JSON.stringify({...v,currency:account.currency,occurred_at:fromZonedTime(v.occurred_at,zone).toISOString(),category_id:kind==="transfer"?null:v.category_id||null,destination_id:kind==="transfer"?v.destination_id:null,tags:v.tags.split(",").map(t=>t.trim()).filter(Boolean),adjustment_direction:Number(v.adjustment_direction)})});onSaved();onClose();}catch(e){setError((e as Error).message);}}
 return <Modal title={existing?"Edit transaction":"Add transaction"} onClose={onClose}><form onSubmit={handleSubmit(submit)}><div className="form-grid"><Field label="Type"><select {...register("kind")}>{["expense","income","transfer","refund","adjustment"].map(k=><option key={k}>{k}</option>)}</select></Field><Field label="Amount"><input inputMode="decimal" {...register("amount")}/></Field><Field label={`Date and time (${zone})`}><input type="datetime-local" {...register("occurred_at")}/></Field><Field label="Account"><select {...register("account_id")}><option value="">Choose account</option>{accounts.map(a=><option key={a.id} value={a.id}>{a.name} ({a.currency})</option>)}</select></Field>{kind==="transfer"?<Field label="Destination"><select {...register("destination_id")}><option value="">Choose destination</option>{accounts.filter(a=>a.id!==watch("account_id")).map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select></Field>:<Field label="Category / subcategory"><select {...register("category_id")}><option value="">Uncategorized</option>{categories.map(c=><option key={c.id} value={c.id}>{c.parent_id?"↳ ":""}{c.name}</option>)}</select></Field>}<Field label="Payment method"><select {...register("payment_method")}>{["upi","cash","debit_card","credit_card","wallet","bank_transfer","other"].map(k=><option key={k}>{k}</option>)}</select></Field><div className="pp-tx-merchant"><Field label="Merchant / payee / source"><input autoComplete="off" {...register("merchant")}/></Field>{(suggestionLoading||suggestions.length>0)&&<div className="pp-tx-suggestions" role="listbox" aria-label="Previous transaction suggestions">{suggestionLoading&&<small>Checking your previous entries...</small>}{suggestions.map(item=><button type="button" key={`${item.merchant}-${item.category_id}-${item.payment_method}`} onClick={()=>applySuggestion(item)}><span><strong>{item.merchant}</strong><small>{item.purpose||item.payment_method.replaceAll("_"," ")} Â· used {item.uses} time{item.uses===1?"":"s"}</small></span><span>Use</span></button>)}</div>}</div><Field label="Location (optional)"><input {...register("location")}/></Field><Field label="Purpose: why this transaction?"><input {...register("purpose")}/></Field><Field label="Tags, separated by commas"><input {...register("tags")}/></Field>{kind==="adjustment"&&<Field label="Balance direction"><select {...register("adjustment_direction")}><option value="1">Increase</option><option value="-1">Decrease</option></select></Field>}</div><Field label="Notes / description"><textarea {...register("notes")}/></Field>{Object.entries(errors).map(([k,e])=><p key={k} role="alert" className="error">{k}: {e.message}</p>)}{error&&<p className="error" role="alert">{error}</p>}<button className="primary full" disabled={isSubmitting||!accounts.length}>{isSubmitting?"Saving...":"Save transaction"}</button></form></Modal>
}
