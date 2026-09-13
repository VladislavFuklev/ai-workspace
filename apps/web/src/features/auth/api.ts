import { api } from "@/lib/api";

import { registerResponseSchema, userProfileSchema, type UserProfile } from "./schemas";

/**
 * Every auth call in one place.
 *
 * Nothing here handles cookies: the API sets them and the browser sends them
 * back, which is what `credentials: "include"` in the client (task 1.7) is for.
 * A token this code could read would be a token an XSS bug could read.
 */
export async function signIn(email: string, password: string): Promise<UserProfile> {
  return api("/api/v1/auth/login", {
    method: "POST",
    body: { email, password },
    schema: userProfileSchema,
  });
}

export async function register(
  email: string,
  password: string,
  displayName: string,
): Promise<{ message: string }> {
  return api("/api/v1/auth/register", {
    method: "POST",
    body: { email, password, display_name: displayName },
    schema: registerResponseSchema,
  });
}

export async function signOut(): Promise<void> {
  await api("/api/v1/auth/logout", { method: "POST" });
}

export async function fetchCurrentUser(): Promise<UserProfile> {
  return api("/api/v1/auth/me", { schema: userProfileSchema });
}

export async function requestPasswordReset(email: string): Promise<void> {
  await api("/api/v1/auth/password-reset/request", {
    method: "POST",
    body: { email },
    schema: registerResponseSchema,
  });
}
