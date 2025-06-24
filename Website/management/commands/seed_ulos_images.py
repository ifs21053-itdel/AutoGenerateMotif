import os
from django.core.management.base import BaseCommand
from django.core.files import File
from Website.models import UlosMotifImage
from django.conf import settings

class Command(BaseCommand):
    help = 'Import all existing Ulos motif images from static folder to database'

    def handle(self, *args, **options):
        base_dir = os.path.join(settings.BASE_DIR, 'static', 'img', 'motifs')
        
        # Daftar jenis ulos (sesuaikan dengan folder yang ada)
        ulos_types = ['harungguan', 'puca', 'sadum']  # tambahkan jenis lain jika ada
        
        for ulos_type in ulos_types:
            type_dir = os.path.join(base_dir, ulos_type)
            
            if not os.path.exists(type_dir):
                self.stdout.write(self.style.WARNING(f"Directory not found: {type_dir}"))
                continue
            
            self.stdout.write(f"Processing {ulos_type} motifs...")
            
            for filename in os.listdir(type_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    filepath = os.path.join(type_dir, filename)
                    name = os.path.splitext(filename)[0]  # Nama file tanpa ekstensi
                    
                    # Cek apakah sudah ada di database berdasarkan ID (nama file)
                    if UlosMotifImage.objects.filter(id=name).exists():
                        self.stdout.write(f"Skipping existing: {name}")
                        continue
                    
                    try:
                        with open(filepath, 'rb') as f:
                            django_file = File(f)
                            
                            # Gunakan nama file sebagai ID
                            motif = UlosMotifImage(
                                id=name,  # Gunakan nama file sebagai ID
                                ulos_type=ulos_type,
                                name=name,
                                image_data=django_file.read(),
                                image_format=filename.split('.')[-1].lower()
                            )
                            motif.save()
                            
                            self.stdout.write(self.style.SUCCESS(f"Imported: {name}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error importing {filepath}: {str(e)}"))