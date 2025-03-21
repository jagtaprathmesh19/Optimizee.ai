// auth.js - Handles authentication and protected API calls

// Function to get JWT token from sessionStorage
function getAccessToken() {
  return sessionStorage.getItem("access_token");
}

// Get Refresh Token from sessionStorage
function getRefreshToken() {
  return sessionStorage.getItem("refresh_token");
}

// Save tokens securely
function storeTokens(accessToken, refreshToken) {
  sessionStorage.setItem("access_token", accessToken);
  sessionStorage.setItem("refresh_token", refreshToken);
}

// Clear stored tokens and log out user
function clearSessionAndLogout() {
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
  window.location.href = "/auth/login/";
}

// Refresh access token using refresh token
async function refreshAccessToken() {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    clearSessionAndLogout();
    return null;
  }

  try {
    let response = await fetch("/token/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    let data = await response.json();

    if (response.ok && data.access) {
      storeTokens(data.access, refreshToken);
      return data.access;
    } else {
      console.warn("Refresh token invalid. Logging out...");
      clearSessionAndLogout();
      return null;
    }
  } catch (error) {
    console.error("Token refresh failed:", error);
    clearSessionAndLogout();
    return null;
  }
}

// Function to make authenticated API calls
async function fetchProtectedData(
  endpoint,
  accessToken,
  method = "GET",
  body = null
) {
  // let accessToken = getAccessToken();

  if (!accessToken) {
    accessToken = await refreshAccessToken();
    if (!accessToken) return null; // Logout if refresh fails
  }

  try {
    let response = await fetch(endpoint, {
      method: method,
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : null,
    });

    if (response.status === 401) {
      console.warn("Access token expired. Attempting refresh...");
      accessToken = await refreshAccessToken();

      if (!accessToken) return null; // Logout if refresh fails

      // Retry request with new token
      response = await fetch(endpoint, {
        method: method,
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : null,
      });
    }

    return response.ok ? response.json() : Promise.reject(response);
  } catch (error) {
    console.error("API request failed:", error);
    return null;
  }
}

// Logout function - Calls API & clears session
async function logout() {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    clearSessionAndLogout();
    return;
  }

  try {
    let response = await fetch("/auth/api/logout/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (response.ok) {
      clearSessionAndLogout();
    } else {
      console.warn("Logout API failed. Clearing session...");
      clearSessionAndLogout();
    }
  } catch (error) {
    console.error("Logout error:", error);
    clearSessionAndLogout();
  }
}
