from fastapi import APIRouter,Depends
from src.config.database import database
from src.controllers.auth import current,admin
from src.models.sampling import SamplePlan
from src.schemas.requests import SampleInput
from src.services.sampling import lock_and_draw
from src.utils.serialize import row
router=APIRouter()
@router.get('/samplings')
def samplings(db=Depends(database),u=Depends(current)): return [row(x) for x in db.query(SamplePlan).order_by(SamplePlan.id.desc()).all()]
@router.post('/runs/{id}/sampling')
def draw(id:int,b:SampleInput,db=Depends(database),u=Depends(admin)):
 plan,reused=lock_and_draw(db,u,id,b.sample_size)
 out=row(plan);out['reused']=reused
 return out
