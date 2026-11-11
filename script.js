const demoUserNameKey = "plp.demoUserName";

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

    if (userName) {
        userName.textContent = storedUserName || "";
        userName.hidden = !storedUserName;
    }
    if (loginButton) {
        loginButton.hidden = Boolean(storedUserName);
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
            window.location.href = "index.html";
        });
    }

    const logo = document.getElementById("logo");
    if (logo) {
        logo.addEventListener("click", () => {
            window.location.href = "index.html";
        });
        logo.style.cursor = "pointer";
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
configureLoginForm();
configureRegisterForm();
