import sys
import io
from sqlmodel import Session, select, func
from app.core.database import engine
from app.models.property import Property

# 强制设置输出编码为 UTF-8，防止 Windows 报错
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with Session(engine) as session:
    count = session.exec(select(func.count(Property.id))).one()
    suburbs = session.exec(select(Property.suburb).distinct()).all()
    
    print("-" * 30)
    print(f"Total listings in DB: {count}")
    print(f"Suburbs covered: {suburbs}")
    print("-" * 30)