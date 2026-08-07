let currentUser = null;
let fetchCurrentUser = null;

export async function getCurrentUser() {
    if (currentUser) {
        return currentUser;
    }

    if (fetchCurrentUser) {
        return fetchCurrentUser;
    }

    const token = localStorage.getItem('token');
    if (!token) {
        return null;
    }

    fetchCurrentUser = (async () => {
        try {
            const response = await fetch("/api/users/me", {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });

            if (response.ok) {
                currentUser = await response.json();
                return currentUser;
            }
            
            localStorage.removeItem("token")
            return null;
        } catch (error) {
            return null;
        } finally {
            fetchCurrentUser = null
        }
    })();

    return fetchCurrentUser;
}

export function logout() {
    currentUser = null;
    fetchCurrentUser = null;
    localStorage.removeItem("token");
    window.location.href = "/";
}

export function getToken() {
    return localStorage.getItem("token");
}

export function setToken(token) {
    localStorage.setItem("token", token);
}

export function clearToken() {
    localStorage.removeItem("token");
    currentUser = null;
}