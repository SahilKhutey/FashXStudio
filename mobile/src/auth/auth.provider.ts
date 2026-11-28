import type {
  AuthOperationResult,
  AuthSession,
  LoginInput,
  RecoveryCompleteInput,
  RecoveryStartInput,
  RegisterInput,
  VerifyAccountInput,
} from "./auth.types";

export interface AuthProvider {
  register(input: RegisterInput): Promise<AuthOperationResult>;
  login(input: LoginInput): Promise<AuthOperationResult>;
  confirmRegistration(input: VerifyAccountInput): Promise<void>;
  resendVerificationCode(email: string): Promise<void>;
  startRecovery(input: RecoveryStartInput): Promise<void>;
  completeRecovery(input: RecoveryCompleteInput): Promise<void>;
  getCurrentSession(): Promise<AuthSession | null>;
  getAccessToken(): Promise<string | null>;
  refreshSession(): Promise<AuthSession>;
  logout(): Promise<void>;
}
