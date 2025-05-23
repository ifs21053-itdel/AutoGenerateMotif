// static/pewarnaan.js

document.addEventListener('DOMContentLoaded', function() {
    const colorButtons = document.querySelectorAll('.color-btn');
    const selectedColorsContainer = document.getElementById('selectedColorsContainer');
    const selectedColorsInput = document.getElementById('selectedColors');
    const colorCounter = document.getElementById('colorCounter');
    
    let selectedColors = [];
    const maxColors = 10;
    
    // Function to update the selected colors display
    function updateSelectedColorsDisplay() {
        // Clear the container
        selectedColorsContainer.innerHTML = '';
        
        // Add each selected color
        selectedColors.forEach((color, index) => {
            const colorItem = document.createElement('div');
            colorItem.className = 'selected-color-item';
            colorItem.style.backgroundColor = color;
            
            // Add remove button
            const removeBtn = document.createElement('div');
            removeBtn.className = 'remove-btn';
            removeBtn.innerHTML = '×';
            removeBtn.addEventListener('click', function() {
                removeColor(index);
            });
            
            colorItem.appendChild(removeBtn);
            selectedColorsContainer.appendChild(colorItem);
        });
        
        // Update the counter
        colorCounter.textContent = `${selectedColors.length}/${maxColors} warna dipilih`;
        
        // Update the hidden input value
        selectedColorsInput.value = JSON.stringify(selectedColors);
    }
    
    // Function to add a color
    function addColor(color) {
        if (selectedColors.length < maxColors && !selectedColors.includes(color)) {
            selectedColors.push(color);
            updateSelectedColorsDisplay();
            return true;
        }
        return false;
    }
    
    // Function to remove a color
    function removeColor(index) {
        selectedColors.splice(index, 1);
        updateSelectedColorsDisplay();
        
        // Update button UI - remove selected class from unselected colors
        colorButtons.forEach(btn => {
            const btnColor = btn.getAttribute('data-color');
            if (!selectedColors.includes(btnColor)) {
                btn.classList.remove('selected');
            }
        });
    }
    
    // Add click event to color buttons
    colorButtons.forEach(button => {
        button.addEventListener('click', function() {
            const color = this.getAttribute('data-color');
            
            // If color is already selected, remove it
            const colorIndex = selectedColors.indexOf(color);
            if (colorIndex !== -1) {
                removeColor(colorIndex);
                this.classList.remove('selected');
            } 
            // Otherwise, add it if possible
            else if (addColor(color)) {
                this.classList.add('selected');
            }
        });
    });
    
    // Initialize display
    updateSelectedColorsDisplay();
});