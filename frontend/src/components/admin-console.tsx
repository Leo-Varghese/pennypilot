"use client";

import {useEffect,useState} from "react";
import {request} from "@/lib/api";

type Overview={
  metrics:{users:number;transactions:number;accounts:number;registrations_last_7_days:number};
  users:Array<{id:string;masked_email:string;created_at:string|null}>;
  privacy:{financial_records_visible:boolean;emails_masked:boolean;admin_source:string};
};

export function AdminConsole(){
 const [data,setData]=useState<Overview|null>(null),[error,setError]=useState(""),[loading,setLoading]=useState(true);
 useEffect(()=>{void (async()=>{try{setData(await request<Overview>("/admin/overview"));}catch(e){setError((e as Error).message);}finally{setLoading(false);}})();},[]);
 if(loading)return <p className="banner">Loading administrator overview...</p>;
 if(error)return <section className="card"><h2>Administrator console</h2><p className="error">{error}</p><p className="muted">Access is granted only when the signed-in email is listed in the backend ADMIN_EMAILS environment variable.</p></section>;
 if(!data)return null;
 return <div className="admin-page">
  <section className="admin-hero"><p className="eyebrow">PRIVACY-SAFE OPERATIONS</p><h2>Administrator console</h2><p>Service-level metrics and a masked user directory. Financial records, balances, transactions, notes, receipts, and full email addresses are not exposed.</p></section>
  <div className="stats admin-stats"><section className="card stat"><p>Registered users</p><strong>{data.metrics.users}</strong></section><section className="card stat"><p>Transactions recorded</p><strong>{data.metrics.transactions}</strong></section><section className="card stat"><p>Financial accounts</p><strong>{data.metrics.accounts}</strong></section><section className="card stat"><p>New users in 7 days</p><strong>{data.metrics.registrations_last_7_days}</strong></section></div>
  <section className="card"><div className="row between"><div><p className="eyebrow">MASKED DIRECTORY</p><h3>Recent users</h3></div><span className="pill">Read only</span></div><div className="table-wrap"><table><thead><tr><th>Masked email</th><th>User ID</th><th>Registered</th></tr></thead><tbody>{data.users.map(user=><tr key={user.id}><td>{user.masked_email}</td><td><code>{user.id}</code></td><td>{user.created_at?new Date(user.created_at).toLocaleString():"Unavailable"}</td></tr>)}</tbody></table></div></section>
  <section className="card admin-privacy"><h3>Privacy boundaries</h3><ul><li>No financial records are visible.</li><li>Email addresses remain masked.</li><li>No transaction or account editing is available.</li><li>Administrator access is controlled server-side through ADMIN_EMAILS.</li></ul></section>
 </div>;
}