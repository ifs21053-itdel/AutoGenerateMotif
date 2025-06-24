from django.db import models
import colorsys
from django.contrib.auth.models import User

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

# Model untuk menyimpan hasil analisis pewarnaan
class UlosColoringResult(models.Model):
    """Model untuk menyimpan hasil analisis pewarnaan Ulos"""
    
    SCHEME_TYPE_CHOICES = [
        ('Monochromatic', 'Monochromatic'),
        ('Analogous', 'Analogous'),
        ('Complementary', 'Complementary'),
        ('Complex', 'Complex'),
        ('Achromatic', 'Achromatic'),
        ('Achromatic + Accent', 'Achromatic + Accent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coloring_results')
    ulos_type = models.ForeignKey(UlosCharacteristic, on_delete=models.CASCADE)
    motif_id = models.CharField(max_length=20)
    
    # Color analysis results
    color_scheme_type = models.CharField(max_length=20, choices=SCHEME_TYPE_CHOICES)
    color_harmony_score = models.FloatField()
    scheme_description = models.TextField()
    hue_range = models.FloatField(default=0)
    achromatic_count = models.IntegerField(default=0)
    chromatic_count = models.IntegerField(default=0)
    
    # Usage recommendations
    best_for = models.TextField()
    ulos_application = models.TextField()
    harmony_level = models.CharField(max_length=20)
    primary_ratio = models.CharField(max_length=10)
    secondary_ratio = models.CharField(max_length=10)
    accent_ratio = models.CharField(max_length=20)
    
    # Optimization scores
    michaelson_contrast = models.FloatField()
    rms_contrast = models.FloatField()
    colorfulness = models.FloatField()
    optimal_unique_colors = models.FloatField()
    user_preference_match = models.FloatField()
    
    # Result image
    colored_image_path = models.CharField(max_length=255)
    used_color_codes = models.JSONField()  # List of color codes used
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.ulos_type.NAME} - {self.color_scheme_type}"
    
    class Meta:
        verbose_name = "Ulos Coloring Result"
        verbose_name_plural = "Ulos Coloring Results"
        db_table = 'ulos_coloring_result'
        ordering = ['-created_at']

# NEW: Model untuk menyimpan preferensi warna pengguna
class UserColorPreference(models.Model):
    """Model untuk menyimpan preferensi warna pengguna"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='color_preferences')
    color_code = models.ForeignKey(UlosColorThread, on_delete=models.CASCADE)
    usage_count = models.IntegerField(default=1)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Color Preference"
        verbose_name_plural = "User Color Preferences"
        db_table = 'user_color_preference'
        unique_together = ('user', 'color_code')

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

class UlosMotifImage(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    ulos_type = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=100)
    image_data = models.BinaryField()
    image_format = models.CharField(max_length=10)
    
    class Meta:
        db_table = 'ulos_motif_image'
        verbose_name = 'Ulos Motif Image'
        verbose_name_plural = 'Ulos Motif Images'
    
    def __str__(self):
        return f"{self.ulos_type} - {self.name}"