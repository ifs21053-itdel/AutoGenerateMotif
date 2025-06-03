$(document).ready(function() {
    let selectedColorCodes = [];
    let selectedMotif = '';

    function generateMotifData(jenisUlos, motifNumber) {
        const id = `${jenisUlos.toLowerCase()}${motifNumber}`;
        const src = `/static/img/motifs/${jenisUlos.toLowerCase()}/${id}.png`;
        return { id, src };
    }

    const ulosMotifs = {};
    const ulosTypes = ['Harungguan', 'Puca', 'Sadum'];
    for (const jenisUlos of ulosTypes) {
        ulosMotifs[jenisUlos] = [];
        for (let i = 1; i <= 5; i++) {
            ulosMotifs[jenisUlos].push(generateMotifData(jenisUlos, i));
        }
    }

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
        updateSelectedColorsDisplay();
    });

    jenisUlosSelect.on('change', function() {
        const selectedUlosType = $(this).val();

        if (motifCarousel.hasClass('slick-initialized')) {
            motifCarousel.slick('unslick');
        }

        motifCarousel.empty();

        selectedMotif = '';
        selectedMotifInput.val('');

        if (selectedUlosType) {
            if (ulosMotifs[selectedUlosType]) {

                ulosMotifs[selectedUlosType].forEach(function(motif) {
                    const slide = $('<div>').addClass('motif-slide');
                    const img = $('<img>')
                        .attr('src', motif.src)
                        .attr('alt', 'Motif ' + selectedUlosType)
                        .attr('data-motif-id', motif.id);
                    slide.append(img);
                    motifCarousel.append(slide);
                });

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

                    motifCarouselContainer.show();

                    motifCarousel.attr('data-active-ulos', selectedUlosType);

                    if (ulosMotifs[selectedUlosType].length > 0) {
                        const firstMotif = ulosMotifs[selectedUlosType][0];
                        selectedMotif = firstMotif.id;
                        selectedMotifInput.val(selectedMotif);
                        motifCarousel.find('.slick-slide').eq(0).addClass('selected');
                    }
                }, 50);
            } else {
                motifCarouselContainer.hide();
            }
        } else {
            motifCarouselContainer.hide();
        }
    });

    $(document).on('click', '.motif-slide', function(e) {
        e.preventDefault();

        $('.motif-slide').removeClass('selected');

        $(this).addClass('selected');

        const img = $(this).find('img');
        if (img.length) {
            selectedMotif = img.data('motif-id');
            selectedMotifInput.val(selectedMotif);
        }

        errorMessage.text('');
    });

    function updateSelectedColorsDisplay() {
        selectedColorsContainer.empty();

        selectedColorCodes.forEach(function(code) {
            const colorObj = ulosColorsData.find(color => color.code === code);

            if (colorObj) {
                const colorContainer = $('<div>').addClass('selected-color-container');

                const codeLabel = $('<div>')
                    .addClass('selected-color-name')
                    .text(code);

                const colorDiv = $('<div>')
                    .addClass('selected-color-box')
                    .css('background-color', colorObj.hex_color);

                const removeBtn = $('<span>')
                    .addClass('remove-color-btn')
                    .html('&times;')
                    .attr('data-code', colorObj.code);

                colorContainer.append(codeLabel);
                colorContainer.append(colorDiv);
                colorDiv.append(removeBtn);
                selectedColorsContainer.append(colorContainer);
            }
        });

        colorCounter.text(`${selectedColorCodes.length} warna dipilih`);
        selectedColorsInput.val(selectedColorCodes.join(','));
    }

    if (selectedColorsInput.val()) {
        selectedColorCodes = selectedColorsInput.val().split(',').filter(Boolean);
        selectedColorCodes.forEach(code => {
            $(`.color-box[data-code="${code}"]`).addClass('selected');
        });
        updateSelectedColorsDisplay();
    }

    $(document).on('click', '.remove-color-btn', function() {
        const colorCodeToRemove = $(this).attr('data-code');
        selectedColorCodes = selectedColorCodes.filter(code => code !== colorCodeToRemove);

        $(`.color-box[data-code="${colorCodeToRemove}"]`).removeClass('selected');

        updateSelectedColorsDisplay();
    });

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
            errorMessage.text(`Gagal memproses pewarnaan. Coba lagi.`);
        } finally {
            loadingSpinner.hide();
            submitButton.prop('disabled', false);
        }
    });
});