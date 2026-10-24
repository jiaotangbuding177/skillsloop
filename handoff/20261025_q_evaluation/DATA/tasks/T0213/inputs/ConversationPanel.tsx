import {useEffect, useRef, useState} from 'react';
export function ConversationPanel({id}:{id:string}) {
 const loaded=useRef<string|null>(null); const [messages,setMessages]=useState<string[]>([]);
 useEffect(()=>{if(loaded.current===id)return;loaded.current=id;
   fetch('/sessions/'+id).then(r=>r.json()).then(x=>setMessages(x.items));},[id]);
 return <ul>{messages.map((x,i)=><li key={i}>{x}</li>)}</ul>;
}
