from django.shortcuts import render, redirect
from subprocess import run, PIPE
from django.contrib.auth import authenticate, login, logout
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
from django.shortcuts import render
from .models import UlosCharacteristic, UlosColorThread
import colorsys
from .Coloring import main_coloring_process
from django.http import JsonResponse
import json 
from django.conf import settings
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image
import uuid
import threading
from django.core.cache import cache
from django.views.decorators.http import require_http_methods

# NEW IMPORTS FOR COLOR ANALYSIS
try:
    from .Coloring import get_color_scheme_preview, get_similar_colors_suggestion
    COLOR_ANALYSIS_AVAILABLE = True
except ImportError:
    COLOR_ANALYSIS_AVAILABLE = False
    print("Warning: Color analysis functions not available from Coloring module")

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

@login_required(login_url='login')
def external(request):
    jmlBaris = request.POST.get('jmlBaris')
    Baris = "1"
    user = request.user
    username = user.username
    length = len(username)
    image=request.FILES['image']
    navlink = ['nav-link nav-link-1 ','nav-link nav-link-2 active','nav-link nav-link-3','nav-link nav-link-4']
    path = os.getcwd()
    user = request.user
    status = user.is_staff
    
    if status == 0:
          status=None
    
    fs = FileSystemStorage()
    filename = fs.save(image.name, image)
    fileurl = fs.open(filename)
    templateurl = fs.url(filename)

    Object = Check(str(fileurl), jmlBaris)

    formatStatus =  Object.checkformat()
    
    print(formatStatus, format)
    if(formatStatus == "0"):
         messages.success(request, "Format file yang diproses hanya menerima jpg")
         return render(request, 'home.html', {"jmlBaris": jmlBaris, "status":status,'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

    isOverRow = Object.checkrow()

    if(isOverRow == "0"):
         messages.success(request, "Jumlah baris yang dapat dihasilkan berkisar dari 2 hingga 40")
         return render(request, 'home.html', {"jmlBaris": jmlBaris, "status":status,'navlink1':navlink[0],'navlink2':navlink[1],'navlink3':navlink[2],'navlink4':navlink[3]})

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
    paginator = Paginator(motifForm, 9)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_pages = paginator.num_pages

    start_page = max(page_obj.number - 1, 1)
    end_page = min(start_page + 2, total_pages)

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

# =================== COLORING FUNCTIONALITY ===================

@login_required(login_url='login')
def coloring_view(request):
    """Enhanced coloring view with color analysis capabilities"""
    ulos_types = UlosCharacteristic.objects.all()
    ulos_colors_from_db = UlosColorThread.objects.all()

    colors_for_template = []
    for color_thread in ulos_colors_from_db:
        try:
            r, g, b = colorsys.hsv_to_rgb(
                float(color_thread.hsv.split(',')[0]) / 360, 
                float(color_thread.hsv.split(',')[1]) / 100, 
                float(color_thread.hsv.split(',')[2]) / 100
            )
            hex_color = '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
            colors_for_template.append({
                'code': color_thread.CODE,
                'hex_color': hex_color,
                'hsv': color_thread.hsv,
            })
        except (ValueError, IndexError):
            continue

    ulos_colors_json_data_for_js = json.dumps(colors_for_template)

    if request.method == 'GET':
        context = {
            'ulos_types': ulos_types,
            'ulos_colors': colors_for_template,
            'ulos_colors_json_data': ulos_colors_json_data_for_js,
            'colored_image_url': None,
            'selected_ulos_type': '',
            'selected_colors_codes_str': '',
            'used_colors_display': [],
            'color_analysis_available': COLOR_ANALYSIS_AVAILABLE,
        }
        return render(request, '../templates/pewarnaan.html', context)

    elif request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        selected_ulos_type = request.POST.get('jenisUlos')
        selected_color_codes_str = request.POST.get('selectedColors')
        selected_motif_id = request.POST.get('selectedMotif')
        selected_colors_codes = [code for code in (selected_color_codes_str.split(',') if selected_color_codes_str else []) if code]

        if not selected_ulos_type or len(selected_colors_codes) < 2 or not selected_motif_id:
            return JsonResponse({'error': 'Please select Ulos type, motif, and at least 2 colors.'}, status=400)
        
        base_image_path = os.path.join(
            settings.BASE_DIR, 'static', 'img', 'motifs', selected_ulos_type, f"{selected_motif_id}.png"
        )
        if not os.path.exists(base_image_path):
            return JsonResponse({'error': f'Motif image not found.'}, status=400)

        task_id = str(uuid.uuid4())
        cache.set(task_id, {'progress': 0, 'status': 'Initializing...'}, timeout=3600)
        
        thread = threading.Thread(target=main_coloring_process, args=(
            selected_ulos_type,
            selected_colors_codes,
            base_image_path,
            task_id
        ))
        thread.start()
        
        return JsonResponse({'task_id': task_id})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required(login_url='login')
def get_progress_view(request, task_id):
    """Enhanced progress view with color analysis results"""
    task_result = cache.get(task_id)

    if task_result is None:
        return JsonResponse({'error': 'Task not found or expired.', 'progress': 100, 'status': 'Error'}, status=404)

    if task_result.get('status') == 'Completed':
        used_colors_display = []
        all_colors = {str(c.CODE): c.get_hex_color() for c in UlosColorThread.objects.all()}
        
        for code in task_result.get('unique_used_color_codes', []):
            hex_color = all_colors.get(str(code), '#FFFFFF')
            used_colors_display.append({'code': code, 'hex_color': hex_color})

        # Store enhanced results in session
        request.session['last_colored_image_path'] = task_result['colored_image_url']
        request.session['last_used_colors_display'] = used_colors_display
        request.session['last_color_analysis'] = task_result.get('color_scheme_analysis', {})
        request.session['last_usage_recommendations'] = task_result.get('usage_recommendations', {})
        request.session['last_optimization_scores'] = task_result.get('optimization_scores', {})

        final_data = {
            'progress': 100,
            'status': 'Completed',
            'colored_image_url': task_result['colored_image_url'],
            'used_colors': used_colors_display,
            'color_scheme_analysis': task_result.get('color_scheme_analysis', {}),
            'usage_recommendations': task_result.get('usage_recommendations', {}),
            'optimization_scores': task_result.get('optimization_scores', {})
        }
        return JsonResponse(final_data)

    elif task_result.get('status') == 'Error':
        return JsonResponse({
            'progress': 100,
            'status': 'Error',
            'error': task_result.get('error', 'An unknown error occurred.')
        })

    return JsonResponse(task_result)

@login_required(login_url='login')
def get_ulos_motifs(request):
    """Get available motifs for selected Ulos type"""
    jenis_ulos = request.GET.get('jenis_ulos')
    motifs_data = []
    if jenis_ulos:
        motif_dir = os.path.join(settings.BASE_DIR, 'static', 'img', 'motifs', jenis_ulos.lower())
        if os.path.exists(motif_dir) and os.path.isdir(motif_dir):
            for i, filename in enumerate(sorted(os.listdir(motif_dir))):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    motif_id = os.path.splitext(filename)[0]
                    motif_src = os.path.join(settings.STATIC_URL, 'img', 'motifs', jenis_ulos.lower(), filename)
                    motifs_data.append({'id': motif_id, 'src': motif_src})
    return JsonResponse(motifs_data, safe=False)

# =================== COLOR ANALYSIS API ENDPOINTS ===================

@require_http_methods(["POST"])
@login_required(login_url='login')
def color_scheme_preview(request):
    """Get color scheme analysis preview without running full optimization"""
    if not COLOR_ANALYSIS_AVAILABLE:
        return JsonResponse({
            'error': 'Color analysis functionality not available',
            'suggestion': 'Please ensure Coloring.py module is properly configured'
        }, status=503)
    
    try:
        data = json.loads(request.body)
        color_codes = data.get('color_codes', [])
        
        if not color_codes:
            return JsonResponse({'error': 'No color codes provided'}, status=400)
        
        if len(color_codes) < 2:
            return JsonResponse({'error': 'At least 2 colors required for analysis'}, status=400)
        
        preview_result = get_color_scheme_preview(color_codes)
        
        # Add debug info
        preview_result['debug'] = {
            'input_colors': color_codes,
            'analysis_timestamp': str(uuid.uuid4())[:8]
        }
        
        return JsonResponse(preview_result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Analysis failed: {str(e)}',
            'type': 'analysis_error'
        }, status=500)

@require_http_methods(["GET"])
@login_required(login_url='login')
def similar_colors_suggestion(request):
    """Get similar color suggestions based on a primary color"""
    if not COLOR_ANALYSIS_AVAILABLE:
        return JsonResponse({
            'error': 'Color analysis functionality not available',
            'suggestion': 'Please ensure Coloring.py module is properly configured'
        }, status=503)
    
    try:
        primary_color = request.GET.get('primary_color')
        count = int(request.GET.get('count', 5))
        
        if not primary_color:
            return JsonResponse({'error': 'Primary color code required'}, status=400)
        
        if count < 1 or count > 20:
            return JsonResponse({'error': 'Count must be between 1 and 20'}, status=400)
        
        # Validate color exists
        if not UlosColorThread.objects.filter(CODE=primary_color).exists():
            return JsonResponse({'error': f'Color code {primary_color} not found'}, status=404)
        
        suggestion_result = get_similar_colors_suggestion(primary_color, count)
        
        # Add debug info
        suggestion_result['debug'] = {
            'primary_color': primary_color,
            'requested_count': count,
            'suggestion_timestamp': str(uuid.uuid4())[:8]
        }
        
        return JsonResponse(suggestion_result)
        
    except ValueError:
        return JsonResponse({'error': 'Invalid count parameter'}, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Suggestion failed: {str(e)}',
            'type': 'suggestion_error'
        }, status=500)

