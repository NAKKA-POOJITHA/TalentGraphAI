const API_BASE = "http://127.0.0.1:8000/api";

class ApiService {
  static getHeaders() {
    const token = localStorage.getItem("tg_token");
    const headers = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  static async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultHeaders = this.getHeaders();
    
    // Merge headers
    const headers = {
      ...defaultHeaders,
      ...options.headers,
    };

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401) {
        // Auto logout on unauthorized token
        localStorage.removeItem("tg_token");
        if (!window.location.pathname.includes("/login") && window.location.pathname !== "/") {
          window.location.href = "/";
        }
      }
      
      const text = await response.text();
      let data = {};
      if (text) {
        try {
          data = jsonParseSafe(text);
        } catch (e) {
          data = { message: text };
        }
      }
      
      if (!response.ok) {
        throw new Error(data.detail || data.message || `Request failed with status ${response.status}`);
      }
      
      return data;
    } catch (error) {
      console.error(`API Error on ${endpoint}:`, error);
      throw error;
    }
  }

  // --- Auth Endpoints ---
  static async login(email, password) {
    const response = await this.request("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (response.access_token) {
      localStorage.setItem("tg_token", response.access_token);
    }
    return response;
  }

  static async register(email, password, fullName) {
    return this.request("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  static async getMe() {
    return this.request("/auth/me");
  }

  static logout() {
    localStorage.removeItem("tg_token");
  }

  // --- Jobs Endpoints ---
  static async getJobs() {
    return this.request("/jobs");
  }

  static async getJob(jobId) {
    return this.request(`/jobs/${jobId}`);
  }

  static async createJob(title, description) {
    return this.request("/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description }),
    });
  }

  static async deleteJob(jobId) {
    return this.request(`/jobs/${jobId}`, {
      method: "DELETE",
    });
  }

  // --- Candidates Endpoints ---
  static async getCandidates() {
    return this.request("/candidates");
  }

  static async getCandidate(candidateId) {
    return this.request(`/candidates/${candidateId}`);
  }

  static async deleteCandidate(candidateId) {
    return this.request(`/candidates/${candidateId}`, {
      method: "DELETE",
    });
  }

  static async uploadResumes(files) {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    
    // We do NOT set Content-Type header manually for FormData,
    // browser will set it with boundary string.
    return this.request("/candidates/upload", {
      method: "POST",
      body: formData,
    });
  }

  // --- Ranking Endpoints ---
  static async discoverCandidates(jobId, limit = 50) {
    return this.request(`/ranking/discover/${jobId}?limit=${limit}`, {
      method: "POST",
    });
  }

  static async getRankingHistory(jobId) {
    return this.request(`/ranking/history/${jobId}`);
  }
}

function jsonParseSafe(text) {
  try {
    return JSON.parse(text);
  } catch (e) {
    return text;
  }
}

export default ApiService;
