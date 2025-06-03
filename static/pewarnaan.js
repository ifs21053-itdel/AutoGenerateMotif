// static/js/pewarnaan.js

$(document).ready(function() {
    let selectedColorCodes = [];
    let selectedMotif = '';

    // Data motif Ulos berdasarkan jenis
    const ulosMotifs = {
        'Harungguan': [
            { id: 'harungguan_1', src: '/static/img/motifs/harungguan/harungguan1.png' },
            { id: 'harungguan_2', src: '/static/img/motifs/harungguan/harungguan2.png' },
            { id: 'harungguan_3', src: '/static/img/motifs/harungguan/harungguan3.png' },
            { id: 'harungguan_4', src: '/static/img/motifs/harungguan/harungguan4.png' },
            { id: 'harungguan_5', src: '/static/img/motifs/harungguan/harungguan5.png' }
        ],
        'Puca': [
            { id: 'puca_1', src: '/static/img/motifs/puca/puca1.png' },
            { id: 'puca_2', src: '/static/img/motifs/puca/puca2.png' },
            { id: 'puca_3', src: '/static/img/motifs/puca/puca3.png' },
            { id: 'puca_4', src: '/static/img/motifs/puca/puca4.png' },
            { id: 'puca_5', src: '/static/img/motifs/puca/puca5.png' }
        ],
        'Sadum': [
            { id: 'sadum_1', src: '/static/img/motifs/sadum/sadum1.png' },
            { id: 'sadum_2', src: '/static/img/motifs/sadum/sadum2.png' },
            { id: 'sadum_3', src: '/static/img/motifs/sadum/sadum3.png' },
            { id: 'sadum_4', src: '/static/img/motifs/sadum/sadum4.png' },
            { id: 'sadum_5', src: '/static/img/motifs/sadum/sadum5.png' }
        ]
    };

    // Kamus nama warna
    const colorNames = {
        'C001': 'Hitam',
        'C002': 'Merah Tua',
        'C003': 'Merah',
        'C004': 'Merah Marun',
        'C005': 'Merah Hati',
        'C006': 'Merah Terang',
        'C007': 'Oranye',
        'C008': 'Magenta',
        'C009': 'Ungu',
        'C010': 'Pink',
        'C011': 'Oranye Terang',
        'C012': 'Coklat',
        'C013': 'Coklat Muda',
        'C014': 'Kuning Tua',
        'C015': 'Kuning',
        'C016': 'Krem',
        'C017': 'Putih',
        'C018': 'Kuning Muda',
        'C019': 'Kuning Cerah',
        'C020': 'Hijau Muda',
        'C021': 'Hijau',
        'C022': 'Hijau Tua',
        'C023': 'Hijau Terang',
        'C024': 'Hijau Neon',
        'C025': 'Hijau Tosca',
        'C026': 'Biru Muda',
        'C027': 'Biru Langit',
        'C028': 'Biru',
        'C029': 'Abu-abu',
        'C030': 'Biru Tua',
        'C031': 'Ungu'
    };

    const selectedColorsContainer = $('#selectedColorsContainer');
    const colorCounter = $('#colorCounter');
    const selectedColorsInput = $('#selectedColorsInput'); 
    const coloringForm = $('#coloringForm');
    const coloredImage = $('#coloredImage');
    const noImageMessage = $('#noImageMessage');
    const loadingSpinner = $('#loadingSpinner');
    const errorMessage = $('#errorMessage');
    const submitButton = $('#submitButton');
    const downloadImageBtn = $('#downloadImageBtn');
    const jenisUlosSelect = $('#jenisUlos');
    const motifCarouselContainer = $('#motifCarouselContainer');
    const motifCarousel = $('#motifCarousel');
    const selectedMotifInput = $('#selectedMotifInput');

    // Pastikan ID ini sesuai dengan hidden input di HTML Anda
    const ulosColorsData = JSON.parse($('#ulosColorsJsonData').val() || '[]');

    // Inisialisasi penanganan klik pada item warna
    $('.color-box').on('click', function() {
        const colorCode = $(this).data('code');
        const index = selectedColorCodes.indexOf(colorCode);

        if (index > -1) {
            // Warna sudah dipilih, hapus
            selectedColorCodes.splice(index, 1);
            $(this).removeClass('selected');
        } else {
            // Warna belum dipilih, tambahkan
            selectedColorCodes.push(colorCode);
            $(this).addClass('selected');
        }
        
        errorMessage.text(''); // Bersihkan pesan error sebelumnya
        updateSelectedColorsDisplay(); // Perbarui tampilan
    });

    // Menangani perubahan pada dropdown jenis ulos
    jenisUlosSelect.on('change', function() {
        const selectedUlosType = $(this).val();
        
        // Reset terlebih dahulu
        // Pastikan carousel di-destroy sepenuhnya jika sudah ada
        if (motifCarousel.hasClass('slick-initialized')) {
            motifCarousel.slick('unslick');
        }
        
        // Kosongkan container
        motifCarousel.empty();
        
        // Reset selectedMotif
        selectedMotif = '';
        selectedMotifInput.val('');
        
        if (selectedUlosType) {
            // Cek apakah motif untuk jenis ulos ini tersedia
            if (ulosMotifs[selectedUlosType]) {
                console.log(`Menampilkan motif untuk jenis: ${selectedUlosType}`);
                
                // Tambahkan motif ke carousel
                ulosMotifs[selectedUlosType].forEach(function(motif) {
                    const slide = $('<div>').addClass('motif-slide');
                    const img = $('<img>')
                        .attr('src', motif.src)
                        .attr('alt', 'Motif ' + selectedUlosType)
                        .attr('data-motif-id', motif.id);
                    slide.append(img);
                    motifCarousel.append(slide);
                });
                
                // Setelah DOM diperbarui, inisialisasi carousel
                setTimeout(function() {
                    motifCarousel.slick({
                        dots: true,
                        infinite: true,
                        speed: 300,
                        slidesToShow: 3,
                        slidesToScroll: 1,
                        centerMode: true,
                        focusOnSelect: true,
                        arrows: true,
                        prevArrow: '<button type="button" class="slick-prev">Previous</button>',
                        nextArrow: '<button type="button" class="slick-next">Next</button>',
                        responsive: [
                            {
                                breakpoint: 768,
                                settings: {
                                    slidesToShow: 2,
                                    slidesToScroll: 1,
                                    arrows: true
                                }
                            },
                            {
                                breakpoint: 576,
                                settings: {
                                    slidesToShow: 1,
                                    slidesToScroll: 1,
                                    arrows: true
                                }
                            }
                        ]
                    });
                    
                    // Tampilkan container carousel
                    motifCarouselContainer.show();
                    
                    // Tambahkan class ke elemen carousel untuk menandai jenis ulos yang aktif
                    motifCarousel.attr('data-active-ulos', selectedUlosType);
                    
                    console.log(`Carousel berhasil diinisialisasi untuk: ${selectedUlosType}`);
                }, 50);
            } else {
                console.log(`Tidak ada motif untuk jenis: ${selectedUlosType}`);
                // Jika tidak ada motif untuk jenis ulos ini, sembunyikan carousel
                motifCarouselContainer.hide();
            }
        } else {
            console.log("Tidak ada jenis ulos yang dipilih");
            // Jika tidak ada jenis ulos yang dipilih, sembunyikan carousel
            motifCarouselContainer.hide();
        }
    });

    // Menangani klik pada motif dengan lebih baik
    $(document).on('click', '.motif-slide', function(e) {
        e.preventDefault();
        
        // Hapus kelas selected dari semua slide
        $('.motif-slide').removeClass('selected');
        
        // Tambahkan kelas selected ke slide yang dipilih
        $(this).addClass('selected');
        
        // Simpan ID motif yang dipilih
        const img = $(this).find('img');
        if (img.length) {
            selectedMotif = img.data('motif-id');
            selectedMotifInput.val(selectedMotif);
            console.log(`Motif dipilih: ${selectedMotif}`);
        }
        
        // Bersihkan pesan error sebelumnya
        errorMessage.text('');
    });

    // Fungsi untuk memperbarui tampilan warna yang dipilih
    function updateSelectedColorsDisplay() {
        selectedColorsContainer.empty(); // Bersihkan tampilan yang ada

        selectedColorCodes.forEach(function(code) {
            // Temukan objek warna lengkap dari ulosColorsData
            const colorObj = ulosColorsData.find(color => color.code === code);

            if (colorObj) {
                // Container untuk warna dan label
                const colorContainer = $('<div>').addClass('selected-color-container');
                
                // Label kode warna
                const codeLabel = $('<div>')
                    .addClass('selected-color-name')
                    .text(code);
                
                // Kotak warna
                const colorDiv = $('<div>')
                    .addClass('selected-color-box')
                    .css('background-color', colorObj.hex_color);

                // Tombol hapus
                const removeBtn = $('<span>')
                    .addClass('remove-color-btn')
                    .html('&times;')
                    .attr('data-code', colorObj.code);

                // Susun elemen
                colorContainer.append(codeLabel);
                colorContainer.append(colorDiv);
                colorDiv.append(removeBtn);
                selectedColorsContainer.append(colorContainer);
            }
        });

        // Perbarui counter
        colorCounter.text(`${selectedColorCodes.length} warna dipilih`);
        selectedColorsInput.val(selectedColorCodes.join(',')); // Perbarui nilai hidden input
    }

    // Inisialisasi warna yang dipilih saat halaman dimuat
    if (selectedColorsInput.val()) {
        selectedColorCodes = selectedColorsInput.val().split(',').filter(Boolean);
        selectedColorCodes.forEach(code => {
            $(`.color-box[data-code="${code}"]`).addClass('selected');
        });
        updateSelectedColorsDisplay();
    }

    // Tangani penghapusan warna dari area 'Warna Terpilih'
    $(document).on('click', '.remove-color-btn', function() {
        const colorCodeToRemove = $(this).attr('data-code');
        selectedColorCodes = selectedColorCodes.filter(code => code !== colorCodeToRemove);

        // Hapus kelas 'selected' dari item palet asli
        $(`.color-box[data-code="${colorCodeToRemove}"]`).removeClass('selected');

        updateSelectedColorsDisplay();
    });

    // Penanganan pengiriman form
    coloringForm.on('submit', async function(e) {
        e.preventDefault();

        errorMessage.text('');
        coloredImage.hide();
        noImageMessage.show();
        downloadImageBtn.hide();
        loadingSpinner.show();
        submitButton.prop('disabled', true);

        const jenisUlos = $('#jenisUlos').val();
        const selectedColors = selectedColorsInput.val();
        const motif = selectedMotifInput.val();

        if (!jenisUlos) {
            errorMessage.text('Pilih jenis Ulos terlebih dahulu.');
            loadingSpinner.hide();
            submitButton.prop('disabled', false);
            return;
        }
        
        if (!motif && motifCarouselContainer.is(':visible')) {
            errorMessage.text('Pilih motif Ulos terlebih dahulu.');
            loadingSpinner.hide();
            submitButton.prop('disabled', false);
            return;
        }
        
        if (selectedColors.split(',').filter(Boolean).length < 2) {
            errorMessage.text('Pilih minimal 2 warna benang.');
            loadingSpinner.hide();
            submitButton.prop('disabled', false);
            return;
        }

        const formData = new FormData(this);

        try {
            const response = await fetch('/pewarnaan/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error: ${response.status} - ${errorText}`);
            }

            const data = await response.json();

            if (data.colored_image_url) {
                const imageUrl = '/static/' + data.colored_image_url;
                coloredImage.attr('src', imageUrl).show();
                noImageMessage.hide();
                
                downloadImageBtn.attr('href', imageUrl);
                downloadImageBtn.show(); 
            } else if (data.error) {
                errorMessage.text(`Error: ${data.error}`);
            } else {
                errorMessage.text('Terjadi kesalahan tidak diketahui.');
            }

        } catch (error) {
            console.error('Fetch error:', error);
            errorMessage.text(`Gagal memproses pewarnaan. Coba lagi.`);
        } finally {
            loadingSpinner.hide();
            submitButton.prop('disabled', false);
        }
    });
});