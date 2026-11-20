import {heading} from '../components/common/header.js';import {table} from '../components/common/table.js';import {esc,fmt,time} from '../utils/format.js';import {recompute,pct} from '../utils/sampling.js';
export function sampling(c,d,selected){
 const approved=d.runs.filter(r=>r.approved&&r.status==='completed');
 const run=approved.find(r=>r.id===selected)||approved[0];
 const plan=run?d.samplings.find(p=>p.run_id===run.id):null;
 const legacy=run&&!run.snapshot.voucher_keys;
 let main='<p class="empty">暂无已复核的已完成报告。请先在“核算与复核”完成复核。</p>';
 if(run){
  const form=plan?'':`<form id="sampling-form" class="inline-form" data-id="${run.id}"><label>样本名额（1–${Math.max(1,(run.snapshot.sources||[]).filter(s=>s.amount_cents>0).length)}）<input name="sample_size" type="number" min="1" value="5" required></label><button>锁定名额与起点并抽查</button></form>${legacy?'<p class="warning">该报告为旧格式快照，缺少凭证身份（voucher_keys），无法对应原凭证，提交将被拒抽；请重新核算生成含凭证身份的快照。</p>':''}`;
  let result='';
  if(plan&&plan.result){
   const r=plan.result,check=recompute(r.items,r.sample_size,r.random_start);
   result=`<div class="metrics">${[['固定名额',r.sample_size],['系统随机起点',r.random_start],['必抽（概率=1）',r.certainty_count],['非必抽池总额（分）',r.pool_total_cents],['剩余名额',r.pool_slots],['抽中合计',r.selected_count]].map(([k,v])=>`<div><small>${k}</small><strong>${fmt(v)}</strong></div>`).join('')}</div><p class="method">${esc(r.method)}</p><p class="${check.ok?'checksum':'error'}">页面按原起点复算：${check.ok?'一致 ✓（必抽、逐笔精确概率与抽中集合全部吻合）':'不一致 ✗ '+esc(check.mismatches.join('；'))}</p><p>快照SHA256 ${esc(r.snapshot_sha256)} · 锁定人 ${esc(plan.created_by)} ${time(plan.created)} · 发布 ${esc(r.published_by)} ${time(r.published_at)}</p>${table(r.items.map(it=>({序号:it.seq,凭证:it.voucher,期间:it.period,部门:it.department,费用类别:it.category,'金额（分）':it.amount_cents,精确概率:it.pi_num+'/'+it.pi_den,'概率%':pct(it.pi_num,it.pi_den),属性:it.certainty?'必抽':(it.amount_cents>0?'参与随机':'零元不抽'),抽中:it.selected?'✓':''})))}`;
  }else if(plan){result=`<p class="warning">名额与起点已锁定（名额${plan.sample_size}，起点${plan.random_start}），结果待发布；刷新或重新提交将沿用原起点补发。</p>`}
  main=`<h2>${esc(run.name)}</h2><p>口径 ${esc(run.snapshot.policy.version)} · 凭证 ${run.snapshot.sources.length} 笔 · 复核说明：${esc(run.review||'—')}</p>${form}${result}`;
 }
 return heading('AUDIT SAMPLING / 05','月结抽查','按已复核报告冻结快照抽原凭证；公共费拆到几个部门也只算一笔。名额固定、概率与金额成比例、达一必抽、零元不抽；起点只锁一次，样本与逐笔精确概率一起发布。')+`<div class="run-layout"><aside class="run-list">${approved.map(r=>`<button class="select-run" data-id="${r.id}">${esc(r.name)} ${d.samplings.some(p=>p.run_id===r.id)?'已抽查':''}</button>`).join('')||'<p class="empty">无已复核报告</p>'}</aside><div>${main}</div></div>`;
}
