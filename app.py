import os
import sqlite3
import random
import datetime
import io
import base64
import pandas as pd

# Grafiklerin arka planda üretilebilmesi için (GUI hatalarını engeller)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, redirect, url_for, flash, send_file

app = Flask(__name__)
# Flash (Uyarı) mesajları için gizli anahtar
app.secret_key = 'smartspend_guvenli_anahtari_123' 

DB_NAME = 'expenses.db'
BUDGET = 10000.0  # Aylık statik bütçe

def get_db_connection():
    """SQLite veritabanı bağlantısını oluşturur."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Veritabanını ve tabloyu oluşturur, eğer boşsa test verisi (Dummy Data) ekler."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tabloyu oluşturma
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount FLOAT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date DATE NOT NULL
        )
    ''')
    
    # Veritabanında veri var mı diye kontrol et
    c.execute('SELECT COUNT(*) FROM expenses')
    count = c.fetchone()[0]
    
    # Veritabanı boşsa otomatik test verisi (Dummy Data) üret
    if count == 0:
        categories = ["Yemek", "Ulaşım", "Eğitim", "Yakıt", "Eğlence", "Diğer"]
        today = datetime.date.today()
        
        for _ in range(30):
            amount = round(random.uniform(50.0, 1500.0), 2)
            category = random.choice(categories)
            description = f"Otomatik oluşturuldu ({category})"
            
            # Son 30 gün içinde rastgele bir tarih belirle
            delta = datetime.timedelta(days=random.randint(0, 30))
            random_date = today - delta
            
            c.execute('''
                INSERT INTO expenses (amount, category, description, date)
                VALUES (?, ?, ?, ?)
            ''', (amount, category, description, random_date.strftime('%Y-%m-%d')))
            
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Ana sayfa: Verileri getirir, Pandas ve Matplotlib analizlerini yapar."""
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT * FROM expenses ORDER BY date DESC', conn)
    conn.close()
    
    # Seçilen ay parametresini al
    selected_month = request.args.get('month', 'ALL')
    
    # Ay listesi oluştur
    available_months = []
    if not df.empty:
        df['month_str'] = df['date'].str[:7]
        unique_months = df['month_str'].unique()
        
        MONTH_NAMES = {
            '01': 'Ocak', '02': 'Şubat', '03': 'Mart', '04': 'Nisan',
            '05': 'Mayıs', '06': 'Haziran', '07': 'Temmuz', '08': 'Ağustos',
            '09': 'Eylül', '10': 'Ekim', '11': 'Kasım', '12': 'Aralık'
        }
        
        for m in sorted(unique_months, reverse=True):
            try:
                y, mon = m.split('-')
                label = f"{MONTH_NAMES.get(mon, mon)} {y}"
            except:
                label = m
            available_months.append({'value': m, 'label': label})
    
        # Filtrele
        if selected_month != 'ALL':
            df = df[df['month_str'] == selected_month]
    
    # Hiç veri yoksa ya da filtrelenmiş veri boşsa güvenle göster
    if df.empty:
        return render_template(
            'index.html', 
            total_spent=0, 
            daily_avg=0,
            transaction_count=0,
            plot_url=None, 
            bar_plot_url=None,
            expenses=[], 
            top_category="Veri Yok", 
            available_months=available_months,
            selected_month=selected_month
        )
        
    # --- PANDAS İLE ANALİZ ---
    total_spent = df['amount'].sum()
    transaction_count = len(df)
    unique_days = df['date'].nunique()
    daily_avg = total_spent / unique_days if unique_days > 0 else 0
    
    # Kategoriye göre harcama toplamını hesapla ve azalan şekilde sırala
    category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)
    top_category = category_totals.index[0] if not category_totals.empty else "Veri Yok"
    
    # --- MATPLOTLIB GÖRSELLEŞTİRME (Pasta) ---
    plt.figure(figsize=(6, 6))
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0', '#ffb3e6']
    
    plt.pie(
        category_totals, 
        labels=category_totals.index, 
        autopct='%1.1f%%', 
        startangle=140,
        colors=colors,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
    )
    title_prefix = "Tüm Zamanlar" if selected_month == 'ALL' else selected_month
    plt.title(f'{title_prefix} Kategori Dağılımı', fontsize=14, fontweight='bold', pad=15)
    plt.axis('equal')
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', transparent=True)
    img_buffer.seek(0)
    plot_url = base64.b64encode(img_buffer.getvalue()).decode('utf8')
    plt.clf()
    plt.close()
    
    # --- MATPLOTLIB GÖRSELLEŞTİRME (Sütun/Bar) ---
    plt.figure(figsize=(9, 4.5))
    if selected_month == 'ALL':
        # Aylara göre göster
        timeline_df = df.groupby('month_str')['amount'].sum().sort_index()
        
        # Eksen Formatlama Örn: "2026-04" -> "Nis '26"
        def format_month_tick(m_str):
            try:
                y, m = m_str.split('-')
                short_months = {'01':'Oca','02':'Şub','03':'Mar','04':'Nis','05':'May','06':'Haz','07':'Tem','08':'Ağu','09':'Eyl','10':'Eki','11':'Kas','12':'Ara'}
                return f"{short_months.get(m, m)} '{y[-2:]}"
            except:
                return m_str
                
        ticks = [format_month_tick(m) for m in timeline_df.index]
        
        # En çok harcanan ayı Kırmızı yap diğerlerini Mavi yap
        colors_bar = []
        if not timeline_df.empty:
            max_val = timeline_df.max()
            colors_bar = ['#ff6b6b' if val == max_val else '#4dabf7' for val in timeline_df.values]
            
        bars = plt.bar(ticks, timeline_df.values, color=colors_bar, edgecolor='white', width=0.6, alpha=0.9)
        plt.title('Aylar Bazında Harcama Gidişatı', fontsize=13, fontweight='bold', pad=15)
        plt.xlabel('Dönemler', fontsize=10, color='#666')
        plt.xticks(rotation=45)
        
        # Ortalama Çizgi
        if not timeline_df.empty:
            avg_line = timeline_df.mean()
            plt.axhline(avg_line, color='#fcc419', linestyle='dashed', linewidth=2, label=f'Ortalama: {int(avg_line)} ₺')
            plt.legend(loc='upper right', fontsize=9, framealpha=0.8)
            
    else:
        # Günlere göre göster
        df['day'] = df['date'].str[-2:].astype(int)
        timeline_df = df.groupby('day')['amount'].sum().sort_index()
        
        ticks = [str(d) for d in timeline_df.index]
        
        # En çok harcanan günü Kırmızı diğerlerini Yeşil yap
        colors_bar = []
        if not timeline_df.empty:
            max_val = timeline_df.max()
            colors_bar = ['#ff6b6b' if val == max_val else '#40c057' for val in timeline_df.values]
            
        bars = plt.bar(ticks, timeline_df.values, color=colors_bar, edgecolor='white', width=0.6, alpha=0.9)
        plt.title(f'{selected_month} - Günlük Harcama Yoğunluğu', fontsize=13, fontweight='bold', pad=15)
        plt.xlabel('Ayın Günleri', fontsize=10, color='#666')
        
        # Ortalama Çizgi
        if not timeline_df.empty:
            avg_line = timeline_df.mean()
            plt.axhline(avg_line, color='#fcc419', linestyle='dashed', linewidth=2, label=f'Ortalama: {int(avg_line)} ₺')
            plt.legend(loc='upper right', fontsize=9, framealpha=0.8)
        
    plt.ylabel('Tutar (₺)', fontsize=10, color='#666')
    
    # Gereksiz çizgileri yok et
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.grid(axis='y', linestyle='--', alpha=0.4)
    
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            plt.text(bar.get_x() + bar.get_width()/2., height + (height * 0.02),
                     f'{int(height)} ₺',
                     ha='center', va='bottom', fontsize=8, color='#333', fontweight='600')
                     
    bar_buffer = io.BytesIO()
    plt.savefig(bar_buffer, format='png', bbox_inches='tight', transparent=True)
    bar_buffer.seek(0)
    bar_plot_url = base64.b64encode(bar_buffer.getvalue()).decode('utf8')
    plt.clf()
    plt.close()
    
    # DataFrame'i Jinja'nın okuyabileceği dict listesine dönüştür
    expenses_list = df.to_dict('records')
    
    return render_template(
        'index.html',
        total_spent=round(total_spent, 2),
        daily_avg=round(daily_avg, 2),
        transaction_count=transaction_count,
        plot_url=plot_url,
        bar_plot_url=bar_plot_url,
        expenses=expenses_list,
        top_category=top_category,
        available_months=available_months,
        selected_month=selected_month
    )

