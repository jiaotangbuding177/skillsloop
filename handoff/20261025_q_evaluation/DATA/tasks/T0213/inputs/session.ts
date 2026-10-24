export function list(rows:any[]){return {items:rows.slice(0,50),nextCursor:rows.at(-1)?.id??null};}
