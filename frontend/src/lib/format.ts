import {formatInTimeZone} from "date-fns-tz";
export function money(value:string|number|null|undefined,currency="INR"){ return value==null?"Not available":new Intl.NumberFormat("en-IN",{style:"currency",currency,maximumFractionDigits:2}).format(Number(value)); }
export function day(value:string,zone="Asia/Kolkata"){try{return formatInTimeZone(value.length===10?`${value}T12:00:00Z`:value,zone,"dd MMM yyyy");}catch{return value;}}
