from sqlalchemy import text
from load_data import engine # ajuste se o nome do seu arquivo for diferente

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.fetchall())