@login_required(login_url='login')
def user_color_history(request):
    """Get user's color usage history and basic analytics"""
    try:
        # Get all available colors
        all_colors = UlosColorThread.objects.all()
        colors_data = []
        
        for color in all_colors:
            colors_data.append({
                'code': color.CODE,
                'hex_color': color.get_hex_color(),
                'hsv': color.hsv,
            })
        
        # Get recent session data if available
        recent_analysis = request.session.get('last_color_analysis', {})
        recent_recommendations = request.session.get('last_usage_recommendations', {})
        recent_scores = request.session.get('last_optimization_scores', {})
        
        response_data = {
            'available_colors': colors_data,
            'recent_session': {
                'color_analysis': recent_analysis,
                'recommendations': recent_recommendations,
                'optimization_scores': recent_scores
            },
            'total_colors': len(colors_data),
            'analysis_available': COLOR_ANALYSIS_AVAILABLE,
            'timestamp': str(uuid.uuid4())[:8]
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': f'History retrieval failed: {str(e)}',
            'type': 'history_error'
        }, status=500)

@login_required(login_url='login')
def validate_color_selection(request):
    """Validate selected colors and provide instant feedback"""
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            color_codes = data.get('color_codes', [])
            
            validation_result = {
                'valid': True,
                'warnings': [],
                'suggestions': [],
                'color_count': len(color_codes)
            }
            
            # Basic validation
            if len(color_codes) < 2:
                validation_result['valid'] = False
                validation_result['warnings'].append('At least 2 colors required')
            
            if len(color_codes) > 10:
                validation_result['warnings'].append('More than 10 colors may create complex patterns')
            
            # Check if colors exist
            existing_colors = UlosColorThread.objects.filter(CODE__in=color_codes)
            if len(existing_colors) != len(color_codes):
                validation_result['warnings'].append('Some selected colors not found in database')
            
            # Add quick analysis if available
            if COLOR_ANALYSIS_AVAILABLE and len(color_codes) >= 2:
                try:
                    quick_analysis = get_color_scheme_preview(color_codes)
                    if quick_analysis.get('success'):
                        validation_result['quick_analysis'] = {
                            'scheme_type': quick_analysis.get('scheme_type', 'Unknown'),
                            'harmony_score': quick_analysis.get('harmony_score', 0)
                        }
                except:
                    pass  # Ignore analysis errors in validation
            
            return JsonResponse(validation_result)
        
        return JsonResponse({'error': 'POST method required'}, status=405)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Validation failed: {str(e)}',
            'type': 'validation_error'
        }, status=500)

