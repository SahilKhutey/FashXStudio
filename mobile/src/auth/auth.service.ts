import { toAuthUserMessage } from "./auth.errors";
import type { AuthProvider } from "./auth.provider";
import type {
  LoginInput,
  RecoveryCompleteInput,
  RecoveryStartInput,
  RegisterInput,
  VerifyAccountInput,
} from "./auth.types";

export class ProviderAuthService {
  constructor(private readonly provider: AuthProvider) {}

  register(input: RegisterInput) {
    return this.provider.register(input);
  }

  login(input: LoginInput) {
    return this.provider.login(input);
  }

  confirmRegistration(input: VerifyAccountInput) {
    return this.provider.confirmRegistration(input);
  }

  resendVerificationCode(email: string) {
    return this.provider.resendVerificationCode(email);
  }

  startRecovery(input: RecoveryStartInput) {
    return this.provider.startRecovery(input);
  }

  completeRecovery(input: RecoveryCompleteInput) {
    return this.provider.completeRecovery(input);
  }

  getCurrentSession() {
    return this.provider.getCurrentSession();
  }

  getAccessToken() {
    return this.provider.getAccessToken();
  }

  refreshSession() {
    return this.provider.refreshSession();
  }

  logout() {
    return this.provider.logout();
  }

  getUserMessage(error: unknown): string {
    return toAuthUserMessage(error);
  }
}
