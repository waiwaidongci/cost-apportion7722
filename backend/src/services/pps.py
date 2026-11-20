import bisect
from fractions import Fraction
METHOD='月结抽查按已复核报告冻结快照抽原凭证，公共费拆到几个部门也只算一笔。样本名额固定，入选概率=剩余名额×凭证原金额÷池内总额；概率达到一的先列为必抽，再按余款和剩余名额重算，零元不抽。非必抽池把金额轴放大剩余名额倍，抽样区间恰为池总额整数分，系统随机起点在[0,池总额)内只锁一次；抽点=起点+k×池总额，命中区间即抽中，逐笔概率精确等于剩余名额×金额÷池总额，页面可按原起点复算。'
def pps_plan(amounts,n):
 """逐笔精确入选概率（Fraction）。amounts为整数分，n为固定名额；零元概率为0。"""
 eligible=[i for i,x in enumerate(amounts) if x>0]
 if not eligible: raise ValueError('报告内没有金额大于零的凭证，零元不抽，无法抽查')
 if isinstance(n,bool) or not isinstance(n,int) or not 1<=n<=len(eligible): raise ValueError(f'样本名额须为1到{len(eligible)}的整数（金额大于零的凭证数），零元不抽')
 pi=[Fraction(0) for _ in amounts];pool=eligible[:];slots=n
 while slots:
  total=sum(amounts[i] for i in pool)
  certain=[i for i in pool if slots*amounts[i]>=total]
  if not certain:
   for i in pool: pi[i]=Fraction(slots*amounts[i],total)
   return pi
  for i in certain: pi[i]=Fraction(1)  # 概率达到一的先列为必抽
  pool=[i for i in pool if i not in certain];slots-=len(certain)  # 按余款和剩余名额重算
 return pi
def pps_draw(amounts,n,start):
 """按锁定起点确定性系统抽样，返回(逐笔概率,抽中集合,剩余名额,池总额)。"""
 pi=pps_plan(amounts,n)
 pool=[i for i,p in enumerate(pi) if 0<p<1]
 slots=n-sum(1 for p in pi if p==1)
 total=sum(amounts[i] for i in pool)
 selected={i for i,p in enumerate(pi) if p==1}
 if slots:
  if isinstance(start,bool) or not isinstance(start,int) or not 0<=start<total: raise ValueError('随机起点越界')
  lows=[];acc=0
  for i in pool: lows.append(acc);acc+=slots*amounts[i]  # 放大slots倍的累计金额轴，区间=池总额整数分
  for k in range(slots): selected.add(pool[bisect.bisect_right(lows,start+k*total)-1])
 return pi,selected,slots,total
