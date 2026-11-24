const demoUserNameKey = "plp.demoUserName";
const themeStorageKey = "plp.theme";

function updateHeader() {
    const storedUserName = localStorage.getItem(demoUserNameKey);
    const userName = document.getElementById("userName");
    const loginButton = document.getElementById("loginButton");
    const registerButton = document.getElementById("registerButton");
    const logoutButton = document.getElementById("logoutButton");
    const pdpImage = document.getElementById("userPDP");
    const exos1Button = document.getElementById("exos1B");
    const exos2Button = document.getElementById("exos2B");
    const exos3Button = document.getElementById("exos3B");
    const exosButton = document.getElementById("ExercicesButton");

    if (userName) {
        userName.textContent = storedUserName || "";
        userName.hidden = !storedUserName;
    }
    if (loginButton) {
        loginButton.hidden = Boolean(storedUserName);
    }
    if (exosButton) {
        exosButton.hidden = !storedUserName;
    }
    if (registerButton) {
        registerButton.hidden = Boolean(storedUserName);
    }
    if (pdpImage){
        registerButton.hidden = Boolean(storedUserName);
        pdpImage.hidden = !storedUserName;
    }
    if (exos1Button){
        registerButton.hidden = Boolean(storedUserName);
        exos1Button.hidden = !storedUserName;
        exos2Button.hidden = !storedUserName;
        exos3Button.hidden = !storedUserName;
    }

    if (logoutButton) {
        logoutButton.hidden = !storedUserName;
        logoutButton.addEventListener("click", () => {
            localStorage.removeItem(demoUserNameKey);
            window.location.href = "/index.html";
        });
    }

    const logo = document.getElementById("logo");
    if (logo) {
        logo.addEventListener("click", () => {
            window.location.href = "/index.html";
        });
        logo.style.cursor = "pointer";
    }

    const logoMini = document.getElementById("logoMini");
    if (logoMini) {
        logoMini.addEventListener("click", () => {
            window.location.href = "/index.html";
        });
        logoMini.style.cursor = "pointer";
    }
}

function saveDemoSession(userName) {
    localStorage.setItem(demoUserNameKey, userName);
    window.location.href = "exosR.html";
}

function configureLoginForm() {
    const form = document.getElementById("loginForm");
    if (!form) {
        return;
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const email = form.elements.email.value.trim();
        saveDemoSession(email.split("@")[0] || "Utilisateur");
    });
}

function configureMobileHeader() {
    const menuButton = document.getElementById("menuButton");
    const menu = document.getElementById("headerMenu");
    if (!menuButton || !menu) {
        return;
    }

    const closeMenu = () => {
        menuButton.setAttribute("aria-expanded", "false");
        menuButton.setAttribute("aria-label", "Ouvrir le menu");
        menu.classList.remove("is-open");
    };

    menuButton.addEventListener("click", () => {
        const isOpen = menuButton.getAttribute("aria-expanded") === "true";
        menuButton.setAttribute("aria-expanded", String(!isOpen));
        menuButton.setAttribute("aria-label", isOpen ? "Ouvrir le menu" : "Fermer le menu");
        menu.classList.toggle("is-open", !isOpen);
    });

    menu.addEventListener("click", (event) => {
        if (event.target.closest("button")) {
            closeMenu();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 700) {
            closeMenu();
        }
    });
}

function configureSettingsPanel() {
    const settingsButton = document.getElementById("settingsButton");
    const settingsPanel = document.getElementById("settingsPanel");
    const settingsContent = document.getElementById("settingsContent");
    if (!settingsButton || !settingsPanel || !settingsContent) {
        return;
    }

    settingsButton.addEventListener("click", () => {
        const isOpen = settingsButton.getAttribute("aria-expanded") === "true";
        settingsButton.setAttribute("aria-expanded", String(!isOpen));
        settingsButton.setAttribute("aria-label", isOpen ? "Ouvrir les paramètres" : "Fermer les paramètres");
        settingsContent.setAttribute("aria-hidden", String(isOpen));
        settingsPanel.classList.toggle("is-open", !isOpen);
    });
}

function configureTheme() {
    const themeSelect = document.getElementById("themeSelect");
    if (!themeSelect) {
        return;
    }

    const savedTheme = localStorage.getItem(themeStorageKey)
        ?? localStorage.getItem("plp.homeTheme");
    const theme = savedTheme === "dark" ? "dark" : "light";
    document.body.dataset.theme = theme;
    themeSelect.value = theme;

    themeSelect.addEventListener("change", () => {
        const selectedTheme = themeSelect.value === "dark" ? "dark" : "light";
        document.body.dataset.theme = selectedTheme;
        localStorage.setItem(themeStorageKey, selectedTheme);
    });
}

function configureRegisterForm() {
    const form = document.getElementById("registerForm");
    if (!form) {
        return;
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();

        const password = form.elements.password;
        const confirmPassword = form.elements.confirmPassword;
        if (password.value !== confirmPassword.value) {
            confirmPassword.setCustomValidity("Les mots de passe ne correspondent pas.");
            confirmPassword.reportValidity();
            confirmPassword.setCustomValidity("");
            return;
        }

        saveDemoSession(form.elements.username.value.trim() || "Utilisateur");
    });
}

function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const checkboxId = inputId === "confirmPassword" ? "showConfirmPassword" : "showPassword";
    const checkbox = document.getElementById(checkboxId);
    if (input && checkbox) {
        input.type = checkbox.checked ? "text" : "password";
    }
}

window.togglePasswordVisibility = togglePasswordVisibility;

updateHeader();
configureMobileHeader();
configureSettingsPanel();
configureTheme();
configureLoginForm();
configureRegisterForm();
