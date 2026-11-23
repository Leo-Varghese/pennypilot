"use client";
import {useEffect,useState} from "react";

type InstallEvent=Event&{prompt:()=>Promise<void>;userChoice:Promise<{outcome:"accepted"|"dismissed"}>};
export function MobileAppSupport(){
 const [event,setEvent]=useState<InstallEvent|null>(null),[installed,setInstalled]=useState(false),[updated,setUpdated]=useState(false);
 useEffect(()=>{
  if("serviceWorker" in navigator){
   navigator.serviceWorker.register("/sw.js",{scope:"/",updateViaCache:"none"}).then(registration=>{
    registration.update();
    registration.addEventListener("updatefound",()=>{const worker=registration.installing;if(!worker)return;worker.addEventListener("statechange",()=>{if(worker.state==="installed"&&navigator.serviceWorker.controller)setUpdated(true);});});
   }).catch(()=>{});
   navigator.serviceWorker.addEventListener("controllerchange",()=>window.location.reload());
  }
  const standalone=window.matchMedia("(display-mode: standalone)").matches||Boolean((navigator as Navigator&{standalone?:boolean}).standalone);
  setInstalled(standalone);
  const before=(raw:Event)=>{raw.preventDefault();setEvent(raw as InstallEvent);};
  const done=()=>{setInstalled(true);setEvent(null);};
  window.addEventListener("beforeinstallprompt",before);
  window.addEventListener("appinstalled",done);
  return()=>{window.removeEventListener("beforeinstallprompt",before);window.removeEventListener("appinstalled",done);};
 },[]);
 async function install(){if(!event){window.location.href="/install";return;}await event.prompt();const choice=await event.userChoice;if(choice.outcome==="accepted")setInstalled(true);setEvent(null);}
 if(installed&&!updated)return null;
 return <>{!installed&&<button type="button" className="mobile-install-button" onClick={()=>void install()}>Install mobile app</button>}{updated&&<button type="button" className="mobile-update-banner" onClick={()=>window.location.reload()}>A PennyPilot update is ready. Tap to refresh.</button>}</>;
}