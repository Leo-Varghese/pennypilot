import type {Metadata} from "next";
import "./globals.css";
import {MobileAppSupport} from "@/components/mobile-app-support";
export const metadata:Metadata={title:"PennyPilot | Your money, with direction",description:"Private personal finance, budgets and savings goals."};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}<MobileAppSupport/></body></html>}
