const API_BASE = '/api/v1';

const DOM = {
    employeeGrid: document.getElementById('employee-grid'),
    deptFilter: document.getElementById('department-filter'),
    btnAdd: document.getElementById('btn-add'),
    drawerOverlay: document.getElementById('drawer-overlay'),
    drawer: document.getElementById('drawer'),
    btnDrawerClose: document.getElementById('btn-drawer-close'),
    formEmployee: document.getElementById('form-employee'),
    photoInput: document.getElementById('photo'),
    photoPreview: document.getElementById('photo-preview'),
    deptSelect: document.getElementById('department_id'),
    
    // Navigation and sections
    navEmployees: document.getElementById('nav-employees'),
    navDepartments: document.getElementById('nav-departments'),
    sectionEmployees: document.getElementById('section-employees'),
    sectionDepartments: document.getElementById('section-departments'),
    
    // Department elements
    btnAddDept: document.getElementById('btn-add-dept'),
    drawerOverlayDept: document.getElementById('drawer-overlay-dept'),
    drawerDept: document.getElementById('drawer-dept'),
    btnDrawerCloseDept: document.getElementById('btn-drawer-close-dept'),
    formDepartment: document.getElementById('form-department'),
    deptTableBody: document.getElementById('dept-table-body'),
    
    modalOverlay: document.getElementById('modal-overlay'),
    modal: document.getElementById('modal'),
    btnModalClose: document.getElementById('btn-modal-close'),
    modalName: document.getElementById('modal-name'),
    modalPhoto: document.getElementById('modal-photo'),
    modalEmail: document.getElementById('modal-email'),
    modalDept: document.getElementById('modal-department'),
    modalPhone: document.getElementById('modal-phone'),
    modalAddress: document.getElementById('modal-address'),
    modalBirthDate: document.getElementById('modal-birth-date'),
    timeline: document.getElementById('timeline')
};

let employees = [];
let departments = [];

// Init
async function init() {
    showSkeletons();
    await fetchDepartments();
    await fetchEmployees();
    setupEventListeners();
}

async function fetchDepartments() {
    try {
        const res = await fetch(`${API_BASE}/departments`);
        departments = await res.json();
        
        DOM.deptFilter.innerHTML = '<option value="">All Departments</option>';
        DOM.deptSelect.innerHTML = '<option value="">Select a department</option>';
        DOM.deptTableBody.innerHTML = '';
        
        departments.forEach(dept => {
            DOM.deptFilter.innerHTML += `<option value="${dept.id}">${dept.name}</option>`;
            DOM.deptSelect.innerHTML += `<option value="${dept.id}">${dept.name}</option>`;
            
            const createdDate = new Date(dept.created_at).toLocaleDateString('ja-JP', {
                year: 'numeric', month: '2-digit', day: '2-digit'
            });
            DOM.deptTableBody.innerHTML += `
                <tr>
                    <td><strong>${dept.code}</strong></td>
                    <td>${dept.name}</td>
                    <td>${createdDate}</td>
                </tr>
            `;
        });
    } catch (e) {
        console.error('Failed to fetch departments', e);
    }
}

async function fetchEmployees() {
    try {
        const deptId = DOM.deptFilter.value;
        const url = deptId ? `${API_BASE}/employees?department_id=${deptId}` : `${API_BASE}/employees`;
        const res = await fetch(url);
        employees = await res.json();
        renderEmployees();
    } catch (e) {
        console.error('Failed to fetch employees', e);
        DOM.employeeGrid.innerHTML = '<p style="color:var(--danger)">Error loading data.</p>';
    }
}

function showSkeletons() {
    DOM.employeeGrid.innerHTML = Array(8).fill(0).map(() => `
        <div class="skeleton-card">
            <div class="skeleton skeleton-photo"></div>
            <div class="card-info">
                <div class="skeleton skeleton-text-1"></div>
                <div class="skeleton skeleton-text-2"></div>
            </div>
        </div>
    `).join('');
}

function renderEmployees() {
    if (employees.length === 0) {
        DOM.employeeGrid.innerHTML = '<p>No employees found.</p>';
        return;
    }

    DOM.employeeGrid.innerHTML = employees.map(emp => `
        <div class="card" onclick="openEmployeeModal(${emp.id})">
            ${emp.photo_url 
                ? `<img src="${emp.photo_url}" class="card-photo" alt="${emp.last_name} ${emp.first_name}" onerror="this.src=''; this.style.display='none'">` 
                : `<div class="card-photo"></div>`}
            <div class="card-info">
                <div class="card-name">${emp.last_name} ${emp.first_name}</div>
                <div class="card-dept">${emp.department ? emp.department.name : 'No Department'}</div>
            </div>
        </div>
    `).join('');
}

