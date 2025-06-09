$(document).ready(function () {
  let selectedColorCodes = [];
  let selectedMotif = "";

  const selectedColorsContainer = $("#selectedColorsContainer");
  const colorCounter = $("#colorCounter");
  const selectedColorsInput = $("#selectedColorsInput");
  const coloringForm = $("#coloringForm");
  const coloredImage = $("#coloredImage");
  const noImageMessage = $("#noImageMessage");
  const loadingSpinner = $("#loadingSpinner");
  const errorMessage = $("#errorMessage");
  const submitButton = $("#submitButton");
  const downloadImageBtn = $("#downloadImageBtn");
  const downloadPdfBtn = $("#downloadPdfBtn");
  const jenisUlosSelect = $("#jenisUlos");
  const motifCarouselContainer = $("#motifCarouselContainer");
  const motifCarousel = $("#motifCarousel");
  const selectedMotifInput = $("#selectedMotifInput");

  const usedColorsDisplay = $("#usedColorsDisplay");
  const actualUsedColorsPalette = $("#actualUsedColorsPalette");

  // TAMBAHAN: Buat elemen loading bar dan tambahkan ke DOM setelah tombol submit
  const loadingBarHTML = `
        <div id="loadingBarContainer" class="loading-bar-container">
            <div id="loadingBarProgress" class="loading-bar-progress"></div>
            <div id="loadingBarText" class="loading-bar-text">0 %</div>
        </div>
    `;
  $("#submitButton").after(loadingBarHTML);

  // TAMBAHAN: Buat referensi ke elemen loading bar
  const loadingBarContainer = $("#loadingBarContainer");
  const loadingBarProgress = $("#loadingBarProgress");
  const loadingBarText = $("#loadingBarText");

  // TAMBAHAN: Fungsi untuk mengupdate progress bar
  function updateLoadingBar(percent) {
    loadingBarProgress.css("width", percent + "%");
    loadingBarText.text(percent + " %");
  }

  const ulosColorsData = JSON.parse($("#ulosColorsJsonData").val() || "[]");

  $(".color-box").on("click", function () {
    const colorCode = $(this).data("code");
    const index = selectedColorCodes.indexOf(colorCode);

    if (index > -1) {
      selectedColorCodes.splice(index, 1);
      $(this).removeClass("selected");
    } else {
      selectedColorCodes.push(colorCode);
      $(this).addClass("selected");
    }
    updateSelectedColorsDisplay();
  });

  jenisUlosSelect.on("change", async function () {
    const selectedUlosType = $(this).val();

    if (motifCarousel.hasClass("slick-initialized")) {
      motifCarousel.slick("unslick");
    }
    motifCarousel.empty();

    $(".custom-nav-container").remove();

    selectedMotif = "";
    selectedMotifInput.val("");

    if (selectedUlosType) {
      try {
        const response = await fetch(
          `/get_motifs/?jenis_ulos=${selectedUlosType}`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch motif data from server.");
        }
        const motifsData = await response.json();

        if (motifsData.length > 0) {
          motifsData.forEach(function (motif) {
            const slide = $("<div>").addClass("motif-slide");
            const img = $("<img>")
              .attr("src", motif.src)
              .attr("alt", "Motif " + selectedUlosType)
              .attr("data-motif-id", motif.id);
            slide.append(img);
            motifCarousel.append(slide);
          });

          // Buat div container untuk tombol navigasi setelah carousel
          const customNavContainer = $(
            '<div class="custom-nav-container"></div>'
          );
          $(".motif-carousel-wrapper").append(customNavContainer);

          setTimeout(function () {
            motifCarousel.slick({
              dots: true, // Aktifkan dots navigasi
              infinite: true,
              speed: 300,
              slidesToShow: 3,
              slidesToScroll: 1,
              centerMode: true,
              focusOnSelect: true,
              arrows: true,
              appendArrows: $(".custom-nav-container"),
              prevArrow:
                '<button type="button" class="slick-prev">&#9664;</button>',
              nextArrow:
                '<button type="button" class="slick-next">&#9654;</button>',
              customPaging: function (slider, i) {
                // Hanya tampilkan 5 dots di tengah
                const totalSlides = slider.slideCount;
                const middleDot = Math.floor(totalSlides / 2);

                // Logika untuk menampilkan hanya 5 dots di tengah
                if (totalSlides <= 5) {
                  // Jika total slide <= 5, tampilkan semua dots
                  return '<button type="button"></button>';
                } else {
                  // Jika total slide > 5, hanya tampilkan 5 dots di tengah
                  const startDot = Math.max(0, middleDot - 2);
                  const endDot = Math.min(totalSlides - 1, middleDot + 2);

                  if (i >= startDot && i <= endDot) {
                    return '<button type="button"></button>';
                  } else {
                    return ""; // Tidak menampilkan dot ini
                  }
                }
              },
              responsive: [
                {
                  breakpoint: 768,
                  settings: {
                    slidesToShow: 2,
                    slidesToScroll: 1,
                    arrows: true,
                  },
                },
                {
                  breakpoint: 576,
                  settings: {
                    slidesToShow: 1,
                    slidesToScroll: 1,
                    arrows: true,
                  },
                },
              ],
            });

            // Add event handler for slide change
            motifCarousel.on(
              "afterChange",
              function (event, slick, currentSlide) {
                $(".motif-slide").removeClass("selected");
                $(slick.$slides[currentSlide]).addClass("selected");

                // Update selectedMotif
                const img = $(slick.$slides[currentSlide]).find("img");
                if (img.length) {
                  selectedMotif = img.data("motif-id");
                  selectedMotifInput.val(selectedMotif);
                }
              }
            );

            // Force a refresh to ensure proper rendering
            motifCarousel.slick("refresh");

            motifCarouselContainer.show();
            motifCarousel.attr("data-active-ulos", selectedUlosType);

            const firstMotif = motifsData[0];
            selectedMotif = firstMotif.id;
            selectedMotifInput.val(selectedMotif);

            // Select first slide after a short delay to ensure proper initialization
            setTimeout(function () {
              motifCarousel.find(".slick-slide:first").addClass("selected");
            }, 100);
          }, 50);
        } else {
          motifCarouselContainer.hide();
          errorMessage.text(
            "Tidak ada motif yang tersedia untuk jenis Ulos ini."
          );
        }
      } catch (error) {
        console.error("Error fetching motifs:", error);
        errorMessage.text("Failed to load motifs. Please try again.");
        motifCarouselContainer.hide();
      }
    } else {
      motifCarouselContainer.hide();
    }
  });

  $(document).on("click", ".motif-slide", function (e) {
    e.preventDefault();

    $(".motif-slide").removeClass("selected");
    $(this).addClass("selected");

    const img = $(this).find("img");
    if (img.length) {
      selectedMotif = img.data("motif-id");
      selectedMotifInput.val(selectedMotif);
    }

    errorMessage.text("");
  });

  function updateSelectedColorsDisplay() {
    selectedColorsContainer.empty();
    selectedColorCodes.forEach(function (code) {
      const colorObj = ulosColorsData.find((color) => color.code === code);
      if (colorObj) {
        const colorContainer = $("<div>").addClass("selected-color-container");
        const codeLabel = $("<div>").addClass("selected-color-name").text(code);
        const colorDiv = $("<div>")
          .addClass("selected-color-box")
          .css("background-color", colorObj.hex_color);
        const removeBtn = $("<span>")
          .addClass("remove-color-btn")
          .html("&times;")
          .attr("data-code", colorObj.code);

        colorContainer.append(codeLabel);
        colorContainer.append(colorDiv);
        colorDiv.append(removeBtn);
        selectedColorsContainer.append(colorContainer);
      }
    });
    colorCounter.text(`${selectedColorCodes.length} warna dipilih`);
    selectedColorsInput.val(selectedColorCodes.join(","));
  }

  if (selectedColorsInput.val()) {
    selectedColorCodes = selectedColorsInput.val().split(",").filter(Boolean);
    selectedColorCodes.forEach((code) => {
      $(`.color-box[data-code="${code}"]`).addClass("selected");
    });
    updateSelectedColorsDisplay();
  }

  $(document).on("click", ".remove-color-btn", function () {
    const colorCodeToRemove = $(this).attr("data-code");
    selectedColorCodes = selectedColorCodes.filter(
      (code) => code !== colorCodeToRemove
    );
    $(`.color-box[data-code="${colorCodeToRemove}"]`).removeClass("selected");
    updateSelectedColorsDisplay();
  });

  // ===== MODIFIKASI: Handler submit form untuk menampilkan LOADING SPINNER + LOADING BAR =====
  coloringForm.on("submit", async function (e) {
    e.preventDefault();

    // Reset UI
    errorMessage.text("");
    coloredImage.hide();
    noImageMessage.show();
    downloadImageBtn.hide();
    downloadPdfBtn.hide();
    usedColorsDisplay.hide();
    actualUsedColorsPalette.empty();

    // Validasi input di frontend
    if (
      !$("#jenisUlos").val() ||
      !selectedMotifInput.val() ||
      selectedColorCodes.length < 2
    ) {
      errorMessage.text("Harap pilih Jenis Ulos, Motif, dan minimal 2 warna.");
      return;
    }

    // Tampilkan UI loading
    loadingSpinner.show();
    loadingBarContainer.show();
    updateLoadingBar(0);
    submitButton.prop("disabled", true);

    const formData = new FormData(this);
    let pollInterval;

    // Fungsi untuk menghentikan semua proses loading di UI
    function stopLoading() {
      if (pollInterval) clearInterval(pollInterval);
      loadingSpinner.hide();
      setTimeout(() => {
        loadingBarContainer.hide();
        updateLoadingBar(0); // Reset bar untuk proses selanjutnya
      }, 1500); // Beri jeda 1.5 detik agar user bisa lihat 100%
      submitButton.prop("disabled", false);
    }

    // Fungsi untuk polling progres ke server
    function pollProgress(taskId) {
      pollInterval = setInterval(async () => {
        try {
          // Tanya ke server "bagaimana progres task ini?"
          const response = await fetch(`/pewarnaan/progress/${taskId}/`);
          if (!response.ok) {
            throw new Error(
              `Polling failed: Server responded with status ${response.status}`
            );
          }
          const data = await response.json();

          // Update loading bar sesuai data dari server
          updateLoadingBar(data.progress || 0);

          // Cek jika proses sudah 100% (selesai atau error)
          if (data.progress >= 100) {
            clearInterval(pollInterval); // Hentikan polling

            if (data.status === "Completed") {
              // Jika sukses, tampilkan semua hasilnya
              const imageUrl = "/static/" + data.colored_image_url;
              coloredImage.attr("src", imageUrl).show();
              noImageMessage.hide();
              downloadImageBtn.attr("href", imageUrl);
              downloadImageBtn.show();
              downloadPdfBtn.show();

              if (data.used_colors && data.used_colors.length > 0) {
                actualUsedColorsPalette.empty();
                data.used_colors.forEach(function (color) {
                  const colorItem = $("<div>")
                    .addClass("used-color-item")
                    .attr("title", `Code: ${color.code}`);
                  const colorBox = $("<div>")
                    .addClass("used-color-box")
                    .css("background-color", color.hex_color);
                  const colorCodeLabel = $("<div>")
                    .addClass("used-color-code")
                    .text(color.code);
                  colorItem.append(colorBox).append(colorCodeLabel);
                  actualUsedColorsPalette.append(colorItem);
                });
                usedColorsDisplay.show();
              }
            } else {
              // Jika selesai dengan error, tampilkan pesan error
              errorMessage.text(
                `Error: ${data.error || "Terjadi kesalahan tidak diketahui."}`
              );
            }

            // Apapun hasilnya (sukses/error), hentikan UI loading
            stopLoading();
          }
        } catch (error) {
          console.error("Polling error:", error);
          errorMessage.text(
            "Gagal terhubung ke server untuk update progres. Coba lagi."
          );
          stopLoading();
        }
      }, 2000); // Polling setiap 2 detik
    }

    // === Langkah Utama saat tombol disubmit ===
    try {
      // 1. Kirim request untuk MEMULAI proses pewarnaan
      const initialResponse = await fetch("/pewarnaan/", {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (!initialResponse.ok) {
        const errorData = await initialResponse.json();
        throw new Error(
          errorData.error || "Gagal memulai proses pewarnaan di server."
        );
      }

      const initialData = await initialResponse.json();

      // 2. Jika server merespon dengan task_id, mulai polling
      if (initialData.task_id) {
        pollProgress(initialData.task_id);
      } else {
        throw new Error(
          "Server tidak memberikan Task ID. Proses tidak bisa dilanjutkan."
        );
      }
    } catch (error) {
      console.error("Submission error:", error);
      errorMessage.text(error.message);
      stopLoading();
    }
  });
});
