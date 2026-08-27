document.addEventListener("DOMContentLoaded", function () {
    const inputs = document.querySelectorAll(".autocomplete-nom");
    if (inputs.length === 0) return;

    let allNoms = [];

    fetch("/auth/api/employe-noms")
        .then((res) => res.json())
        .then((data) => {
            allNoms = data;
        })
        .catch(() => {
            allNoms = [];
        });

    inputs.forEach(function (input) {
        const wrapper = input.closest(".autocomplete-wrapper");
        const list = wrapper.querySelector(".autocomplete-list");

        function closeList() {
            list.innerHTML = "";
            list.classList.remove("show");
        }

        input.addEventListener("input", function () {
            const value = input.value.trim().toLowerCase();
            closeList();

            if (!value) return;

            const matches = allNoms.filter((nom) =>
                nom.toLowerCase().includes(value)
            );

            if (matches.length === 0) return;

            matches.slice(0, 6).forEach(function (nom) {
                const item = document.createElement("button");
                item.type = "button";
                item.className = "autocomplete-item";
                item.textContent = nom;
                item.addEventListener("click", function () {
                    input.value = nom;
                    closeList();
                });
                list.appendChild(item);
            });

            list.classList.add("show");
        });

        // Ferme la liste si on clique ailleurs
        document.addEventListener("click", function (e) {
            if (!wrapper.contains(e.target)) {
                closeList();
            }
        });

        // Ferme la liste avec Échap
        input.addEventListener("keydown", function (e) {
            if (e.key === "Escape") closeList();
        });
    });
});