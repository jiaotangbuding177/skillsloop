export function install(refresh:()=>void){document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")refresh();});}
