
# YouTube Ultra Downloader v2.1

YouTube'dan playlist ve video indirmek için gelişmiş bir GUI uygulaması.

## Özellikler

- Playlist desteği (tüm videoları otomatik algılar)
- Paralel indirme (1-50 thread)
- MP4, MP3 ve WAV format desteği
- Gerçek zamanlı ilerleme takibi
- Karanlık/Açık tema desteği
- Otomatik ses bildirimi
- Durdurma/Duraklatma özellikleri
- Detaylı log sistemi
- Otomatik ffmpeg ve yt-dlp kurulumu

## Sistem Gereksinimleri

- Python 3.6 veya üzeri
- İnternet bağlantısı (indirme ve yt-dlp güncelleme için)
- Windows, Linux veya macOS

## Kurulum

### Windows

1. **Python kurulumu** (eğer yoksa):
   - [Python.org](https://www.python.org/downloads/) adresinden Python 3.x indirin
   - Kurulum sırasında "Add Python to PATH" seçeneğini işaretleyin

2. **Programı indirin**:
   - Bu repository'yi ZIP olarak indirin veya klonlayın
   - Dosyaları bir klasöre çıkarın

3. **Bağımlılıkları kontrol edin**:
   - Program otomatik olarak yt-dlp ve ffmpeg'i kuracaktır
   - Manuel kurulum için:
     - [yt-dlp](https://github.com/yt-dlp/yt-dlp) indirip program klasörüne koyun
     - [ffmpeg](https://ffmpeg.org/download.html) indirip sistem PATH'ine ekleyin

4. **Programı çalıştırın**:
   - `full_youtube_playlist_installer.py` dosyasına çift tıklayın
   - Veya komut satırından: `python full_youtube_playlist_installer.py`

### Linux (Ubuntu/Debian)

1. **Python ve Tkinter kurulumu**:
```bash
sudo apt update
sudo apt install python3 python3-tk python3-pip -y
```

1. Programı indirin:

```bash
git clone https://github.com/n4dlr/Youtube-PlayList-Installer
cd Youtube-PlayList-Installer
```

1. Gerekli araçları kurun (program otomatik kurar, manuel için):

```bash
sudo apt install ffmpeg yt-dlp -y
```

1. Çalıştırma izinleri verin:

```bash
chmod +x full_youtube_playlist_installer.py
```

1. Programı çalıştırın:

```bash
python3 full_youtube_playlist_installer.py
```

Diğer Linux Dağıtımları

· Fedora/RHEL:

```bash
sudo dnf install python3 tkinter ffmpeg yt-dlp
```

· Arch Linux:

```bash
sudo pacman -S python tk ffmpeg yt-dlp
```

Kullanım

1. Programı başlatın
2. YouTube playlist veya video linkini yapıştırın
3. İndirme formatını seçin (MP4, MP3, WAV)
4. Thread sayısını ayarlayın (1-50)
5. Çıktı klasörünü seçin
6. "🚀 Start Downloads" butonuna tıklayın

Önemli Notlar

· İlk çalıştırmada yt-dlp otomatik indirilecektir (internet gerektirir)
· ffmpeg video/audio dönüşümü için gereklidir (program otomatik kurmaya çalışır)
· Windows'ta antivirüs programı yt-dlp.exe'yi engelleyebilir, güvenilir olarak işaretleyin
· Linux'ta sudo ile kurulum gerekebilir (program sorar)

Sorun Giderme

Windows'ta "yt-dlp bulunamadı" hatası:

· İnternet bağlantınızı kontrol edin
· Manuel olarak yt-dlp.exe'yi buradan indirip program klasörüne koyun

Linux'ta Tkinter hatası:

```bash
sudo apt install python3-tk
```

ffmpeg bulunamadı hatası:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Windows için ffmpeg'i PATH'e ekleyin
```

Program çöküyor/kapanıyor:

· Log dosyasını kontrol edin (ytdownloader_log.txt)
· Python sürümünüzü kontrol edin (python --version)

Dosya Yapısı

```
├── full_youtube_playlist_installer.py  # Ana program
├── ytdownloader_log.txt                # Log dosyası
├── yt-dlp (veya yt-dlp.exe)            # Otomatik indirilir
├── requirements.txt                     # Python gereksinimleri
└── README.md                           # Bu dosya
```

Lisans

Bu program özgür yazılımdır. YouTube'un hizmet şartlarına uygun kullanın.

Uyarı

· YouTube'un hizmet şartlarını ihlal etmeyin
· Sadece kişisel kullanım ve izin verilen içerikler için kullanın
· Telif hakkı ile korunan içeriği izinsiz indirmeyin

```

Bu dosyaları programınızın bulunduğu klasöre kaydedin. `README.md` dosyası hem Windows hem Linux kullanıcıları için detaylı kurulum ve kullanım talimatları içeriyor.
