// Aktualizuje percento vedľa slideru
const powerSlider = document.getElementById("power");
const powerVal = document.getElementById("powerVal");

powerSlider.addEventListener("input", () => {
    powerVal.innerText = powerSlider.value + "%";
});

// Ukladanie nastavení cez POST
function saveSettings() {
    const data = {
        rtc: document.getElementById("rtc").value,
        onTime: document.getElementById("onTime").value,
        offTime: document.getElementById("offTime").value,
        power: document.getElementById("power").value
    };

    fetch("/save", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    })
    .then(response => response.text())
    .then(text => {
        document.getElementById("statusMsg").innerText = text;
        console.log("💾 Nastavenia uložené:", data);
    })
    .catch(err => {
        document.getElementById("statusMsg").innerText = "Chyba: " + err;
        console.error(err);
    });
}
