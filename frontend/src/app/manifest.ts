import type {MetadataRoute} from "next";

export default function manifest():MetadataRoute.Manifest{
 return {
  id:"/",
  name:"PennyPilot Personal Finance",
  short_name:"PennyPilot",
  description:"Track transactions, budgets, savings goals, planned purchases, analytics, and AI-assisted financial explanations.",
  start_url:"/",
  scope:"/",
  display:"standalone",
  orientation:"any",
  background_color:"#ffffff",
  theme_color:"#0f806b",
  categories:["finance","productivity"],
  prefer_related_applications:false,
  icons:[
   {src:"/icons/pennypilot-192.png",sizes:"192x192",type:"image/png",purpose:"any"},
   {src:"/icons/pennypilot-512.png",sizes:"512x512",type:"image/png",purpose:"any"},
   {src:"/icons/pennypilot-512.png",sizes:"512x512",type:"image/png",purpose:"maskable"},
  ],
 };
}