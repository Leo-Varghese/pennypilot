"use client";
import * as Dialog from "@radix-ui/react-dialog";
import {X} from "lucide-react";
import {ReactNode} from "react";
export function Modal({title,children,onClose}:{title:string;children:ReactNode;onClose:()=>void}){return <Dialog.Root open onOpenChange={v=>!v&&onClose()}><Dialog.Portal><Dialog.Overlay className="overlay"/><Dialog.Content className="modal"><div className="row between"><Dialog.Title>{title}</Dialog.Title><Dialog.Close className="icon" aria-label="Close"><X size={20}/></Dialog.Close></div><Dialog.Description className="muted">Changes are saved securely to your account.</Dialog.Description>{children}</Dialog.Content></Dialog.Portal></Dialog.Root>}
export function Field({label,children}:{label:string;children:ReactNode}){return <label className="field"><span>{label}</span>{children}</label>}
export function Empty({text="No records yet. Add your first record to get started."}:{text?:string}){return <p className="empty">{text}</p>}
export function Progress({value}:{value:number}){return <progress aria-label="Progress" max={100} value={Math.min(100,Math.max(0,value))}/>}
