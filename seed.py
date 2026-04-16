import sqlite3
import random
import datetime

DB_NAME = 'expenses.db'
categories = ["Yemek", "Ulaşım", "Eğitim", "Yakıt", "Eğlence", "Diğer"]
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

today = datetime.date.today()

# Önceki 12 aya (365 güne) yayılan 100 yeni kayıt oluştur
for _ in range(150):
    amount = round(random.uniform(50.0, 1500.0), 2)
    category = random.choice(categories)
    description = f"Geçmiş Dönem Otomatik ({category})"
    
    # 0 ile 365 gün arası rastgele geriye git
    delta = datetime.timedelta(days=random.randint(0, 365))
    random_date = today - delta
    
    c.execute('''
        INSERT INTO expenses (amount, category, description, date)
        VALUES (?, ?, ?, ?)
    ''', (amount, category, description, random_date.strftime('%Y-%m-%d')))
    
conn.commit()
conn.close()
print("150 adet yepyeni veri tüm aylara eklendi.")
