const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiService {
  constructor() {
    this.token = null;
  }

  setToken(token) {
    this.token = token;
  }

  async _request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const activeToken = this.token || (typeof localStorage !== 'undefined' ? localStorage.getItem('growwpulse_auth_token') : null);
    if (activeToken) {
      headers['Authorization'] = `Bearer ${activeToken}`;
    }

    const url = `${API_BASE_URL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errorMsg = `Server returned ${response.status}`;
        let errorCode = null;

        try {
          const errData = await response.json();
          if (errData) {
            if (errData.detail) {
              if (typeof errData.detail === 'object') {
                errorMsg = errData.detail.message || errData.detail.error || JSON.stringify(errData.detail);
                errorCode = errData.detail.error;
              } else if (typeof errData.detail === 'string') {
                errorMsg = errData.detail;
              }
            } else if (errData.message) {
              errorMsg = errData.message;
              errorCode = errData.error;
            }
          }
        } catch (_) {}

        if (response.status === 503) {
          if (!errorMsg || errorMsg.includes('Server returned 503')) {
            errorMsg = 'Database unavailable — your changes were not saved.';
          }
        } else if (response.status === 401) {
          if (!errorMsg || errorMsg.includes('Server returned 401')) {
            errorMsg = 'Session expired or unauthorized. Please sign in again.';
          }
        }

        const customError = new Error(errorMsg);
        customError.status = response.status;
        customError.code = errorCode;
        throw customError;
      }

      return await response.json();
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  async register(name, email, password) {
    return this._request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
  }

  async login(email, password) {
    return this._request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async getMe() {
    return this._request('/auth/me');
  }

  async getHealth() {
    return this._request('/health');
  }

  async getMarketStatus() {
    return this._request('/market-status');
  }

  async getWatchlist() {
    return this._request('/watchlist');
  }

  async addStock(symbol) {
    return this._request('/watchlist', {
      method: 'POST',
      body: JSON.stringify({ symbol }),
    });
  }

  async removeStock(symbol) {
    return this._request(`/watchlist/${encodeURIComponent(symbol)}`, {
      method: 'DELETE',
    });
  }

  async getWatchlistChanges() {
    return this._request('/watchlist/changes');
  }

  async markCurrentAsSeen() {
    return this._request('/watchlist/mark-seen', {
      method: 'POST',
    });
  }

  async getQuote(symbol) {
    return this._request(`/quote/${encodeURIComponent(symbol)}`);
  }

  async searchStocks(query = '') {
    const q = (query || '').trim();
    return this._request(q ? `/search?q=${encodeURIComponent(q)}` : '/search');
  }
}

export const api = new ApiService();
