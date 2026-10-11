# Lablar

| Hafta | İçerik | Kurulum ve kullanım |
|:---:|---|---|
| 2 | SQL injection, command injection, path traversal; argument injection, SSTI, XXE ve NoSQL ek örnekleri | [Web labı](hafta02/README.md) · [Kodlar](hafta02/) |
| 4 | Dört rakamlı PIN'e brute force ve hata sayfasından key sızıntısı | [Kripto labı](hafta04/README.md) · [Hazır çözümler](hafta04/cozum.py) |

Python 3.10+ kullanın. Komutları depo kökünde çalıştırın; açık terminal sunucuyu çalışır tutar.

## Hafta 2

```powershell
python -m pip install -r lablar/hafta02/requirements.txt
python -X utf8 lablar/hafta02/app.py
```

Tarayıcıda http://127.0.0.1:5023 adresini açın. Normal ve exploit girdilerini aynı ekranda deneyip hatalı/düzeltilmiş sürümleri karşılaştırın. Command ve argument örnekleri için Git'in PATH üzerinde bulunması gerekir.

## Hafta 4

```powershell
python -m pip install -r lablar/hafta04/requirements.txt
python -X utf8 lablar/hafta04/lab.py
```

Tarayıcıda http://127.0.0.1:8084 adresini açın. Akış: paketi incele → PIN adaylarını veya hata yanıtını göster → notu aç → çözümü açıkla. Bütün işlemler hazır düğmelerle çalışır; derste kod yazılmaz. İki lab da AAD kullanmadan, nonce ve ciphertext/tag ile çalışır. Açıklamalı çözümler labın son adımındadır.

Düzeltilmiş sürümü karşılaştırmak için ikinci terminalde `python -X utf8 lablar/hafta04/lab.py --fixed --port 8085` çalıştırıp http://127.0.0.1:8085 adresini açın.

[Ders ana sayfasına dön](../README.md)