# =================== PDF GENERATION ===================

@login_required(login_url='login')
def generate_ulos_pdf(request):
    """Enhanced PDF generation with color analysis information"""
    colored_image_path = request.session.get('last_colored_image_path')
    used_colors_display = request.session.get('last_used_colors_display', [])
    color_analysis = request.session.get('last_color_analysis', {})
    usage_recommendations = request.session.get('last_usage_recommendations', {})
    optimization_scores = request.session.get('last_optimization_scores', {})

    if not colored_image_path:
        return HttpResponse("No colored image found", status=400)

    full_image_path = os.path.join(settings.BASE_DIR, 'static', colored_image_path)
    if not os.path.exists(full_image_path):
        return HttpResponse("Colored image file not found", status=404)

    try:
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.setTitle("Hasil Pewarnaan Motif Ulos - Analisis Lengkap")
        p.setAuthor("Aplikasi Pewarnaan Ulos")

        pil_img = Image.open(full_image_path)
        img_width, img_height = pil_img.size

        # Enhanced cover page with analysis
        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, height - 50, "Hasil Pewarnaan Motif Ulos")

        # Main image
        image_area_width = width / 2 - 50
        image_area_height = height - 150

        image_ratio = min(image_area_width / img_width, image_area_height / img_height)
        scaled_img_width = img_width * image_ratio
        scaled_img_height = img_height * image_ratio
        
        image_x = 50
        image_y = (height - scaled_img_height) / 2 - 20
        
        p.drawImage(full_image_path, image_x, image_y, 
                            width=scaled_img_width, height=scaled_img_height, 
                            preserveAspectRatio=True)

        # Grid section
        p.setFont("Helvetica-Bold", 14)
        grid_title_x = width / 2 + 50
        grid_title_y = height - 80
        p.drawString(grid_title_x, grid_title_y, "URUTAN MENEMPEL")

        grid_start_x = grid_title_x
        grid_start_y = grid_title_y - 30
        cell_size = 30
        
        p.setFont("Helvetica", 10)
        for row_idx in range(4):
            for col_idx in range(4):
                x = grid_start_x + col_idx * cell_size
                y = grid_start_y - row_idx * cell_size - cell_size
                cell_label = f"{chr(65+col_idx)}{row_idx+1}"
                
                p.rect(x, y, cell_size, cell_size)
                text_width = p.stringWidth(cell_label, "Helvetica", 10)
                p.drawString(x + (cell_size - text_width) / 2, y + cell_size/2 - 3, cell_label)

        # Color palette
        if used_colors_display:
            p.setFont("Helvetica-Bold", 12)
            colors_title_x = grid_title_x
            colors_title_y = grid_start_y - 4 * cell_size - 40
            p.drawString(colors_title_x, colors_title_y, "Warna yang Digunakan:")

            color_item_y = colors_title_y - 20
            color_box_size = 15
            text_offset = 5

            p.setFont("Helvetica", 10)
            for color_info in used_colors_display:
                if color_info and 'hex_color' in color_info and 'code' in color_info:
                    hex_color = color_info['hex_color']
                    code = color_info['code']

                    try:
                        r_hex = int(hex_color[1:3], 16) / 255.0
                        g_hex = int(hex_color[3:5], 16) / 255.0
                        b_hex = int(hex_color[5:7], 16) / 255.0
                        p.setFillColorRGB(r_hex, g_hex, b_hex)
                        p.rect(colors_title_x, color_item_y, color_box_size, color_box_size, fill=1)
                        p.setStrokeColorRGB(0,0,0)
                        p.rect(colors_title_x, color_item_y, color_box_size, color_box_size, fill=0, stroke=1)
                    except ValueError:
                        p.setFillColorRGB(0.5, 0.5, 0.5)
                        p.rect(colors_title_x, color_item_y, color_box_size, color_box_size, fill=1)
                        p.setStrokeColorRGB(0,0,0)
                        p.rect(colors_title_x, color_item_y, color_box_size, color_box_size, fill=0, stroke=1)

                    p.setFillColorRGB(0,0,0)
                    p.drawString(colors_title_x + color_box_size + text_offset, color_item_y + 3, f"{code}")
                    color_item_y -= 20

        p.setFont("Helvetica", 10)
        p.drawString(width / 2 - 30, 30, "Halaman 1 dari 19")
        p.showPage()

        ## Desain Utuh - Bagian Atas
        # --- Page 2: Cropped top half of the image ---
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, height - 50, "Desain Utuh - Bagian Atas ")

        top_half_height = img_height // 2
        cropped_top_img = pil_img.crop((0, 0, img_width, top_half_height))

        max_width_page = width - 200
        max_height_page = height - 200
        ratio_page = min(max_width_page / cropped_top_img.width, max_height_page / cropped_top_img.height)
        scaled_width_page = cropped_top_img.width * ratio_page
        scaled_height_page = cropped_top_img.height * ratio_page

        p.drawInlineImage(cropped_top_img, (width - scaled_width_page) / 2, (height - scaled_height_page) / 2 - 20, # Dipusatkan vertikal
                                width=scaled_width_page, height=scaled_height_page)
        
        p.setFont("Helvetica", 10)
        p.drawString(width / 2 - 30, 30, "Halaman 2 dari 19")
        p.showPage()
        

