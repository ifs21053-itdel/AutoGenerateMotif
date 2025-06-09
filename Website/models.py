from django.db import models
import colorsys

class MotifForm(models.Model):
    imgBefore = models.TextField()
    imgAfter  = models.TextField()
    urutanLidi = models.TextField()

class MotifForm1(models.Model):
    imgBefore = models.TextField()
    imgAfter  = models.TextField()
    urutanLidi = models.TextField()
    jenisGenerate = models.TextField()
    jmlBaris = models.TextField()
    user = models.TextField()
    time = models.DateTimeField(auto_now_add= True)

class UlosColorThread(models.Model):
    CODE = models.CharField(max_length=10, primary_key=True)
    hsv = models.CharField(max_length=50)

    def get_hex_color(self):
        """
        Mengonversi nilai HSV string yang tersimpan di database
        menjadi format warna hexadecimal (#RRGGBB).
        """
        try:
            h_str, s_str, v_str = self.hsv.split(',')
            h = float(h_str)
            s = float(s_str) / 100.0
            v = float(v_str) / 100.0
            
            r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
            
            # Konversi nilai RGB (0-1) menjadi integer (0-255)
            r_int = int(r * 255)
            g_int = int(g * 255)
            b_int = int(b * 255)
            
            return '#%02x%02x%02x' % (r_int, g_int, b_int)
        except (ValueError, IndexError):
            # Kembali ke warna default jika ada error pada format HSV
            return '#FFFFFF' 

    def __str__(self):
        return self.CODE

    class Meta:
        verbose_name = "Ulos Color Thread"
        verbose_name_plural = "Ulos Color Threads"
        db_table = 'ulos_color_thread'

class UlosCharacteristic(models.Model):
    NAME = models.CharField(max_length=50, primary_key=True)
    garis = models.TextField()
    pola = models.TextField()
    warna_dominasi = models.TextField()
    warna_aksen = models.TextField()
    kontras_warna = models.TextField()

    def __str__(self):
        return self.NAME

    class Meta:
        verbose_name = "Ulos Characteristic"
        verbose_name_plural = "Ulos Characteristics"
        db_table = 'ulos_characteristic'
    

class Post(models.Model):
    title= models.TextField()
    content= models.TextField()

# pengenmbangan untuk select optiom
# class Motif(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     imgBefore = models.ImageField(upload_to='images/')  # Gambar sebelum motif dibuat
#     imgAfter = models.ImageField(upload_to='images/')   # Gambar setelah motif dibuat
#     urutanLidi = models.CharField(max_length=100)        # Urutan lidi yang digunakan
#     jenisGenerate = models.CharField(max_length=50)      # Jenis algoritma/generate yang digunakan
#     jmlBaris = models.IntegerField()                     # Jumlah baris yang dihasilkan
#     time = models.DateTimeField(auto_now_add=True)       # Waktu pembuatan motif