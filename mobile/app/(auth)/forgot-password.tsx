import React from "react";
import { useRouter } from "expo-router";
import { RecoveryScreen } from "../../src/features/auth/RecoveryScreen";

export default function ForgotPasswordRoute() {
  const router = useRouter();

  return (
    <RecoveryScreen
      onRecoveryComplete={() => {
        router.replace("/(auth)/sign-in");
      }}
      onBackToLogin={() => {
        router.replace("/(auth)/sign-in");
      }}
    />
  );
}