@app.route('/add', methods=['POST'])
def add_expense():
    """Yeni harcamayı veritabanına ekler (Backend Validasyonu İçerir)."""
    amount_str = request.form.get('amount')
    category = request.form.get('category')
    description = request.form.get('description', '')
    date_str = request.form.get('date')
    
    # 1. Validasyon: Miktar Kontrolü
    try:
        amount = float(amount_str)
        if amount <= 0:
            flash("Dikkat: Miktar 0'dan büyük olmalıdır!", "danger")
            return redirect(url_for('index'))
    except (ValueError, TypeError):
        flash("Dikkat: Geçersiz bir miktar girdiniz!", "danger")
        return redirect(url_for('index'))
        
    # 2. Validasyon: Boş Alan Kontrolü
    if not category or not date_str:
        flash("Dikkat: Kategori ve Tarih alanları boş bırakılamaz!", "danger")
        return redirect(url_for('index'))
        
    # 3. Validasyon: Tarih Formatı (YYYY-MM-DD)
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        flash("Dikkat: Lütfen sistemin desteklediği formattan (YYYY-MM-DD) şaşmayın.", "danger")
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO expenses (amount, category, description, date)
        VALUES (?, ?, ?, ?)
    ''', (amount, category, description, date_str))
    conn.commit()
    conn.close()
    
    flash("Süper! Harcama başarıyla eklendi.", "success")
    return redirect(url_for('index'))

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_expense(item_id):
    """Gelen id'ye ait harcamayı siler."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    
    flash("Harcama sistemden başarıyla silindi.", "success")
    return redirect(url_for('index'))

@app.route('/export')
def export_csv():
    """Tüm verileri Pandas aracılığıyla CSV belleğine alarak indirmeye sunar."""
    selected_month = request.args.get('month', 'ALL')
    
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT date, category, description, amount FROM expenses ORDER BY date DESC', conn)
    conn.close()
    
    if selected_month != 'ALL':
        df['month_str'] = df['date'].str[:7]
        df = df[df['month_str'] == selected_month]
        df.drop(columns=['month_str'], inplace=True, errors='ignore')
    
    # Sütun isimlerini çeviriyoruz
    df.rename(columns={'date': 'Tarih', 'category': 'Kategori', 'description': 'Açıklama', 'amount': 'Miktar (TL)'}, inplace=True)
    
    # Disk yerine bellekte tutarak (BytesIO) dosyayı oluşturuyoruz
    csv_buffer = io.BytesIO()
    # TR karakter bozulmaması için utf-8-sig
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig', sep=';')
    csv_buffer.seek(0)
    
    filename = f'smartspend_harcamalar_{selected_month}.csv' if selected_month != 'ALL' else 'smartspend_harcamalar_tum_zamanlar.csv'
    
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

# 1. Gunicorn gibi canlı sunucularda çalışırken veritabanı kurulduğundan emin ol
with app.app_context():
    try:
        init_db()
    except Exception as e:
        print("Veritabanı başlatma hatası:", e)

if __name__ == '__main__':
    # 2. Flask'i başlat (Sadece lokal test için)
    app.run(debug=True)
