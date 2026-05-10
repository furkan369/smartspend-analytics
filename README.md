# SmartSpend - Harcama Takip ve Analiz Uygulaması

SmartSpend, kişisel harcamalarınızı takip etmenizi, yönetmenizi ve görselleştirerek analiz etmenizi sağlayan basit ve kullanışlı bir web tabanlı Python uygulamasıdır. Bu proje, veri bilimi ve web programlama temel kavramlarını (Flask, Pandas, Matplotlib) bir araya getirmek amacıyla  geliştirilmiştir.

## Özellikler

- **Harcama Ekleme/Silme:** Miktar, kategori, tarih ve açıklama bilgileriyle yeni harcamalar ekleyebilir ve silebilirsiniz.
- **Veri Görselleştirme:** Matplotlib kullanılarak harcamalarınız pasta grafiği (kategori dağılımı) ve sütun grafiği (günlük/aylık harcama yoğunluğu) ile görselleştirilir.
- **Aylık Filtreleme:** İsteğinize göre tüm zamanların verisini veya sadece belirli bir ayın verilerini listeleyip analiz edebilirsiniz.
- **CSV Olarak Dışa Aktarma:** Pandas kütüphanesi sayesinde harcama verilerinizi tek tıkla Excel veya benzeri programlarda açabileceğiniz `.csv` formatında indirebilirsiniz.


## Kullanılan Teknolojiler

- **Backend:** Python, Flask
- **Veri Analizi ve Görselleştirme:** Pandas, Matplotlib
- **Veritabanı:** SQLite (Veriler `expenses.db` adlı yerel dosyada saklanır)
- **Frontend:** HTML, CSS (Jinja2 Template Engine ile entegre)


## Proje Hakkında Notlar
Bu proje  Flask yapısını, SQLite ile veritabanı işlemlerini ve Pandas/Matplotlib ile veri analizini uygulamalı olarak göstermeyi amaçlamaktadır. 
