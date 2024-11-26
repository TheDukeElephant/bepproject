
function toggleDevice(deviceId) {
    const button = document.getElementById(`${deviceId}-toggle`);
    const isOn = button.classList.toggle('on');
    button.textContent = isOn ? 'On' : 'Off';

    // Send the toggle state to the server (this is a placeholder, you need to implement the server-side logic)
    fetch(`/toggle-device`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ device: deviceId, state: isOn ? 'on' : 'off' }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
// Adjust the value of the input field by a specified step
// Adjust the value of the input field by a specified step
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
    if (min !== undefined) newValue = Math.max(newValue, min);
    if (max !== undefined) newValue = Math.min(newValue, max);

    // Set the rounded value back to the input
    input.value = newValue;
}

