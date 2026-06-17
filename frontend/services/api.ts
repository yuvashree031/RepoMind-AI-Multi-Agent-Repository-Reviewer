const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Repository {
  id: string;
  url: string;
  owner: string;
  name: string;
  default_branch: string;
  description?: string;
  created_at: string;
}

export interface Finding {
  file_path: string;
  line_number: number;
  type?: string;
  vulnerability_type?: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  description: string;
  suggestion?: string;
  recommendation?: string;
  code_snippet?: string;
}

export interface Review {
  id: string;
  repository_id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  overall_score: number | null;
  security_score: number | null;
  code_quality_score: number | null;
  architecture_score: number | null;
  devops_score: number | null;
  findings: {
    code_quality?: Finding[];
    security?: Finding[];
    architecture?: {
      controllers?: string[];
      models?: string[];
      routes?: string[];
      services?: string[];
      databases?: string[];
    };
    devops?: Finding[];
    logs?: string[];
    languages?: Record<string, { size_bytes: number; percentage: number; file_count: number }>;
    frameworks?: string[];
    summary?: string;
  } | null;
  mermaid_diagram: string | null;
  created_at: string;
  repository: Repository;
  report?: {
    id: string;
    review_id: string;
    content_md: string;
    created_at: string;
  } | null;
}

export interface ReviewSummary {
  id: string;
  repository_id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  overall_score: number | null;
  created_at: string;
  repository: {
    id: string;
    url: string;
    owner: string;
    name: string;
  };
}

export interface StatusResponse {
  id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  overall_score: number | null;
  logs: string[];
  error?: string | null;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Helper to inject bearer authorization token if logged in
function getHeaders(authRequired: boolean = true): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (authRequired && typeof window !== 'undefined') {
    const token = localStorage.getItem('repomind_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
}

export const apiService = {
  /**
   * Register a new user account
   */
  async signup(email: string, password: string, fullName?: string): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: getHeaders(false),
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Registration failed');
    }
    
    const data: AuthResponse = await response.json();
    if (typeof window !== 'undefined') {
      localStorage.setItem('repomind_token', data.access_token);
      localStorage.setItem('repomind_user', JSON.stringify(data.user));
    }
    return data;
  },

  /**
   * Authenticate a user
   */
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: getHeaders(false),
      body: JSON.stringify({ email, password }),
    });
    
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Invalid email or password');
    }
    
    const data: AuthResponse = await response.json();
    if (typeof window !== 'undefined') {
      localStorage.setItem('repomind_token', data.access_token);
      localStorage.setItem('repomind_user', JSON.stringify(data.user));
    }
    return data;
  },

  /**
   * Log out the current user by removing token
   */
  logout() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('repomind_token');
      localStorage.removeItem('repomind_user');
    }
  },

  /**
   * Fetch details of currently logged in user
   */
  async getMe(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      method: 'GET',
      headers: getHeaders(true)
    });
    
    if (!response.ok) {
      this.logout();
      throw new Error('Failed to retrieve user profile');
    }
    return response.json();
  },

  /**
   * Check if user session exists in local storage
   */
  isAuthenticated(): boolean {
    if (typeof window !== 'undefined') {
      return !!localStorage.getItem('repomind_token');
    }
    return false;
  },

  /**
   * Retrieve current user info from cache
   */
  getCurrentUser(): User | null {
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem('repomind_user');
      if (userStr) {
        try {
          return JSON.parse(userStr);
        } catch {
          return null;
        }
      }
    }
    return null;
  },

  /**
   * Queue a new repository analysis
   */
  async analyzeRepository(url: string, token?: string): Promise<{ review_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: getHeaders(true),
      body: JSON.stringify({ url, token }),
    });
    
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to submit repository for analysis');
    }
    
    return response.json();
  },

  /**
   * Get all review summaries (for history list)
   */
  async getReviews(): Promise<ReviewSummary[]> {
    const response = await fetch(`${API_BASE_URL}/api/reviews`, {
      headers: getHeaders(true)
    });
    if (!response.ok) {
      throw new Error('Failed to fetch review history');
    }
    return response.json();
  },

  /**
   * Get full details of a specific review
   */
  async getReviewDetail(reviewId: string): Promise<Review> {
    const response = await fetch(`${API_BASE_URL}/api/reviews/${reviewId}`, {
      headers: getHeaders(true)
    });
    if (!response.ok) {
      throw new Error('Failed to fetch review details');
    }
    return response.json();
  },

  /**
   * Poll active review status and logs
   */
  async getReviewStatus(reviewId: string): Promise<StatusResponse> {
    const response = await fetch(`${API_BASE_URL}/api/reviews/${reviewId}/status`, {
      headers: getHeaders(true)
    });
    if (!response.ok) {
      throw new Error('Failed to fetch review status');
    }
    return response.json();
  },

  /**
   * Returns download URL link for the report (authorizes via query parameter token)
   */
  getReportDownloadUrl(reviewId: string): string {
    const token = typeof window !== 'undefined' ? localStorage.getItem('repomind_token') : null;
    return `${API_BASE_URL}/api/reviews/${reviewId}/download${token ? `?token=${token}` : ''}`;
  }
};
