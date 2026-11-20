// 与后端 src/services/sampling.py 完全同构的整数复算：按公布的原起点重算必抽、逐笔精确概率与抽中集合。
const B=BigInt;
export function recompute(items,sampleSize,randomStart){
 const amounts=items.map(it=>B(it.amount_cents)),n=B(sampleSize);
 const pi=amounts.map(()=>[0n,1n]);let pool=amounts.map((a,i)=>a>0n?i:-1).filter(i=>i>=0),slots=n;
 const certainty=new Set();
 while(slots>0n){
  const total=pool.reduce((s,i)=>s+amounts[i],0n),cert=pool.filter(i=>slots*amounts[i]>=total);
  if(!cert.length){for(const i of pool)pi[i]=[slots*amounts[i],total];break}
  for(const i of cert){pi[i]=[1n,1n];certainty.add(i)}
  pool=pool.filter(i=>!certainty.has(i));slots-=B(cert.length);
 }
 const total=pool.reduce((s,i)=>s+amounts[i],0n),selected=new Set(certainty);
 if(slots>0n){
  const lows=[];let acc=0n;
  for(const i of pool){lows.push([acc,i]);acc+=slots*amounts[i]}
  for(let k=0n;k<slots;k++){
   const point=B(randomStart)+k*total;let lo=0,hi=lows.length-1,ans=0;
   while(lo<=hi){const mid=(lo+hi)>>1;if(lows[mid][0]<=point){ans=mid;lo=mid+1}else hi=mid-1}
   selected.add(lows[ans][1]);
  }
 }
 const mismatches=[];
 if(selected.size!==Number(n))mismatches.push(`抽中数${selected.size}≠名额${n}`);
 items.forEach((it,i)=>{
  const[pn,pd]=pi[i];
  if(pn*B(it.pi_den)!==B(it.pi_num)*pd)mismatches.push(`第${it.seq}笔精确概率不符`);
  if(!!it.certainty!==(pn>0n&&pn===pd))mismatches.push(`第${it.seq}笔必抽标记不符`);
  if(!!it.selected!==selected.has(i))mismatches.push(`第${it.seq}笔抽中标记不符`);
 });
 return{ok:!mismatches.length,mismatches};
}
export const pct=(num,den)=>{const bp=B(num)*10000n/B(den);return `${bp/100n}.${String(bp%100n).padStart(2,'0')}%`};
