// auth.js - Complete authentication and token management

// Main Auth object with all authentication functionality
const Auth = {
  // Token management
  getAccessToken() {
    return sessionStorage.getItem("access_token");
  },

  getRefreshToken() {
    return getCookie("refresh_token");
  },

  storeAccessToken(accessToken) {
    sessionStorage.setItem("access_token", accessToken);
  },

  storeTokens(accessToken, refreshToken) {
    this.storeAccessToken(accessToken);
    // Store refresh token as HttpOnly cookie (handled by server)
    // We just track that we received it
    console.log("Tokens stored successfully");
  },

  clearTokens() {
    sessionStorage.removeItem("access_token");
    // Clear the refresh token cookie
    document.cookie =
      "refresh_token=; Path=/; Expires=Fri, 10 May 2025 00:00:00 GMT; Secure; SameSite=Strict";
  },

  isAuthenticated() {
    return !!this.getAccessToken();
  },

  // Authentication actions
  async login(username, password, rememberMe = false) {
    // const csrftoken = getCookie("csrftoken");
    try {
      const url = "/auth/api/login/";
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password, remember_me: rememberMe }),
        credentials: "include",
      });

      const data = await response.json();

      if (response.ok) {
        this.storeTokens(data.access_token, data.refresh_token);
        return {
          success: true,
          user: data.user || {},
        };
      } else {
        return {
          success: false,
          error: data.error || "Login failed",
        };
      }
    } catch (error) {
      console.error("Login error:", error);
      return {
        success: false,
        error: "An error occurred during login",
      };
    }
  },

  async register(userData) {
    console.error("Message from auth register function ");
    // const csrftoken = getCookie("csrftoken");
    try {
      const url = "/auth/api/signup/";
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
        credentials: "include",
      });

      console.log("Registration response status:", response.status);

      const data = await response.json();
      console.log("Registration response data:", data);

      if (response.ok) {
        this.storeTokens(data.access_token);
        return {
          success: true,
          user: data.user || {},
        };
      } else {
        return {
          success: false,
          error: data.error || data.message || "Registration failed",
        };
      }
    } catch (error) {
      console.error("Registration error:", error);
      return {
        success: false,
        error: "An error occurred during registration",
      };
    }
  },

  async refreshToken() {
    const refreshToken = this.getRefreshToken();

    if (!refreshToken) {
      return false;
    }

    try {
      const response = await fetch("/auth/api/token/refresh/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: refreshToken }),
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        this.storeAccessToken(data.access);
        return true;
      }

      return false;
    } catch (error) {
      console.error("Token refresh failed:", error);
      return false;
    }
  },

  async logout() {
    try {
      // Get current token for authorization header
      const token = this.getAccessToken();
      const refreshToken = this.getRefreshToken();

      // Try to call API to invalidate token on server
      if (token) {
        await fetch("/auth/api/logout/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: refreshToken
            ? JSON.stringify({ refresh_token: refreshToken })
            : null,
          credentials: "include",
        }).catch((err) => console.warn("Logout API error:", err));
      }
    } finally {
      // Always clean up local storage
      this.clearTokens();
      window.location.href = "/auth/login/";
    }
  },

  isTokenExpired() {
    const token = this.getAccessToken();
    if (!token) return true;

    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.exp < Date.now() / 1000;
    } catch (e) {
      return true;
    }
  },

  // API utilities
  async fetchWithAuth(url, options = {}) {
    if (this.isTokenExpired()) {
      const refreshed = await this.refreshToken();
      if (!refreshed) {
        this.redirectToLogin();
        throw new Error("Session expired");
      }
    }
    const token = this.getAccessToken();

    if (!token) {
      // Try to refresh the token
      const refreshed = await this.refreshToken();
      if (!refreshed) {
        this.redirectToLogin();
        throw new Error("Authentication required");
      }
    }

    // Add auth header with current token
    const authOptions = {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${this.getAccessToken()}`,
      },
    };

    // Handle JSON body
    if (
      options.body &&
      typeof options.body !== "string" &&
      !(options.body instanceof FormData)
    ) {
      authOptions.body = JSON.stringify(options.body);
      authOptions.headers = {
        ...authOptions.headers,
        "Content-Type": "application/json",
      };
    }

    try {
      let response = await fetch(url, authOptions);

      // If unauthorized, try token refresh once
      if (response.status === 401) {
        const refreshed = await this.refreshToken();

        if (refreshed) {
          // Retry with new token
          authOptions.headers[
            "Authorization"
          ] = `Bearer ${this.getAccessToken()}`;
          response = await fetch(url, authOptions);
        } else {
          // Redirect to login if refresh failed
          this.redirectToLogin();
          throw new Error("Authentication failed after token refresh");
        }
      }

      // Parse JSON if response is OK
      if (response.ok) {
        // Check if response is JSON
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          return response.json();
        }
        return response;
      }

      // Handle error responses
      const error = new Error(
        `API request failed with status ${response.status}`
      );
      error.status = response.status;

      try {
        error.data = await response.json();
      } catch (e) {
        error.data = null;
      }

      throw error;
    } catch (error) {
      console.error("API request failed:", error);
      throw error;
    }
  },

  redirectToLogin() {
    window.location.replace("/auth/login/");
  },

  redirectToDashboard() {
    window.location.replace("/user/dashboard/");
  },

  // UI related
  updateAuthUI() {
    // Update navigation based on auth state
    const isLoggedIn = this.isAuthenticated();
    const loginLinks = document.querySelectorAll('a[href="/auth/login/"]');
    const logoutLinks = document.querySelectorAll(".logout-link");
    const authOnlyElements = document.querySelectorAll(".auth-only");
    const guestOnlyElements = document.querySelectorAll(".guest-only");

    if (isLoggedIn) {
      // Show authenticated-only elements
      authOnlyElements.forEach((el) => el.classList.remove("d-none"));
      // Hide guest-only elements
      guestOnlyElements.forEach((el) => el.classList.add("d-none"));
      // Setup logout links
      logoutLinks.forEach((link) => {
        link.addEventListener("click", (e) => {
          e.preventDefault();
          this.logout();
        });
      });
    } else {
      // Hide authenticated-only elements
      authOnlyElements.forEach((el) => el.classList.add("d-none"));
      // Show guest-only elements
      guestOnlyElements.forEach((el) => el.classList.remove("d-none"));
    }
  },
};

// Helper function to get cookies
function getCookie(name) {
  const cookies = document.cookie.split("; ");
  for (let cookie of cookies) {
    const [key, value] = cookie.split("=");
    if (key === name) return value;
  }
  return null;
}

// Initialize authentication UI when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
  Auth.updateAuthUI();
});

// For backward compatibility with existing code
function getAccessToken() {
  return Auth.getAccessToken();
}
function storeAccessToken(token) {
  return Auth.storeAccessToken(token);
}
function clearSessionAndLogout() {
  return Auth.logout();
}
async function refreshAccessToken() {
  return Auth.refreshToken() ? Auth.getAccessToken() : null;
}
async function fetchProtectedData(url, method, body) {
  return Auth.fetchWithAuth(url, { method, body });
}
async function logout() {
  return Auth.logout();
}
