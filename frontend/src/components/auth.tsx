"use client";
import {useState} from "react";
import {useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {z} from "zod";
import {Wallet,ShieldCheck} from "lucide-react";
import {request,setToken} from "@/lib/api";
import {Field} from "./ui";
const schema=z.object({email:z.email(),password:z.string().min(12,"Use at least 12 characters").max(128)});
type Values=z.infer<typeof schema>;
export function Auth({onLogin}:{onLogin:()=>void}){
 const [register,setRegister]=useState(false),[error,setError]=useState("");
 const {register:field,handleSubmit,formState:{errors,isSubmitting}}=useForm<Values>({resolver:zodResolver(schema)});
 async function submit(values:Values){setError("");try{const data=await request<{access_token:string}>(`/auth/${register?"register":"login"}`,{method:"POST",body:JSON.stringify(values)});setToken(data.access_token);onLogin();}catch(e){setError((e as Error).message);}}
 return <main className="auth"><section className="auth-story"><div className="brand"><Wallet/> PennyPilot</div><h1>A clearer view.<br/>A calmer money life.</h1><p>Track the everyday. Plan the important. Know exactly where your money goes.</p><div className="pill"><ShieldCheck size={18}/> Private by design. Your records, your control.</div></section><section className="auth-card"><p className="eyebrow">YOUR MONEY, WITH DIRECTION</p><h2>{register?"Start your money journey":"Welcome back"}</h2><p className="muted">{register?"Create an account. No sample financial history is added.":"Sign in to your personal finance workspace."}</p><form onSubmit={handleSubmit(submit)}><Field label="Email"><input type="email" autoComplete="email" {...field("email")}/></Field>{errors.email&&<small role="alert">{errors.email.message}</small>}<Field label="Password"><input type="password" autoComplete={register?"new-password":"current-password"} {...field("password")}/></Field>{errors.password&&<small role="alert">{errors.password.message}</small>}{error&&<p className="error" role="alert">{error}</p>}<button className="primary full" disabled={isSubmitting}>{isSubmitting?"Connecting...":register?"Create account":"Sign in"}</button></form><button className="link" onClick={()=>setRegister(!register)}>{register?"Already have an account? Sign in":"New here? Create an account"}</button><p className="muted small">Sessions stay in memory only. Refreshing the page requires signing in again.</p></section></main>
}
