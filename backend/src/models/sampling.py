from sqlalchemy import Column,Integer,BigInteger,String,JSON,Float
from src.config.database import Base
class SamplePlan(Base):
 __tablename__='sample_plans'
 id=Column(Integer,primary_key=True)
 run_id=Column(Integer,unique=True,nullable=False)  # 每份报告只锁一份名额与起点
 sample_size=Column(Integer,nullable=False)  # 锁定的固定名额
 random_start=Column(BigInteger,nullable=False)  # 锁定的系统随机起点（整数分，放大轴）
 pool_slots=Column(Integer,nullable=False)  # 扣除必抽后的剩余名额
 pool_total_cents=Column(BigInteger,nullable=False)  # 扣除必抽后的池内总额（分）
 status=Column(String(20),nullable=False)  # locked / published
 result=Column(JSON)  # 发布后写入样本与逐笔精确概率
 created=Column(Float); published_at=Column(Float); created_by=Column(String(120))
