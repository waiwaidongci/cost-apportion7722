import secrets,time
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from src.models.run import Run
from src.models.sampling import SamplePlan
from src.services.audit import log
from src.services.pps import METHOD,pps_plan,pps_draw
def _checked(run):
 if not run: raise HTTPException(404,'报告不存在')
 if run.status!='completed' or not run.approved: raise HTTPException(409,'月结抽查仅面向已复核的已完成报告')
 snap=run.snapshot or {}
 keys=snap.get('voucher_keys');sources=snap.get('sources') or []
 if not keys or len(keys)!=len(sources) or any(not isinstance(k,str) or not k for k in keys):
  raise HTTPException(422,'该报告为旧格式快照，缺少凭证身份（voucher_keys），无法对应原凭证，已拒抽；请重新核算生成含凭证身份的快照后再抽查')
 return keys,sources
def lock_and_draw(db,user,run_id,sample_size):
 """抽前只锁一次名额和系统随机起点；并发沿用先锁的一份；崩溃恢复沿用原起点；重跑不重复发布。"""
 run=db.get(Run,run_id)
 keys,sources=_checked(run)
 amounts=[int(s['amount_cents']) for s in sources]
 plan=db.query(SamplePlan).filter_by(run_id=run_id).first()
 reused=plan is not None
 if plan is None:
  pi=pps_plan(amounts,sample_size)  # 名额合法性在此校验（ValueError→422）
  slots=sample_size-sum(1 for p in pi if p==1)
  total=sum(amounts[i] for i,p in enumerate(pi) if 0<p<1)
  plan=SamplePlan(run_id=run_id,sample_size=sample_size,pool_slots=slots,pool_total_cents=total,random_start=secrets.randbelow(total) if total else 0,status='locked',created=time.time(),created_by=user.email)
  db.add(plan);log(db,user.email,'sampling.lock',f'报告{run_id} 名额{sample_size}')
  try: db.commit()
  except IntegrityError:  # 并发申请：沿用先锁的一份
   db.rollback();plan=db.query(SamplePlan).filter_by(run_id=run_id).first();reused=True
 if plan.status!='published':
  pi,selected,slots,total=pps_draw(amounts,plan.sample_size,plan.random_start)  # 崩溃恢复沿用原起点
  assert len(selected)==plan.sample_size
  items=[{'seq':i+1,'voucher':keys[i],'period':s['period'],'department':s['department'],'category':s['category'],'amount_cents':amounts[i],'pi_num':pi[i].numerator,'pi_den':pi[i].denominator,'certainty':pi[i]==1,'selected':i in selected} for i,s in enumerate(sources)]
  plan.result={'method':METHOD,'run_id':run_id,'run_name':run.name,'snapshot_sha256':run.checksum,'sample_size':plan.sample_size,'random_start':plan.random_start,'eligible_count':sum(1 for x in amounts if x>0),'eligible_total_cents':sum(amounts),'certainty_count':sum(1 for p in pi if p==1),'pool_slots':slots,'pool_total_cents':total,'selected_count':len(selected),'items':items,'published_by':user.email,'published_at':time.time()}
  plan.status='published';plan.published_at=plan.result['published_at']
  log(db,user.email,'sampling.publish',f'报告{run_id} 起点{plan.random_start}')
  db.commit()
 return plan,reused
