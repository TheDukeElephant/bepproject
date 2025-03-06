// Only keep toggleDevice & remove slider references for pump or ITO
function toggleDevice(deviceId) {
    const button = document.getElementById(`${deviceId}-toggle`);
    const isOn = button.classList.toggle('on');
    button.textContent = isOn ? 'On' : 'Off';

    // Hidden input update
    const stateInput = document.getElementById(`${deviceId}_state`);
    if (stateInput) {
        stateInput.value = isOn ? 'on' : 'off';
    }

    fetch('/toggle-device', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device: deviceId, state: isOn ? 'on' : 'off' }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(`Device ${deviceId} toggled to ${data.state}`);
        } else {
            console.error(`Error toggling ${deviceId}:`, data.error);
            alert(`Failed to toggle device: ${data.error}`);
        }
    })
    .catch(error => {
        console.error(`Error toggling device ${deviceId}:`, error);
        alert(`An error occurred: ${error.message}`);
    });
}
