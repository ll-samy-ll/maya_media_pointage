document.addEventListener("DOMContentLoaded", function () {
    const overlay = document.getElementById("loader-overlay");
    if (!overlay) return;

    function showLoader() {
        overlay.classList.add("show");
    }

    // --- Déclenchement sur soumission de formulaire ---
    document.querySelectorAll("form").forEach(function (form) {
        form.addEventListener("submit", function () {
            // Ne pas bloquer si le formulaire est invalide (validation HTML5)
            if (form.checkValidity && !form.checkValidity()) return;
            showLoader();
        });
    });

    // --- Déclenchement sur clic de lien de navigation ---
    document.querySelectorAll("a[href]").forEach(function (link) {
        const href = link.getAttribute("href");

        // On ignore les ancres, les liens externes/nouvel onglet, et les
        // déclencheurs de modales/onglets Bootstrap (qui ne rechargent pas la page)
        if (
            !href ||
            href.startsWith("#") ||
            href.startsWith("javascript:") ||
            link.target === "_blank" ||
            link.hasAttribute("data-bs-toggle") ||
            link.hasAttribute("data-bs-dismiss")
        ) {
            return;
        }

        link.addEventListener("click", function () {
            showLoader();
        });
    });

    // Sécurité : si jamais la page reste bloquée (retour navigateur, cache),
    // on masque le loader après un délai raisonnable.
    window.addEventListener("pageshow", function () {
        overlay.classList.remove("show");
    });
});