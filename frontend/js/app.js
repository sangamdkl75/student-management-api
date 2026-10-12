const API_URL = "https://student-management-backend-gilt.vercel.app";

let currentUser = null;


/* =========================
   PAGE CONTROL
========================= */

function showPage(pageId) {
    document.querySelectorAll(".page").forEach(page => {
        page.classList.add("hidden");
    });

    document.getElementById("dashboard-page").classList.add("hidden");

    document.getElementById(pageId).classList.remove("hidden");
}


/* =========================
   LOGIN
========================= */

document.getElementById("login-form").addEventListener("submit", async function (event) {

    event.preventDefault();

    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    const message = document.getElementById("login-message");

    const formData = new URLSearchParams();

    formData.append("username", username);
    formData.append("password", password);

    try {

        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Login failed");
        }

        localStorage.setItem("access_token", data.access_token);

        currentUser = username;

        document.getElementById("current-user").textContent =
            `Welcome, ${username}`;

        showDashboard();

    } catch (error) {

        message.textContent = error.message;
        message.style.color = "red";
    }
});


/* =========================
   REGISTER
========================= */

document.getElementById("register-form").addEventListener("submit", async function (event) {

    event.preventDefault();

    const username =
        document.getElementById("register-username").value;

    const password =
        document.getElementById("register-password").value;

    const message =
        document.getElementById("register-message");

    try {

        const response = await fetch(`${API_URL}/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Registration failed");
        }

        message.textContent =
            "Registration successful. You can now login.";

        message.style.color = "green";

        document.getElementById("register-form").reset();

    } catch (error) {

        message.textContent = error.message;
        message.style.color = "red";
    }
});


/* =========================
   DASHBOARD
========================= */

function showDashboard() {

    document.querySelectorAll(".page").forEach(page => {
        page.classList.add("hidden");
    });

    document.getElementById("dashboard-page")
        .classList.remove("hidden");

    loadStudents();
}


/* =========================
   GET STUDENTS
========================= */

async function loadStudents() {

    const token = localStorage.getItem("access_token");

    if (!token) {
        showPage("login-page");
        return;
    }

    const loading = document.getElementById("loading");
    const tableBody = document.getElementById("student-table-body");
    const emptyState = document.getElementById("empty-state");

    loading.classList.remove("hidden");
    emptyState.classList.add("hidden");

    tableBody.innerHTML = "";

    try {

        const response = await fetch(`${API_URL}/students/`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Failed to load students");
        }

        if (data.length === 0) {
            emptyState.classList.remove("hidden");
            return;
        }

        data.forEach(student => {

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${student.id}</td>
                <td>${escapeHtml(student.name)}</td>
                <td>${student.age}</td>
                <td>${escapeHtml(student.course)}</td>

                <td>
                    <div class="action-buttons">

                        <button
                            class="edit-btn"
                            onclick="editStudent(${student.id})"
                        >
                            Edit
                        </button>

                        <button
                            class="delete-btn"
                            onclick="deleteStudent(${student.id})"
                        >
                            Delete
                        </button>

                    </div>
                </td>
            `;

            tableBody.appendChild(row);
        });

    } catch (error) {

        showDashboardMessage(error.message, "red");

    } finally {

        loading.classList.add("hidden");
    }
}


/* =========================
   ADD / EDIT FORM
========================= */

function showStudentForm() {

    document.getElementById("student-form-container")
        .classList.remove("hidden");

    document.getElementById("student-form-title")
        .textContent = "Add Student";

    document.getElementById("student-form").reset();

    document.getElementById("student-id").value = "";
}


function hideStudentForm() {

    document.getElementById("student-form-container")
        .classList.add("hidden");

}


/* =========================
   SAVE STUDENT
========================= */

document.getElementById("student-form").addEventListener("submit", async function (event) {

    event.preventDefault();

    const token = localStorage.getItem("access_token");

    const id = document.getElementById("student-id").value;

    const student = {

        name: document.getElementById("student-name").value,

        age: Number(
            document.getElementById("student-age").value
        ),

        course: document.getElementById("student-course").value
    };

    const isEditing = id !== "";

    const url = isEditing
        ? `${API_URL}/students/${id}`
        : `${API_URL}/students/`;

    const method = isEditing
        ? "PUT"
        : "POST";

    try {

        const response = await fetch(url, {

            method: method,

            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },

            body: JSON.stringify(student)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Operation failed");
        }

        hideStudentForm();

        showDashboardMessage(
            isEditing
                ? "Student updated successfully"
                : "Student created successfully",
            "green"
        );

        loadStudents();

    } catch (error) {

        showDashboardMessage(error.message, "red");
    }
});


/* =========================
   EDIT STUDENT
========================= */

async function editStudent(id) {

    const token = localStorage.getItem("access_token");

    try {

        const response = await fetch(
            `${API_URL}/students/${id}`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const student = await response.json();

        if (!response.ok) {
            throw new Error(
                student.detail || "Failed to get student"
            );
        }

        document.getElementById("student-form-container")
            .classList.remove("hidden");

        document.getElementById("student-form-title")
            .textContent = "Edit Student";

        document.getElementById("student-id").value =
            student.id;

        document.getElementById("student-name").value =
            student.name;

        document.getElementById("student-age").value =
            student.age;

        document.getElementById("student-course").value =
            student.course;

    } catch (error) {

        showDashboardMessage(error.message, "red");
    }
}


/* =========================
   DELETE STUDENT
========================= */

async function deleteStudent(id) {

    const confirmed =
        confirm("Are you sure you want to delete this student?");

    if (!confirmed) {
        return;
    }

    const token = localStorage.getItem("access_token");

    try {

        const response = await fetch(
            `${API_URL}/students/${id}`,
            {
                method: "DELETE",

                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to delete student"
            );
        }

        showDashboardMessage(
            "Student deleted successfully",
            "green"
        );

        loadStudents();

    } catch (error) {

        showDashboardMessage(error.message, "red");
    }
}


/* =========================
   LOGOUT
========================= */

function logout() {

    localStorage.removeItem("access_token");

    currentUser = null;

    document.getElementById("login-form").reset();

    showPage("login-page");
}


/* =========================
   MESSAGES
========================= */

function showDashboardMessage(message, color) {

    const element =
        document.getElementById("dashboard-message");

    element.textContent = message;
    element.style.color = color;

    setTimeout(() => {
        element.textContent = "";
    }, 4000);
}


/* =========================
   SECURITY HELPER
========================= */

function escapeHtml(value) {

    const div = document.createElement("div");

    div.textContent = value;

    return div.innerHTML;
}


/* =========================
   CHECK LOGIN ON START
========================= */

window.addEventListener("load", function () {

    const token = localStorage.getItem("access_token");

    if (token) {
        showDashboard();
    } else {
        showPage("login-page");
    }

});