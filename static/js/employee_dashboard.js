document.addEventListener("DOMContentLoaded", function () {
    const btnDepart = document.getElementById("btn-depart");
    const hint = document.getElementById("depart-hint");
    if (!btnDepart) return;

    const availableAt = btnDepart.getAttribute("data-available-at");
    if (!availableAt) return;

    const targetTime = new Date(availableAt).getTime();

    function updateCountdown() {
        const diff = targetTime - Date.now();

        if (diff <= 0) {
            btnDepart.disabled = false;
            if (hint) hint.textContent = "Vous pouvez pointer votre départ";
            clearInterval(interval);
            return;
        }

        const minutes = Math.floor(diff / 60000);
        const seconds = Math.floor((diff % 60000) / 1000);
        if (hint) {
            hint.textContent = `Disponible dans ${minutes}m ${seconds.toString().padStart(2, "0")}s`;
        }
    }

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
});

// --- Horloge en temps réel ---
document.addEventListener("DOMContentLoaded", function () {
    const horlogeEl = document.getElementById("horloge-live");
    if (!horlogeEl) return;

    function pad(n) {
        return n.toString().padStart(2, "0");
    }

    function updateHorloge() {
        const now = new Date();
        horlogeEl.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    }

    updateHorloge();
    setInterval(updateHorloge, 1000);
});