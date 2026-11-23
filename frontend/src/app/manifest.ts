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
  background_color:"#f3f7f4",
  theme_color:"#0f806b",
  categories:["finance","productivity"],
  prefer_related_applications:false,
  icons:[
   {src:"/pennypilot-app-icon.svg",sizes:"192x192",type:"image/svg+xml",purpose:"any"},
   {src:"/pennypilot-app-icon.svg",sizes:"512x512",type:"image/svg+xml",purpose:"maskable"},
  ],
 };
}