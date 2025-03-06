// Toggle the state of a relay or device
function toggleDevice(deviceId) {
    const button = document.getElementById(`${deviceId}-toggle`);
    const isOn = button.classList.toggle('on'); // Toggle the button's 'on' state
    button.textContent = isOn ? 'On' : 'Off'; // Update the button's label

    // Update the hidden input field for the device state
    const stateInput = document.getElementById(`${deviceId}_state`);
    if (stateInput) {
        stateInput.value = isOn ? 'on' : 'off';
    }

    console.log(`Toggling device: ${deviceId}, State: ${isOn ? 'on' : 'off'}`); // Debugging log

    // Send the toggle state to the server
    fetch(`/toggle-device`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ device: deviceId, state: isOn ? 'on' : 'off' }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log(`Device ${deviceId} toggled successfully: ${data.state}`);
            } else {
                console.error(`Error toggling device ${deviceId}:`, data.error);
                alert(`Failed to toggle device: ${data.error}`);
            }
        })
        .catch((error) => {
            console.error(`Error toggling device ${deviceId}:`, error);
            alert(`An error occurred: ${error.message}`);
        });
}


function updateDeviceSpeed(deviceId, speed) {
    console.log(`Updating speed for ${deviceId} to ${speed}%`); // Debugging log

    fetch(`/set-device-speed`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ device: deviceId, speed: speed }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log(`Speed for ${deviceId} updated successfully to ${speed}%`);
            } else {
                console.error(`Error updating speed for ${deviceId}:`, data.error);
                alert(`Failed to update speed: ${data.error}`);
            }
        })
        .catch((error) => {
            console.error(`Error updating speed for ${deviceId}:`, error);
            alert(`An error occurred: ${error.message}`);
        });
}

// Function to update slider value display
function updateSliderValue(sliderId, value) {
    const valueElement = document.getElementById(`${sliderId}-value`);
    if (valueElement) {
        valueElement.textContent = value; // Update the displayed value
    }
}


// Attach event listeners to sliders for real-time updates
document.querySelectorAll('.slider').forEach(slider => {
    slider.addEventListener('input', function () {
        // Map slider IDs to backend device names
        const sliderIdToDeviceMap = {
            'setpumpspeed': 'pump-ena',      // Map pump speed slider
            'settopito': 'ito-top-ena',     // Map ITO top speed slider
            'setbottomito': 'ito-bottom-ena' // Map ITO bottom speed slider
        };

        const deviceId = sliderIdToDeviceMap[this.id]; // Get the backend device name
        if (deviceId) {
            updateDeviceSpeed(deviceId, this.value); // Send the speed update to the server
        } else {
            console.error(`No mapping found for slider ID: ${this.id}`);
        }
    });
});

// Adjust the value of an input field by a specified step
function adjustValue(id, step) {
    const input = document.getElementById(id);
    let currentValue = parseFloat(input.value) || 0;
    const min = parseFloat(input.min);
    const max = parseFloat(input.max);

    // Calculate the new value
    let newValue = currentValue + step;

    // Round to one decimal place
    newValue = Math.round(newValue * 10) / 10;

    // Apply bounds
    if (!isNaN(min)) newValue = Math.max(newValue, min);
    if (!isNaN(max)) newValue = Math.min(newValue, max);

    // Set the rounded value back to the input
    input.value = newValue;
}

// Attach event listeners for increment and decrement buttons
document.querySelectorAll('.increment-button').forEach(button => {
    button.addEventListener('click', function () {
        const targetId = this.parentElement.querySelector('input').id;
        adjustValue(targetId, parseFloat(this.getAttribute('data-step')) || 1);
    });
});

document.querySelectorAll('.decrement-button').forEach(button => {
    button.addEventListener('click', function () {
        const targetId = this.parentElement.querySelector('input').id;
        adjustValue(targetId, -(parseFloat(this.getAttribute('data-step')) || 1));
    });
});
