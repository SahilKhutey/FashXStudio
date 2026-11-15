/**
 * FashXStudio Shopper Account Lifecycle API Client.
 * Connects Expo mobile client to backend /api/v1/account endpoints.
 */

import { authenticatedFetch } from "./authenticatedFetch";

export type AccountStatus =
  | "PENDING_VERIFICATION"
  | "PROVISIONING"
  | "ACTIVE"
  | "DISABLED"
  | "DELETION_PENDING"
  | "DELETION_IN_PROGRESS"
  | "DELETED";

export interface AccountMeResponse {
  user_id: string;
  email_normalized: string | null;
  email_verified: boolean;
  status: AccountStatus;
  roles: string[];
  created_at: string;
}

export interface AccountProvisionResponse {
  user_id: string;
  status: AccountStatus;
  email_normalized: string | null;
  email_verified: boolean;
  is_new: bool;
}

export interface AccountDeletionResponse {
  job_id: string;
  user_id: string;
  status: AccountStatus;
  message: string;
}

export interface AccountDeletionStatusResponse {
  job_id: string;
  user_id: string;
  status: string;
  requested_at: string;
  started_at: string | null;
  completed_at: string | null;
  attempts: number;
}

export class AccountApiClient {
  constructor(private baseUrl: string = "/api/v1/account") {}

  async provision(email?: string, emailVerified: boolean = false): Promise<AccountProvisionResponse> {
    const res = await authenticatedFetch(`${this.baseUrl}/provision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, email_verified: emailVerified }),
    });
    if (!res.ok) {
      throw new Error(`Failed to provision account: HTTP ${res.status}`);
    }
    return res.json();
  }

  async getMe(): Promise<AccountMeResponse> {
    const res = await authenticatedFetch(`${this.baseUrl}/me`, {
      method: "GET",
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch account: HTTP ${res.status}`);
    }
    return res.json();
  }

  async requestEmailChange(newEmail: string): Promise<{ message: string; status: string }> {
    const res = await authenticatedFetch(`${this.baseUrl}/email-change`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_email: newEmail }),
    });
    if (!res.ok) {
      throw new Error(`Failed to request email change: HTTP ${res.status}`);
    }
    return res.json();
  }

  async confirmEmailChange(newEmail: string, code: string): Promise<{ user_id: string; email_normalized: string; status: string }> {
    const res = await authenticatedFetch(`${this.baseUrl}/email-change/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_email: newEmail, confirmation_code: code }),
    });
    if (!res.ok) {
      throw new Error(`Failed to confirm email change: HTTP ${res.status}`);
    }
    return res.json();
  }

  async disableAccount(reason?: string): Promise<{ user_id: string; status: AccountStatus; disabled_at: string }> {
    const res = await authenticatedFetch(`${this.baseUrl}/disable`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) {
      throw new Error(`Failed to disable account: HTTP ${res.status}`);
    }
    return res.json();
  }

  async requestDeletion(reason?: string): Promise<AccountDeletionResponse> {
    const res = await authenticatedFetch(`${this.baseUrl}/deletion-request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) {
      throw new Error(`Failed to request account deletion: HTTP ${res.status}`);
    }
    return res.json();
  }

  async getDeletionStatus(): Promise<AccountDeletionStatusResponse> {
    const res = await authenticatedFetch(`${this.baseUrl}/deletion-status`, {
      method: "GET",
    });
    if (!res.ok) {
      throw new Error(`Failed to get deletion status: HTTP ${res.status}`);
    }
    return res.json();
  }

  async revokeAllSessions(): Promise<{ user_id: string; revoked_sessions_count: number; message: string }> {
    const res = await authenticatedFetch(`${this.baseUrl}/sessions/revoke-all`, {
      method: "POST",
    });
    if (!res.ok) {
      throw new Error(`Failed to revoke sessions: HTTP ${res.status}`);
    }
    return res.json();
  }
}

export const accountApiClient = new AccountApiClient();
