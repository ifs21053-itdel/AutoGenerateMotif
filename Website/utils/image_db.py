import os
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files import File
from myapp.models import UlosMotifImage

def save_motif_to_db(ulos_type: str, name: str, image_file: (InMemoryUploadedFile or File)):
    """
    Menyimpan gambar motif ke database
    Menerima InMemoryUploadedFile (upload form) atau File (file system)
    """
    # Baca data gambar
    image_data = image_file.read()
    
    # Dapatkan ekstensi file
    if hasattr(image_file, 'name'):  # Untuk InMemoryUploadedFile
        ext = os.path.splitext(image_file.name)[1].lower()[1:]
    else:  # Untuk File
        ext = os.path.splitext(name)[1].lower()[1:]
    
    # Buat record di database
    motif = UlosMotifImage(
        ulos_type=ulos_type.lower(),
        name=name,
        image_data=image_data,
        image_format=ext
    )
    motif.save()
    return motif