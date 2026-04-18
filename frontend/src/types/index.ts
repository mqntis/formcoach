export interface User {
  id: number;
  email: string;
}

export interface Session {
  id: number;
  title: string;
  notes?: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  user: User;
}
