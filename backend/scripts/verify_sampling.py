"""月结抽查核对：小账穷举起点核对逐笔精确概率；并核对锁定幂等、并发沿用、崩溃恢复与旧报告拒抽。
用法：docker compose exec -T backend python -m scripts.verify_sampling"""
import random,threading,time,types
from fractions import Fraction
from src.services.pps import pps_plan,pps_draw

def enumerate_case(amounts,n):
 """对全部整数起点穷举，核对每笔抽中频率==公布的精确概率；零元从不抽中；每次抽中数==名额。"""
 pi=pps_plan(amounts,n)
 assert sum(pi)==n,f'概率守恒失败: {amounts} n={n}'
 _,selected,slots,total=pps_draw(amounts,n,0)
 assert len(selected)==n,f'抽中数不等于固定名额: {amounts} n={n}'
 if total==0:  # 全部必抽，无随机起点空间
  assert selected=={i for i,p in enumerate(pi) if p==1}
  return total
 counts=[0]*len(amounts)
 for start in range(total):
  _,selected,s2,t2=pps_draw(amounts,n,start)
  assert (s2,t2)==(slots,total) and len(selected)==n,f'抽中数不等于固定名额: {amounts} n={n} 起点{start}'
  for i in selected: counts[i]+=1
 for i,x in enumerate(amounts):
  got=Fraction(counts[i],total) if total else Fraction(0)
  assert got==pi[i],f'穷举不符: {amounts} n={n} 第{i+1}笔 穷举{got} 公布{pi[i]}'
  if x==0: assert counts[i]==0,'零元被抽中'
 return total

def check_algorithm():
 fixed=[([1,2,3,4,10],2),([0,5,0,5],1),([0,0,7],1),([1000,10,10,10],2),([6,6,6,1],2),([5,5,4],3),([3,1,1,1,1,1],3),([9,1,1],2)]
 for amounts,n in fixed: enumerate_case(amounts,n)
 rng=random.Random(7)
 for _ in range(60):
  amounts=[rng.randint(0,9) for _ in range(rng.randint(2,8))]
  if not any(amounts): amounts[rng.randrange(len(amounts))]=1
  enumerate_case(amounts,rng.randint(1,sum(1 for x in amounts if x>0)))
 big=[random.Random(42).randint(1000,500000) for _ in range(240)]
 pi,selected,_,_=pps_draw(big,10,123456)
 assert sum(pi)==10 and len(selected)==10
 assert pps_draw(big,10,123456)[1]==selected,'同起点重跑结果不一致'
 print(f'算法核对通过：8组固定小账+60组随机小账已穷举全部起点，逐笔频率==精确概率；240笔大账守恒与确定性通过')

def check_service():
 from src.config.database import Session
 from src.models.run import Run
 from src.models.sampling import SamplePlan
 from src.models.identity import Audit
 from src.services.sampling import lock_and_draw
 user=types.SimpleNamespace(email='verify@local');stamp=str(time.time())
 legacy=Run(name='verify-legacy-'+stamp,status='completed',approved=True,review='核对用旧报告',created=time.time(),checksum='a'*64,result=None,snapshot={'policy':{'version':'v','weights':{'甲':1}},'sources':[{'period':'2026-10','department':'公共','category':'耗材','amount_cents':100}],'period':'2026-10'})
 fresh=Run(name='verify-fresh-'+stamp,status='completed',approved=True,review='核对用新报告',created=time.time(),checksum='b'*64,result=None,snapshot={'policy':{'version':'v','weights':{'甲':1}},'sources':[{'period':'2026-10','department':'公共','category':'耗材','amount_cents':a} for a in (0,5,5,10,80)],'voucher_keys':['v0','v1','v2','v3','v4'],'period':'2026-10'})
 with Session() as db:
  db.add(legacy);db.add(fresh);db.commit();lid,fid=legacy.id,fresh.id
  try:
   try:
    lock_and_draw(db,user,lid,1);raise AssertionError('旧报告未拒抽')
   except Exception as exc:
    assert '凭证身份' in str(getattr(exc,'detail',exc)),'拒抽未说明原因'
   errors=[];locked=[]
   def work(k):
    try:
     with Session() as s: locked.append(lock_and_draw(s,user,fid,2+k%3)[0])
    except Exception as e: errors.append(e)
   ts=[threading.Thread(target=work,args=(k,)) for k in range(8)]
   for t in ts: t.start()
   for t in ts: t.join()
   assert not errors,errors
   plans=db.query(SamplePlan).filter_by(run_id=fid).all()
   assert len(plans)==1,'并发申请出现多份锁定'
   plan=plans[0]
   assert all(p.id==plan.id and p.random_start==plan.random_start and p.sample_size==plan.sample_size for p in locked),'并发未沿用先锁的一份'
   saved=plan.result
   assert plan.status=='published' and saved['selected_count']==plan.sample_size
   again,reused=lock_and_draw(db,user,fid,99)  # 重跑且名额不同：沿用先锁，不重复发布
   assert reused and again.id==plan.id and again.result==saved,'重跑未沿用已发布结果'
   plan.status='locked';plan.result=None;plan.published_at=None;db.commit()  # 模拟锁定后崩溃
   recovered,_=lock_and_draw(db,user,fid,plan.sample_size)
   assert recovered.random_start==plan.random_start,'崩溃恢复未沿用原起点'
   assert recovered.result['items']==saved['items'],'崩溃恢复样本不一致'
   print(f'服务核对通过：旧报告拒抽并说明原因；8线程并发只锁一份；重跑不重复发布；崩溃恢复沿用原起点（名额{plan.sample_size}，起点{plan.random_start}）')
  finally:
   for a in db.query(Audit).filter(Audit.detail.contains('报告'+str(fid))).all(): db.delete(a)
   db.query(SamplePlan).filter_by(run_id=fid).delete()
   db.delete(db.get(Run,lid));db.delete(db.get(Run,fid));db.commit()

if __name__=='__main__':
 check_algorithm();check_service();print('全部核对通过')