## Desain Utuh - Bagian Bawah
        # --- Page 3: Cropped bottom half of the image ---
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, height - 50, "Desain Utuh - Bagian Bawah ")
        
        bottom_half_height = img_height // 2
        cropped_bottom_img = pil_img.crop((0, bottom_half_height, img_width, img_height))

        scaled_width_page_bottom = cropped_bottom_img.width * ratio_page
        scaled_height_page_bottom = cropped_bottom_img.height * ratio_page

        p.drawInlineImage(cropped_bottom_img, (width - scaled_width_page_bottom) / 2, (height - scaled_height_page_bottom) / 2 - 20, # Dipusatkan vertikal
                                width=scaled_width_page_bottom, height=scaled_height_page_bottom)
        
        p.setFont("Helvetica", 10)
        p.drawString(width / 2 - 30, 30, "Halaman 3 dari 19")
        p.showPage()

        section_width = img_width // 4
        section_height = img_height // 4
        
        page_counter = 4

        section_labels = [
            ["A1", "A2", "A3", "A4"],
            ["B1", "B2", "B3", "B4"],
            ["C1", "C2", "C3", "C4"],
            ["D1", "D2", "D3", "D4"]
        ]

        for row_idx in range(4):
            for col_idx in range(4):
                section_label = section_labels[col_idx][row_idx] 

                left = col_idx * section_width
                upper = row_idx * section_height
                right = left + section_width
                lower = upper + section_height

                cropped_img = pil_img.crop((left, upper, right, lower))

                p.setFont("Helvetica-Bold", 16)
                p.drawString(100, height - 50, section_label)

                max_section_width = width - 200
                max_section_height = height - 200
                section_ratio = min(max_section_width / section_width, max_section_height / section_height)
                scaled_section_width = section_width * section_ratio
                scaled_section_height = section_height * section_ratio

                p.drawInlineImage(cropped_img, (width - scaled_section_width) / 2,
                                            (height - scaled_section_height) / 2 - 20,
                                            width=scaled_section_width,
                                            height=scaled_section_height)
                
                p.setFont("Helvetica", 10)
                p.drawString(width / 2 - 30, 30, f"Halaman {page_counter} dari 19")
                page_counter += 1

                p.showPage()
        p.save()

        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="hasil_pewarnaan_ulos_analisis.pdf"'

        return response

    except Exception as e:
        print(f"Error generating PDF: {e}")
        return HttpResponse(f"Error generating PDF: {e}", status=500)

# =================== AUTHENTICATION ===================
            
def SignupPage(request):
    if request.user.is_authenticated:
         return redirect('home')
    if request.method=='POST':
        uname=request.POST.get('username')
        email=request.POST.get('email')
        pass1=request.POST.get('password1')
        pass2=request.POST.get('password2')
        
        if not re.match(r"^[a-zA-Z0-9_]+$", uname):
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