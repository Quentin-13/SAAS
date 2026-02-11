import api, { setTokens, clearTokens, getAccessToken } from "./api";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  phone: string | null;
  is_active: boolean;
  organization_id: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export async function getUser(): Promise<User> {
  const response = await api.get("/auth/me");
  return response.data;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const response = await api.post("/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  const tokens: TokenResponse = response.data;
  setTokens(tokens.access_token, tokens.refresh_token);
  return tokens;
}

export async function register(data: {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
}): Promise<TokenResponse> {
  const response = await api.post("/auth/register", data);
  const tokens: TokenResponse = response.data;
  setTokens(tokens.access_token, tokens.refresh_token);
  return tokens;
}

export function logout() {
  clearTokens();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}
