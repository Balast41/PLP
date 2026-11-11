async function injectComponent(selector, file) {
    const placeholder = document.querySelector(selector);
    if (!placeholder) {
        throw new Error(`Emplacement introuvable : ${selector}`);
    }

    const response = await fetch(file);
    if (!response.ok) {
        throw new Error(`Impossible de charger ${file} (${response.status})`);
    }

    placeholder.innerHTML = await response.text();
}

async function loadComponents() {
    await Promise.all([
        injectComponent("#site-header", "header.html"),
        injectComponent("#site-footer", "footer.html")
    ]);

    const pageScript = document.createElement("script");
    pageScript.src = "script.js";
    pageScript.onerror = () => console.error("Impossible de charger script.js");
    document.body.appendChild(pageScript);
}

loadComponents().catch((error) => {
    console.error("Erreur lors du chargement des éléments communs :", error);
    document.querySelectorAll("#site-header, #site-footer").forEach((placeholder) => {
        placeholder.textContent = "Impossible de charger cette partie de la page.";
    });
});
