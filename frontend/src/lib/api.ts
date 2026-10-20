let token = "";
export const setToken = (value:string) => { token=value; };
export function apiBase(){
 const base=process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/,"");
 if(!base) throw new Error("Set NEXT_PUBLIC_API_BASE_URL to your FastAPI origin, then rebuild the frontend.");
 return base;
}
export async function request<T=unknown>(path:string, options:RequestInit={}):Promise<T>{
 const headers=new Headers(options.headers);
 if(token) headers.set("Authorization",`Bearer ${token}`);
 if(options.body && !(options.body instanceof FormData)) headers.set("Content-Type","application/json");
 let response:Response;
 try { response=await fetch(`${apiBase()}/api/v1${path}`,{...options,headers,cache:"no-store",signal:AbortSignal.timeout(30000)}); }
 catch { throw new Error("Cannot reach the API. Check the backend health, API URL and allowed CORS origins."); }
 if(!response.ok){ const body=await response.json().catch(()=>({detail:response.statusText})); throw new Error(typeof body.detail==="string"?body.detail:JSON.stringify(body.detail)); }
 if(response.status===204) return undefined as T;
 return response.json() as Promise<T>;
}
export async function download(path:string,name:string){
 const response=await fetch(`${apiBase()}/api/v1${path}`,{headers:{Authorization:`Bearer ${token}`},cache:"no-store"});
 if(!response.ok) throw new Error("Download failed. Check your session and filters.");
 const url=URL.createObjectURL(await response.blob()); const a=document.createElement("a"); a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
