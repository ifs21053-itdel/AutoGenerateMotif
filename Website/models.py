from django.db import models

#Create Model Here
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