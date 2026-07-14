
document.addEventListener("DOMContentLoaded", () => {
    // ==========================================
    // 백엔드 서버 기본 주소 설정 (Live Server 연동용)
    // ==========================================
    const BACKEND_URL = "http://127.0.0.1:8001";

    // ==========================================
    // 0. 글로벌 DOM 요소 선택 및 상태 관리
    // ==========================================
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const loginBtn = document.getElementById("login-btn");
    const signupBtn = document.getElementById("signup-btn");
    
    const authContainer = document.getElementById("auth-container"); // 로그인 창
    const appContainer = document.getElementById("app-container");   // 회원정보 관리 메인 창
    const contactList = document.getElementById("contact-list");     // 회원목록 컨테이너
    const categorySelect = document.getElementById("category-select");// 관계 선택창

    let currentCategories = []; // 관계 목록 캐싱용 array
// [Enter 키 로그인 기능 추가]
    const handleEnterLogin = (e) => {
        if (e.key === "Enter") {
            loginBtn.click(); // 기존 로그인 버튼 클릭 동작 실행
        }
    };

    usernameInput.addEventListener("keydown", handleEnterLogin);
    passwordInput.addEventListener("keydown", handleEnterLogin);
    // ==========================================
    // 1. 회원가입 및 즉시 화면 전환 (POST /auth/signup -> 자동 로그인)
    // ==========================================
    signupBtn.addEventListener("click", async () => {
        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username || !password) {
            alert("아이디와 비밀번호를 모두 입력해 주세요.");
            return;
        }

        try {
            // [Step 1] 회원가입 요청
            const response = await fetch(`${BACKEND_URL}/auth/signup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
                credentials: "include"
            });

            const text = await response.text();
            let data = {};
            try { data = JSON.parse(text); } catch (e) {}

            if (response.status === 201) {
                alert(`회원가입이 완료되었습니다!\n회원정보 관리 화면으로 즉시 전환합니다.`);
                
                // [Step 2] 회원가입 성공 즉시 자동 로그인 처리 (화면 전환 유도)
                const formData = new URLSearchParams();
                formData.append("username", username);
                formData.append("password", password);

                const loginResponse = await fetch(`${BACKEND_URL}/auth/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: formData.toString(),
                    credentials: "include"
                });

                if (loginResponse.ok) {
                    // 화면 전환: 로그인창 숨기고 메인화면 표시
                    if (authContainer) authContainer.style.display = "none";
                    if (appContainer) appContainer.style.display = "block";
                    
                    // 데이터 초기 로딩
                    await loadCategories();
                    await loadContacts();
                    
                    // 비밀번호 필드 초기화
                    passwordInput.value = "";
                } else {
                    alert("회원가입은 완료되었으나 자동 로그인에 실패했습니다. 수동으로 로그인해 주세요.");
                }
            } else if (response.status === 409) {
                alert(data.detail || "이미 존재하는 아이디입니다.");
            } else {
                alert(data.detail || "회원가입 중 에러가 발생했습니다.");
            }
        } catch (error) {
            console.error("Signup Error:", error);
            alert("백엔드 서버와 통신할 수 없습니다.");
        }
    });

    // ==========================================
    // 2. 로그인 비동기 연동 (POST /auth/login)
    // ==========================================
    loginBtn.addEventListener("click", async () => {
        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username || !password) {
            alert("아이디와 비밀번호를 입력해 주세요.");
            return;
        }

        try {
            const formData = new URLSearchParams();
            formData.append("username", username);
            formData.append("password", password);

            const response = await fetch(`${BACKEND_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData.toString(),
                credentials: "include"
            });

            const data = await response.json();

            if (response.ok) {
                alert("성공적으로 로그인되었습니다!");
                if (authContainer) authContainer.style.display = "none";
                if (appContainer) appContainer.style.display = "block";
                
                // 기존에 저장해둔 유저 고유의 정보 목록을 DB로부터 불러옴 (보존 확인)
                await loadCategories();
                await loadContacts();
            } else {
                alert(data.detail || "아이디 또는 비밀번호가 올바르지 않습니다.");
            }
        } catch (error) {
            console.error("Login Error:", error);
            alert("백엔드 서버와 통신할 수 없습니다.");
        }
    });

    // ==========================================
    // 3. 관계(카테고리) 목록 조회
    // ==========================================
    async function loadCategories() {
        if (!categorySelect) return;
        try {
            const response = await fetch(`${BACKEND_URL}/categories`, { credentials: "include" });
            if (response.ok) {
                currentCategories = await response.json();
                categorySelect.innerHTML = `<option value="">선택해주세요</option>` + 
                    currentCategories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join("");
            }
        } catch (error) {
            console.error("Load Categories Error:", error);
        }
    }

    // ==========================================
    // 4. 회원정보 목록 조회 및 렌더링
    // ==========================================
    async function loadContacts(searchKeyword = "") {
        if (!contactList) return;
        try {
            let url = `${BACKEND_URL}/contacts?page=1&limit=50`;
            if (searchKeyword) url += `&search=${encodeURIComponent(searchKeyword)}`;

            const response = await fetch(url, { credentials: "include" });
            if (response.ok) {
                const contacts = await response.json();
                
                if (contacts.length === 0) {
                    contactList.innerHTML = `<div class="empty-msg">등록된 회원 정보가 없습니다.</div>`;
                    return;
                }

                contactList.innerHTML = contacts.map(contact => {
                    const catObj = currentCategories.find(c => c.id === contact.category_id);
                    const categoryName = catObj ? catObj.name : "미분류";

                    return `
                        <div class="contact-card" data-id="${contact.id}">
                            <div class="contact-info">
                                <h3>${contact.name} <span class="badge">${categoryName}</span></h3>
                                <p class="phone">📞 ${formatPhone(contact.phone)}</p>
                                <p class="address">📍 ${contact.address}</p>
                            </div>
                            <div class="card-actions">
                                <button class="delete-contact-btn" onclick="deleteContact(${contact.id})">삭제</button>
                            </div>
                        </div>
                    `;
                }).join("");
            }
        } catch (error) {
            console.error("Load Contacts Error:", error);
        }
    }

    // ==========================================
    // 5. 회원정보 추가 및 맞춤형 알림 문구 출력 (POST /contacts)
    // ==========================================
    const addContactForm = document.getElementById("add-contact-form");
    if (addContactForm) {
        addContactForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const name = document.getElementById("contact-name").value.trim();
            const phone = document.getElementById("contact-phone").value.replace(/-/g, "").trim();
            const address = document.getElementById("contact-address").value.trim();
            const category_id = parseInt(categorySelect.value, 10);

            if (isNaN(category_id)) {
                alert("관계 항목을 선택해 주세요.");
                return;
            }

            // 선택된 관계의 텍스트 가져오기 (예: 가족, 친구 등)
            const selectedCategoryName = categorySelect.options[categorySelect.selectedIndex].text;

            try {
                const response = await fetch(`${BACKEND_URL}/contacts`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, phone, address, category_id }),
                    credentials: "include"
                });

                const data = await response.json();

                if (response.status === 201) {
                    // 요구사항 반영: "이름, 전화번호, 주소, 관계가 저장되었습니다" 얼럿 출력
                    alert(`이름: ${name}\n전화번호: ${formatPhone(phone)}\n주소: ${address}\n관계: ${selectedCategoryName}\n\n위 정보가 성공적으로 저장되었습니다.`);
                    addContactForm.reset();
                    await loadContacts(); // 회원목록 칸에 즉시 반영
                } else if (response.status === 422) {
                    alert(`무결성 검증 실패!\n- 이름: 한글 1~5자\n- 번호: 010 시작 11자리\n- 주소: '시'로 끝날 것`);
                } else {
                    alert(data.detail || "저장에 실패했습니다.");
                }
            } catch (error) {
                console.error("Add Contact Error:", error);
            }
        });
    }

    // ==========================================
    // 6. 회원 정보 삭제
    // ==========================================
    window.deleteContact = async (contactId) => {
        if (!confirm("정말 삭제하시겠습니까?")) return;
        try {
            const response = await fetch(`${BACKEND_URL}/contacts/${contactId}`, { method: "DELETE", credentials: "include" });
            if (response.status === 204) { alert("삭제되었습니다."); await loadContacts(); }
        } catch (error) { console.error(error); }
    };

    // ==========================================
    // 7. 검색창 입력 연동
    // ==========================================
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => { loadContacts(e.target.value.trim()); });
    }

    function formatPhone(phoneStr) {
        if (phoneStr.length === 11) return phoneStr.replace(/(\d{3})(\d{4})(\d{4})/, "$1-$2-$3");
        return phoneStr;
    }

    // ==========================================
    // 8. 로그아웃 (POST /auth/logout)
    // ==========================================
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            if (!confirm("로그아웃 하시겠습니까?")) return;
            try {
                const response = await fetch(`${BACKEND_URL}/auth/logout`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include" });
                if (response.ok) {
                    alert("로그아웃되었습니다.");
                    if (appContainer) appContainer.style.display = "none";
                    if (authContainer) authContainer.style.display = "block";
                    usernameInput.value = ""; passwordInput.value = ""; contactList.innerHTML = "";
                }
            } catch (error) { console.error(error); }
        });
    }
});