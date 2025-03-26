// auth.js - Handles authentication and protected API calls

// Function to get cookies by name
function getCookie(name) {
  const cookies = document.cookie.split("; ");
  for (let cookie of cookies) {
    const [key, value] = cookie.split("=");
    if (key === name) return value;
  }
  return null;
}

// Function to get JWT token from sessionStorage
function getAccessToken() {
  return sessionStorage.getItem("access_token");
}

function storeAccessToken(accessToken) {
  sessionStorage.setItem("access_token", accessToken);
}

// // Get Refresh Token from sessionStorage
// function getRefreshToken() {
//   return sessionStorage.getItem("refresh_token");
// }

// // Save tokens securely
// function storeTokens(accessToken, refreshToken) {
//   sessionStorage.setItem("access_token", accessToken);
//   sessionStorage.setItem("refresh_token", refreshToken);
// }

// Clear stored tokens and log out user
function clearSessionAndLogout() {
  sessionStorage.removeItem("access_token");
  // sessionStorage.removeItem("refresh_token");
  window.location.href = "/auth/login/";
}

// Refresh access token using refresh token
async function refreshAccessToken() {
  const refreshToken = getCookie("refresh_token");

  if (!refreshToken) {
    clearSessionAndLogout();
    return null;
  }
  try {
    let response = await fetch("/token/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
      credentials: "include",
    });

    let data = await response.json();

    if (response.ok && data.access) {
      storeAccessToken(data.access);
      return data.access;
    } else {
      console.warn("Session expired. Logging out...");
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
async function fetchProtectedData(endpoint, method = "GET", body = null) {
  let accessToken = getAccessToken();

  if (!accessToken) {
    accessToken = await refreshAccessToken();
    if (!accessToken) return null; // Logout if refresh fails
  }

  try {
    let response = await fetch(endpoint, {
      method: method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: body ? JSON.stringify(body) : null,
    });

    if (response.status === 401) {
      console.warn("Access token expired. Attempting refresh...");
      accessToken = await refreshAccessToken();

      if (!accessToken) {
        window.location.href = "/auth/login/";
        return null; // Logout if refresh fails
      }

      // Retry request with new token
      response = await fetch(endpoint, {
        method: method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${accessToken}`,
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
  try {
    let response = await fetch("/auth/api/logout/", {
      method: "POST",
      credentials: "include",
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
