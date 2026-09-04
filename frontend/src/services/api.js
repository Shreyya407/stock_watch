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

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const url = `${API_BASE_URL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errorMsg = `Server returned ${response.status}`;
        try {
          const errData = await response.json();
          if (errData && errData.detail) {
            errorMsg = errData.detail;
          }
        } catch (_) {}
        throw new Error(errorMsg);
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
