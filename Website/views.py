from django .shortcuts import render,redirect
from subprocess import run,PIPE
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.contrib import messages 
from django.core.files.storage import FileSystemStorage
from .models import MotifForm1
from django.contrib.auth.models import User
from .models import Post
from django.contrib.sessions.models import Session
from itertools import zip_longest
from .CheckModule import Check
from .CreateImageModule import CreateImageMotif
from .SaveModule import Save
from .MotifModule import Motif
from .zipModule import ZIP
from .deleteModule import Delete
import sys, os, re

from django.utils.datastructures import MultiValueDictKeyError


@login_required(login_url='login')
def image(request):
    user = request.user
    status = user.is_staff
    
    if status == 0:
          status=None
    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2 active','nav-link nav-link-3','nav-link nav-link-4']
    return render(request, 'home.html',{"status":status,'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

@login_required(login_url='login')
def loading(request):
    user = request.user
    status = user.is_superuser

    if status == 1:
          Autentificate = 1
    users = User.objects.all()
    JumlahAkun = User.objects.count()
    
    jumlah_data = Session.objects.count()
    jumlah_Motif = MotifForm1.objects.count()

    return render(request, 'checkLoading.html',{'users':users,'status':Autentificate,'jmlOnline_user':jumlah_data,'jmlMotif':jumlah_Motif,'jmlAkun':JumlahAkun})

@login_required(login_url='login')
def UpdateUser(request, id):
     user = User.objects.get(id = id)

     return render(request, 'UpdateUser.html',{'user':user})

@login_required(login_url='login')
def updaterecord(request, id):
    staff = request.POST['staff']
    active = request.POST['active']
    admin = request.POST['admin']
    member = User.objects.get(id=id)
    member.is_staff = staff
    member.is_active = active
    member.is_superuser = admin
    member.save()
    messages.info(request, 'Data berhasil di ubah')

    return redirect('Monitoring')

@login_required(login_url='login')
def generator(request):
    navlink = ['nav-link nav-link-1 active ','nav-link nav-link-2','nav-link nav-link-3','nav-link nav-link-4']
    return render(request, 'started.html', {'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

# external lama
@login_required(login_url='login')
def external(request):
    jmlBaris = request.POST.get('jmlBaris')
    Baris = "1"
    user = request.user
    username = user.username
    length = len(username)
    # ModeGenerate = request.POST.get('ModeGenerate')
    image=request.FILES['image']
    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2 active','nav-link nav-link-3','nav-link nav-link-4']
    path = os.getcwd()
    # print("path now", path)
    # print("image is ", image)
    user = request.user
    status = user.is_staff
    
    if status == 0:
          status=None
    
    fs = FileSystemStorage()
    filename = fs.save(image.name, image)
    fileurl = fs.open(filename)
    templateurl = fs.url(filename)
    # print("file raw url",filename)
    # print("file full url", fileurl)
    # print("template url ", templateurl)

    # Memanggil Object Check
    
    Object = Check(str(fileurl), jmlBaris)

    # Memanggil metode check format
    formatStatus =  Object.checkformat()
    
    print(formatStatus, format)
    if(formatStatus == "0"):
         messages.success(request, "Format file yang diproses hanya menerima jpg")
         return render(request, 'home.html', {"jmlBaris": jmlBaris, "status":status,'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

    # Memanggil metode check format
    isOverRow = Object.checkrow()

    if(isOverRow == "0"):
         messages.success(request, "Jumlah baris yang dapat dihasilkan berkisar dari 2 hingga 40")
         return render(request, 'home.html', {"jmlBaris": jmlBaris, "status":status,'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

    
    # # Memanggil metode check spesifikasi gambar

    state, imgHeight = Object.checkSpecImage1()
    
    if state == "0":
        return render(request,'failed.html',{'imgHeight':str(imgHeight)})
    
    state, imgWidth = Object.checkSpecImage2()
    
    jmlBaris = int(jmlBaris)
    if state == "0":
        return render(request,'failedWidth.html',{'imgWidth':str(imgWidth)})
    else: 
        if(jmlBaris %2 == 0):
            jmlBaris = str(jmlBaris)
            Image = CreateImageMotif(str(fileurl), str(filename), jmlBaris, Baris, "4", username)
            URLEdit, UrutanLidi = Image.imageEven()
            URLEdit2, UrutanLidi2 = Image.imageEven()
            URLEdit3, UrutanLidi3 = Image.imageEven()
            URLEdit4, UrutanLidi4 = Image.imageEven()

        else:
            jmlBaris = str(jmlBaris)
            Image = CreateImageMotif(str(fileurl), str(filename), jmlBaris, Baris, "4", username)
            URLEdit, UrutanLidi = Image.imageOdd()
            URLEdit2, UrutanLidi2 = Image.imageOdd()
            URLEdit3, UrutanLidi3 = Image.imageOdd()
            URLEdit4, UrutanLidi4 = Image.imageOdd()

        jenisGenerate = ['Tabu Search', 'Greedy Serach', 'Random Search', 'ACO']

        return render(request, 'motif.html',{'user':username,'jmlBaris':jmlBaris, 'raw_url':templateurl, 'edit_url': URLEdit, 'urutan_lidi':UrutanLidi, 'edit_url2': URLEdit2, 'urutan_lidi2':UrutanLidi2, 'edit_url3': URLEdit3, 'urutan_lidi3':UrutanLidi3, 'edit_url4': URLEdit4, 'urutan_lidi4':UrutanLidi4, 'jenis1':jenisGenerate[3], 'jenis2':jenisGenerate[3], 'jenis3':jenisGenerate[3], 'jenis4':jenisGenerate[3],'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

# external paling baru
# @login_required(login_url='login')
# def external(request):
#     jmlBaris = request.POST.get('jmlBaris')
#     user = request.user
#     username = user.username
#     image_url = request.POST.get('lidiSelect')  # Ambil URL gambar dari select option
    
#     navlink = ['nav-link nav-link-1 ', 'nav-link nav-link-2 active', 'nav-link nav-link-3', 'nav-link nav-link-4']
    
#     # Validasi jumlah baris
#     if not jmlBaris:
#         messages.error(request, "Jumlah baris harus diisi.")
#         return render(request, 'home.html', {"status": user.is_staff, 'navlink1': navlink[0], 'navlink2': navlink[1], 'navlink3': navlink[2], 'navlink4': navlink[3]})
    
#     jmlBaris = int(jmlBaris)
    
#     # Unduh gambar dari URL
#     response = requests.get(image_url)
#     if response.status_code != 200:
#         messages.error(request, "Gagal mengunduh gambar dari URL yang diberikan.")
#         return render(request, 'home.html', {"status": user.is_staff, 'navlink1': navlink[0], 'navlink2': navlink[1], 'navlink3': navlink[2], 'navlink4': navlink[3]})
    
#     # Simpan gambar ke dalam sistem penyimpanan
#     fs = FileSystemStorage()
#     filename = fs.save(user.username + '.jpg', ContentFile(response.content))
#     fileurl = fs.url(filename)
    
#     # Lanjutkan proses seperti sebelumnya
#     Object = Check(str(fileurl), jmlBaris)
    
#     if Object:
#         # Lakukan sesuatu dengan Object yang diperoleh dari Check
#         # Contoh: Menyimpan data ke dalam database atau menampilkan hasil
#         return render(request, 'external.html', {'Object': Object, 'status': user.is_staff, 'navlink1': navlink[0], 'navlink2': navlink[1], 'navlink3': navlink[2], 'navlink4': navlink[3]})
#     else:
#         messages.error(request, "Gagal melakukan proses pembuatan motif.")
#         return render(request, 'home.html', {"status": user.is_staff, 'navlink1': navlink[0], 'navlink2': navlink[1], 'navlink3': navlink[2], 'navlink4': navlink[3]})

@login_required(login_url='login')
def save(request):
    MotifAsal = request.POST.get('image2')
    MotifHasil = request.POST.get('image3')
    Urutan = request.POST.get('urutan')
    Urutan = Urutan[1:-1]
    jenisGenerate = request.POST.get('JenisGenerate')
    jmlBaris = request.POST.get('jmlBaris')
    user = request.POST.get('user')
    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2 active','nav-link nav-link-3','nav-link nav-link-4']
    path = os.getcwd()
    
    ObjectAsal = Save(str(MotifAsal), user)
    Objecthasil = Save(str(MotifHasil), user)

    # Memanggil metode check format
    image2 =  ObjectAsal.SaveMotifAsal()
    image3 =  Objecthasil.SaveMotiHasil()

    return render(request, 'download.html',{'user':user,'jmlBaris':jmlBaris,'raw_url1':image2, 'edit_url1': image3, 'Urutan':str(Urutan), 'jenis': str(jenisGenerate),'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

@login_required(login_url='login')
def PostImage(request):
        if request.method == 'POST':
            if request.POST.get('imgBefore') and request.POST.get('imgAfter') and request.POST.get('urutanLidi') and request.POST.get('jenisGenerate') and request.POST.get('jmlBaris') and request.POST.get('user'):
                    post=MotifForm1()
                    post.imgBefore= request.POST.get('imgBefore')
                    post.imgAfter= request.POST.get('imgAfter')
                    post.urutanLidi = request.POST.get('urutanLidi')
                    post.jenisGenerate = request.POST.get('jenisGenerate')
                    post.jmlBaris = request.POST.get('jmlBaris')
                    post.user = request.POST.get('user')
                    post.save()
                    
                    return render(request, 'success.html')  

            else:
                    return render(request,'success.html')

@login_required(login_url='login')
def createpost(request):
        if request.method == 'POST':
            if request.POST.get('title') and request.POST.get('content'):
                post=Post()
                post.title= request.POST.get('title')
                post.content= request.POST.get('content')
                post.save()
                
                return render(request, 'createpost.html')  

        else:
                return render(request,'createpost.html')

def tes(request):
    return render(request, 'createpost.html')

@login_required(login_url='login')
def Search(request):
    filter = request.POST.get('filter')
    f = request.POST.get('SearchMotif')
    user = request.user
    status = user.is_staff
    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2','nav-link nav-link-3 active','nav-link nav-link-4']

    if status == 0:
          status=None
    if filter == "Jumlah Baris":
        motifForm = MotifForm1.objects.all().filter(jmlBaris__iexact=f).values().order_by('time').reverse()
        filter=['Jumlah Baris','Nama','Tanggal']
    elif filter == "Nama":
        motifForm = MotifForm1.objects.all().filter(user__icontains= f).values().order_by('time').reverse()
        filter=['Nama','Jumlah Baris','Tanggal']
    elif filter == "Tanggal":
        motifForm = MotifForm1.objects.all().filter(time__icontains=f).values().order_by('time').reverse()
        filter=['Tanggal','Nama','Jumlah Baris']

    if (motifForm == ""):
         motifForm = None
    
    context = {"motifForm" : motifForm, "typeFilter1": filter[0], "typeFilter2": filter[1], "typeFilter3": filter[2], "valueFilter": f, "status":status,'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]}
    if(f == ''):
         return redirect('list1')
    return render(request,"search.html", context)

@login_required(login_url='login')
def show(request):
    user = request.user
    status = user.is_staff
    navlink = ['nav-link nav-link-1 ', 'nav-link nav-link-2', 'nav-link nav-link-3 active', 'nav-link nav-link-4']
    if status == 0:
        status = None
    
    motifForm = MotifForm1.objects.all().values().order_by('time').reverse()
    paginator = Paginator(motifForm, 9)  # 9 gambar per halaman

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dapatkan jumlah halaman total
    total_pages = paginator.num_pages

    # Hitung nomor halaman yang akan ditampilkan
    start_page = max(page_obj.number - 1, 1)
    end_page = min(start_page + 2, total_pages)

    # Sesuaikan start_page jika end_page kurang dari 3 halaman dan total_pages lebih dari 3
    if end_page - start_page < 2 and total_pages > 3:
        start_page = max(end_page - 2, 1)

    page_range = range(start_page, end_page + 1)

    context = {
        "motifForm": page_obj,
        'page_range': page_range,
        "status": status,
        'navlink1': navlink[0],
        'navlink2': navlink[1],
        'navlink3': navlink[2],
        'navlink4': navlink[3]
    }

    return render(request, "ListMotif.html", context)

@login_required(login_url='login')
def tagName(request, user):
    username = request.user
    status = username.is_staff
    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2','nav-link nav-link-3 active','nav-link nav-link-4']
    if status == 0:
          status=None
    
    motifForm = MotifForm1.objects.all().filter(user__iexact= user).values().order_by('time').reverse()
        

    context = {"motifForm":motifForm,"status":status,'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]}

    return render(request, "searchTag.html", context)

@login_required(login_url='login')
def tagJmlBaris(request, jmlBaris):
    username = request.user
    status = username.is_staff
    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2','nav-link nav-link-3 active','nav-link nav-link-4']
    if status == 0:
          status=None
    
    motifForm = MotifForm1.objects.all().filter(jmlBaris__iexact= jmlBaris).values().order_by('time').reverse()
        

    context = {"motifForm":motifForm,"status":status,'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]}

    return render(request, "searchTag.html", context)

@login_required(login_url='login')
def tagWaktu(request, time):
    username = request.user
    status = username.is_staff
    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2','nav-link nav-link-3 active','nav-link nav-link-4']
    if status == 0:
          status=None
    time = time[0:10]
    motifForm = MotifForm1.objects.all().filter(time__icontains= time).values().order_by('time').reverse()
        

    context = {"motifForm":motifForm,"status":status,'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]}

    return render(request, "searchTag.html", context)

@login_required(login_url='login')
def motif(request, id):
    motif = MotifForm1.objects.get(id = id)
    user = request.user
    status = user.is_superuser
    status1 = user.is_staff
    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2','nav-link nav-link-3 active','nav-link nav-link-4']
    if status1 == 0:
          status1=None
    if status == 0:
          status=None

    if len(motif.imgAfter)>0:
        ObjectAsal = Motif(str(motif.imgBefore))

        image =  ObjectAsal.UrutanLidi()
        
    ObjecHasil = Motif(str(motif.imgAfter))

    Urutan_Lidi = eval(image)
    UrutanLidi_even = []
    UrutanLidi_odd = []

    for i in range(len(Urutan_Lidi)):
         if i % 2 == 0:
              UrutanLidi_even.append(Urutan_Lidi[i])
         else:
              UrutanLidi_odd.append(Urutan_Lidi[i]) 
    
    image = image[1:-1]

    Lidi =  ObjectAsal.GridLidi()
    Hasil =  ObjecHasil.GridMotif()

    ObjectRed = Motif(Hasil)
    RedLine =  ObjectRed.redLine()

    ObjectZIP = ZIP(str(motif.imgAfter), str(motif.imgBefore))
    Zipfile =  ObjectZIP.ZIPFile()

    Help = ObjectAsal.GridHelp()

    ObjecSlice = Motif(Lidi)
    Slice =  ObjecSlice.Slice()

    Slice = eval(Slice)

    Slice_even = []
    Slice_odd = []     
    for i in range(len(Slice)):
         if i%2 == 0:
              Slice_even.append(Slice[i])
         else:
              Slice_odd.append(Slice[i])
    
    ObjecSlice2 = Motif(RedLine)
    Slice2 =  ObjecSlice2.Slice()

    Slice2 = eval(Slice2)

    Slice2_even = []
    Slice2_odd = []

    for i in range(len(Slice2)):
         if i % 2 == 0:
              Slice2_even.append(Slice2[i])
         else:
              Slice2_odd.append(Slice2[i]) 
       
    UrutanMotif = f"[{motif.urutanLidi}]"
    UrutanMotif = eval(UrutanMotif)

    UrutanMotif_even = []
    UrutanMotif_odd = []

    for i in range(len(UrutanMotif)):
         if i % 2 == 0:
              UrutanMotif_even.append(UrutanMotif[i])
         else:
              UrutanMotif_odd.append(UrutanMotif[i]) 
    
    myList = zip_longest(Slice_even, UrutanLidi_even, Slice_odd, UrutanLidi_odd)
    myList2 = zip_longest(Slice2_even, UrutanMotif_even, Slice2_odd, UrutanMotif_odd)

    return render (request, 'lihatMotif.html', {'zip': Zipfile,'GridHelp': Help,'SliceMotif': myList2,'SliceLidi': myList,'UrutanLidi': Urutan_Lidi,'RedLine': RedLine,'Lidi': Lidi,'urutanAsliLidi': image,'motif': motif, "status":status, 'status1':status1,'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

@login_required(login_url='login')
def deleteMotif(request):

    id = request.POST.get('DeleteImage')
    prod = MotifForm1.objects.get(id = id)
    if len(prod.imgAfter)>0:
        ObjecDelete1 = Delete(str(prod.imgAfter))
        ObjecDelete2 = Delete(str(prod.imgBefore))

        Image1 =  ObjecDelete1.DeleteMotif()
        Image2 =  ObjecDelete2.DeleteMotif()
        
        messages.success(request, "Motif berhasil dihapus")
    prod.delete()
    
    return redirect('list1')

@login_required(login_url='login')    
def showTest(request):
    
    motifForm = Post.objects.all().values()
    context = {"motifForm":motifForm}

    return render(request, "ListMotif.html", context)

@login_required(login_url='login')
def help(request):
    
    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2','nav-link nav-link-3','nav-link nav-link-4 active']
    return render(request, "help.html", {'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

@login_required(login_url='login')
def help_generate(request):

    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2','nav-link nav-link-3','nav-link nav-link-4 active']
    return render(request, "help-generator.html", {'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

@login_required(login_url='login')
def help_lidi(request):

    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2','nav-link nav-link-3','nav-link nav-link-4 active']
    return render(request, "help-lidi.html", {'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

@login_required(login_url='login')
def help_search(request):

    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2','nav-link nav-link-3','nav-link nav-link-4 active']
    return render(request, "help-search.html", {'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

@login_required(login_url='login')
def help_download(request):

    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2','nav-link nav-link-3','nav-link nav-link-4 active']
    return render(request, "help-download.html", {'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

@login_required(login_url='login')
def pewarnaan(request):
    user = request.user
    status = user.is_staff
    
    if status == 0:
        status = None
    
    if request.method == 'POST':
        jenis_ulos = request.POST.get('jenisUlos')
        selected_colors = request.POST.get('selectedColors')
        
        # Validate input
        if jenis_ulos == 'Jenis Ulos' or not selected_colors:
            messages.error(request, "Silakan pilih jenis ulos dan minimal satu warna.")
        else:
            try:
                # Parse selected colors JSON
                import json
                colors_list = json.loads(selected_colors)
                
                if not colors_list:
                    messages.error(request, "Silakan pilih minimal satu warna.")
                else:
                    # Fetch the base motif pattern based on jenis_ulos
                    if jenis_ulos == "harungguan":
                        base_motif = MotifForm1.objects.filter(jenisGenerate__icontains="Harungguan").first()
                    elif jenis_ulos == "puca":
                        base_motif = MotifForm1.objects.filter(jenisGenerate__icontains="Puca").first()
                    elif jenis_ulos == "sadum":
                        base_motif = MotifForm1.objects.filter(jenisGenerate__icontains="Sadum").first()
                    else:
                        base_motif = None
                    
                    if base_motif:
                        # Import required libraries
                        from PIL import Image
                        import colorsys
                        
                        # Process each selected color
                        created_motifs = []
                        for color in colors_list:
                            try:
                                # Process the image coloring
                                img_path = base_motif.imgAfter
                                
                                # Create a new filename for the colored motif
                                original_filename = os.path.basename(img_path)
                                color_code = color.replace('#', '')
                                colored_filename = f"colored_{color_code}_{user.username}_{original_filename}"
                                
                                # Get the path to save the new colored image
                                fs = FileSystemStorage()
                                save_path = os.path.join(fs.location, colored_filename)
                                
                                # Open the original image
                                img = Image.open(img_path.path if hasattr(img_path, 'path') else img_path)
                                
                                # Create a new image for the result
                                colored_img = img.copy().convert('RGBA')
                                
                                # Get the image data
                                pixels = colored_img.load()
                                
                                # Convert hex color to RGB
                                r = int(color[1:3], 16)
                                g = int(color[3:5], 16)
                                b = int(color[5:7], 16)
                                
                                # Convert RGB to HSV
                                h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                                
                                # Process each pixel
                                for i in range(colored_img.width):
                                    for j in range(colored_img.height):
                                        r_orig, g_orig, b_orig, a = pixels[i, j]
                                        
                                        # Only process non-white and non-transparent pixels
                                        if a > 0 and (r_orig < 250 or g_orig < 250 or b_orig < 250):
                                            # Convert to HSV for easier manipulation
                                            h_pixel, s_pixel, v_pixel = colorsys.rgb_to_hsv(r_orig/255, g_orig/255, b_orig/255)
                                            
                                            # Keep the value (brightness) of the original pixel
                                            # but use the hue and saturation from the selected color
                                            new_r, new_g, new_b = colorsys.hsv_to_rgb(h, s, v_pixel)
                                            
                                            # Apply the new color
                                            pixels[i, j] = (int(new_r*255), int(new_g*255), int(new_b*255), a)
                                
                                # Save the colored image
                                colored_img.save(save_path)
                                
                                # Create a new MotifForm1 entry for the colored motif
                                colored_motif = MotifForm1()
                                colored_motif.imgBefore = base_motif.imgBefore
                                colored_motif.imgAfter = colored_filename
                                colored_motif.urutanLidi = base_motif.urutanLidi
                                colored_motif.jenisGenerate = f"{jenis_ulos} (Warna: {color})"
                                colored_motif.jmlBaris = base_motif.jmlBaris
                                colored_motif.user = user.username
                                colored_motif.save()
                                
                                created_motifs.append(color)
                            except Exception as e:
                                messages.error(request, f"Terjadi kesalahan saat memproses warna {color}: {str(e)}")
                        
                        if created_motifs:
                            if len(created_motifs) == 1:
                                messages.success(request, f"Pewarnaan motif {jenis_ulos} dengan warna {created_motifs[0]} berhasil diterapkan! Lihat hasil di halaman Motif.")
                            else:
                                messages.success(request, f"Pewarnaan motif {jenis_ulos} dengan {len(created_motifs)} warna berhasil diterapkan! Lihat hasil di halaman Motif.")
                    else:
                        messages.error(request, f"Tidak ditemukan motif dasar untuk jenis ulos {jenis_ulos}.")
            except Exception as e:
                messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    # Update navlink array untuk 5 menu (termasuk Pewarnaan)
    navlink = ['nav-link nav-link-1', 'nav-link nav-link-2', 'nav-link nav-link-3', 'nav-link nav-link-4 active', 'nav-link nav-link-5']
    return render(request, 'pewarnaan.html', {
        "status": status, 
        'navlink1': navlink[0], 
        'navlink2': navlink[1], 
        'navlink3': navlink[2], 
        'navlink4': navlink[3],
        'navlink5': navlink[4]
    })

def SignupPage(request):
    if request.user.is_authenticated:
         return redirect('home')
    if request.method=='POST':
        uname=request.POST.get('username')
        email=request.POST.get('email')
        pass1=request.POST.get('password1')
        pass2=request.POST.get('password2')
        
        if not re.match(r"^[a-zA-Z0-9_]+$", uname):
            # username is not valid, return an error response
            messages.info(request, 'Username tidak menerima adanya spasi dan simbol lainnya kecuali tanda "_"')
            return render(request,'signup.html', {'uname': uname,'email': email,'pass1': pass1,'pass2': pass2 })
        
        if pass1==pass2:
            if User.objects.filter(username=uname).exists():
                messages.info(request, 'Username sudah pernah digunakan')
                return render(request,'signup.html', {'uname': uname,'email': email,'pass1': pass1,'pass2': pass2 })
            elif User.objects.filter(email=email).exists():
                messages.info(request, 'Email sudah pernah digunakan')
                return render(request,'signup.html', {'uname': uname,'email': email,'pass1': pass1,'pass2': pass2 })
            elif int(len(pass1)<8):
                 messages.info(request, 'Kata sandi minimal 8 karakter')
                 return render(request, 'signup.html', {'uname': uname,'email': email,'pass1': pass1,'pass2': pass2 })
            else:
                user = User.objects.create_user(username=uname, email=email, password=pass1)
                user.save()
                
                user=authenticate(request,username=uname,password=pass1)
                login(request,user)
                
                messages.success(request, 'Akun Berhasil Dibuat')
                
                return redirect('home')
                    
        else:
            messages.info(request, 'Kata Sandi dan Konfirmasi Kata Sandi yang dimasukkan berbeda')
            return render(request,'signup.html', {'uname': uname,'email': email,'pass1': pass1,'pass2': pass2 })
    else:
        return render(request, 'signup.html')


def LoginPage(request):
    if request.user.is_authenticated:
         return redirect('home')
    if request.method=='POST':
        username=request.POST.get('username')
        pass1=request.POST.get('pass')
        user=authenticate(request,username=username,password=pass1)
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.warning(request, 'Username atau Kata Sandi Salah', extra_tags='alert')
            return redirect('login')

    return render (request,'login.html')

def LogoutPage(request):
    logout(request)
    return redirect('login')