async function openEmployeeModal(id) {
    try {
        const res = await fetch(`${API_BASE}/employees/${id}`);
        const emp = await res.json();
        
        DOM.modalName.textContent = `${emp.last_name} ${emp.first_name}`;
        DOM.modalEmail.textContent = `Email: ${emp.email}`;
        DOM.modalDept.textContent = `Department: ${emp.department ? emp.department.name : 'N/A'}`;
        DOM.modalPhone.textContent = emp.phone ? `Phone: ${emp.phone}` : 'Phone: N/A';
        DOM.modalAddress.textContent = emp.address ? `Address: ${emp.address}` : 'Address: N/A';
        DOM.modalBirthDate.textContent = emp.birth_date ? `Birth Date: ${emp.birth_date}` : 'Birth Date: N/A';
        
        if (emp.photo_url) {
            DOM.modalPhoto.src = emp.photo_url;
            DOM.modalPhoto.style.display = 'block';
        } else {
            DOM.modalPhoto.style.display = 'none';
        }

        // Render timeline using histories
        if (emp.histories && emp.histories.length > 0) {
            // Sort histories by start_date descending
            const sortedHist = [...emp.histories].sort((a, b) => new Date(b.start_date) - new Date(a.start_date));
            DOM.timeline.innerHTML = sortedHist.map(h => {
                const dept = departments.find(d => d.id === h.department_id);
                const deptName = dept ? dept.name : '不明な部署';
                const period = h.end_date ? `${h.start_date} ~ ${h.end_date}` : `${h.start_date} ~ 現在`;
                return `
                    <div class="timeline-item">
                        <div class="timeline-date">${period}</div>
                        <div class="timeline-content">${deptName} - ${h.role}</div>
                    </div>
                `;
            }).join('');
        } else {
            DOM.timeline.innerHTML = '<p>No history available.</p>';
        }

        DOM.modalOverlay.classList.add('active');
        DOM.modal.classList.add('active');
    } catch (e) {
        console.error('Failed to load employee details', e);
    }
}

// Event Listeners
function setupEventListeners() {
    // Navigation Switching
    DOM.navEmployees.addEventListener('click', (e) => {
        e.preventDefault();
        DOM.sectionEmployees.style.display = 'block';
        DOM.sectionDepartments.style.display = 'none';
        DOM.navEmployees.classList.add('active');
        DOM.navDepartments.classList.remove('active');
    });

    DOM.navDepartments.addEventListener('click', (e) => {
        e.preventDefault();
        DOM.sectionEmployees.style.display = 'none';
        DOM.sectionDepartments.style.display = 'block';
        DOM.navEmployees.classList.remove('active');
        DOM.navDepartments.classList.add('active');
    });

    // Drawer (Employee)
    DOM.btnAdd.addEventListener('click', () => {
        DOM.drawerOverlay.classList.add('active');
        DOM.drawer.classList.add('active');
    });

    [DOM.btnDrawerClose, DOM.drawerOverlay].forEach(el => {
        el.addEventListener('click', () => {
            DOM.drawerOverlay.classList.remove('active');
            DOM.drawer.classList.remove('active');
            DOM.formEmployee.reset();
            DOM.photoPreview.style.backgroundImage = 'none';
            DOM.photoPreview.textContent = 'Preview';
        });
    });

    // Drawer (Department)
    DOM.btnAddDept.addEventListener('click', () => {
        DOM.drawerOverlayDept.style.display = 'block';
        DOM.drawerDept.classList.add('active');
    });

    [DOM.btnDrawerCloseDept, DOM.drawerOverlayDept].forEach(el => {
        el.addEventListener('click', () => {
            DOM.drawerOverlayDept.style.display = 'none';
            DOM.drawerDept.classList.remove('active');
            DOM.formDepartment.reset();
        });
    });

    // Modal
    [DOM.btnModalClose, DOM.modalOverlay].forEach(el => {
        el.addEventListener('click', () => {
            DOM.modalOverlay.classList.remove('active');
            DOM.modal.classList.remove('active');
        });
    });

    // Filter
    DOM.deptFilter.addEventListener('change', () => {
        showSkeletons();
        fetchEmployees();
    });

    // Photo Preview
    DOM.photoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                DOM.photoPreview.style.backgroundImage = `url(${e.target.result})`;
                DOM.photoPreview.textContent = '';
            };
            reader.readAsDataURL(file);
        }
    });

    // Form Submit (Employee)
    DOM.formEmployee.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(DOM.formEmployee);
        const submitBtn = DOM.formEmployee.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';

        try {
            const res = await fetch(`${API_BASE}/employees`, {
                method: 'POST',
                body: formData
            });

            if (res.ok) {
                DOM.btnDrawerClose.click();
                showSkeletons();
                fetchEmployees();
            } else {
                alert('Failed to save employee');
            }
        } catch (error) {
            console.error('Error saving employee', error);
            alert('An error occurred.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save';
        }
    });

    // Form Submit (Department)
    DOM.formDepartment.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const code = document.getElementById('dept_code').value.trim();
        const name = document.getElementById('dept_name').value.trim();
        const submitBtn = DOM.formDepartment.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';

        try {
            const res = await fetch(`${API_BASE}/departments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, name })
            });

            if (res.ok) {
                DOM.btnDrawerCloseDept.click();
                await fetchDepartments();
            } else {
                const data = await res.json();
                alert(`Failed to save department: ${data.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error saving department', error);
            alert('An error occurred.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save';
        }
    });
}

// Start
init();
