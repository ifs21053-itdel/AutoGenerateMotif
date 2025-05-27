// static/js/pewarnaan.js

$(document).ready(function() {
    let selectedColorCodes = [];

    const selectedColorsContainer = $('#selectedColorsContainer');
    const colorCounter = $('#colorCounter');
    const selectedColorsInput = $('#selectedColorsInput'); 
    const coloringForm = $('#coloringForm');
    const coloredImage = $('#coloredImage');
    const noImageMessage = $('#noImageMessage');
    const loadingSpinner = $('#loadingSpinner'); // Spinner di dalam tombol
    const errorMessage = $('#errorMessage');
    const submitButton = $('#submitButton'); // Tombol submit
    const downloadImageBtn = $('#downloadImageBtn'); // Tombol download baru

    // Pastikan ID ini sesuai dengan hidden input di HTML Anda:
    // <input type="hidden" id="ulosColorsJsonData" value="{{ ulos_colors_json_data|safe }}">
    const ulosColorsData = JSON.parse($('#ulosColorsJsonData').val() || '[]');

    // Fungsi untuk memperbarui tampilan warna yang dipilih
    function updateSelectedColorsDisplay() {
        selectedColorsContainer.empty(); // Bersihkan tampilan yang ada

        selectedColorCodes.forEach(function(code) {
            // Temukan objek warna lengkap (termasuk hex_color) dari ulosColorsData
            const colorObj = ulosColorsData.find(color => color.code === code);

            if (colorObj) {
                const colorDiv = $('<div>')
                    .addClass('selected-color-box') // Gunakan .selected-color-box sesuai CSS Anda
                    .css('background-color', colorObj.hex_color); // Set warna latar belakang

                const removeBtn = $('<span>')
                    .addClass('remove-color-btn') // Gunakan .remove-color-btn sesuai CSS Anda
                    .html('&times;') // Tampilkan 'x'
                    .attr('data-code', colorObj.code); // Simpan kode warna di tombol hapus

                colorDiv.append(removeBtn);
                selectedColorsContainer.append(colorDiv);
            }
        });

        // Perbarui counter tanpa batasan maxColors
        colorCounter.text(`${selectedColorCodes.length} warna dipilih`);
        selectedColorsInput.val(selectedColorCodes.join(',')); // Perbarui nilai hidden input
    }

    // Inisialisasi warna yang dipilih saat halaman dimuat
    // Ini penting jika ada data yang sudah terisi dari Django (misal, setelah POST)
    if (selectedColorsInput.val()) {
        selectedColorCodes = selectedColorsInput.val().split(',').filter(Boolean);
        selectedColorCodes.forEach(code => {
            $(`.color-item[data-code="${code}"]`).addClass('selected');
        });
        updateSelectedColorsDisplay(); // Panggil fungsi update display saat inisialisasi
    }

    // Tangani penambahan/penghapusan warna dari palet
    $('.color-item').on('click', function() {
        const colorCode = $(this).data('code'); // Ambil kode warna dari elemen HTML

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

    // Tangani penghapusan warna dari area 'Warna Terpilih'
    $(document).on('click', '.remove-color-btn', function() { // Gunakan .remove-color-btn
        const colorCodeToRemove = $(this).attr('data-code');
        selectedColorCodes = selectedColorCodes.filter(code => code !== colorCodeToRemove);

        // Juga hapus kelas 'selected' dari item palet asli
        $(`.color-item[data-code="${colorCodeToRemove}"]`).removeClass('selected');

        updateSelectedColorsDisplay(); // Perbarui tampilan
    });

    // Penanganan pengiriman form
    coloringForm.on('submit', async function(e) {
        e.preventDefault(); // Mencegah pengiriman form default

        errorMessage.text('');
        coloredImage.hide();
        noImageMessage.show();
        downloadImageBtn.hide(); // Sembunyikan tombol download saat proses dimulai
        loadingSpinner.show(); // Tampilkan spinner
        submitButton.prop('disabled', true); // Nonaktifkan tombol submit

        const jenisUlos = $('#jenisUlos').val();
        const selectedColors = selectedColorsInput.val(); // Dapatkan string dari hidden input

        if (!jenisUlos) {
            errorMessage.text('Pilih jenis Ulos terlebih dahulu.');
            loadingSpinner.hide();
            submitButton.prop('disabled', false); // Aktifkan kembali tombol
            return;
        }
        // Periksa apakah jumlah warna yang dipilih kurang dari 2
        if (selectedColors.split(',').filter(Boolean).length < 2) {
            errorMessage.text('Pilih minimal 2 warna benang.');
            loadingSpinner.hide();
            submitButton.prop('disabled', false); // Aktifkan kembali tombol
            return;
        }

        const formData = new FormData(this); // 'this' merujuk ke elemen form

        try {
            const response = await fetch('/pewarnaan/', { // Sesuaikan URL jika perlu
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest', // Tandai sebagai permintaan AJAX
                }
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error: ${response.status} - ${errorText}`);
            }

            const data = await response.json(); // Asumsi respons adalah JSON

            if (data.colored_image_url) {
                const imageUrl = '/static/' + data.colored_image_url;
                coloredImage.attr('src', imageUrl).show();
                noImageMessage.hide();
                
                // Tampilkan tombol download dan atur atributnya
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
            loadingSpinner.hide()
            submitButton.prop('disabled', false); // Aktifkan kembali tombol
        }
    });
});