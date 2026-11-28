import React from "react";
import { useRouter } from "expo-router";
import { RegisterScreen } from "../../src/features/auth/RegisterScreen";

export default function RegisterRoute() {
  const router = useRouter();

  return (
    <RegisterScreen
      onVerificationRequired={(email) => {
        router.push({
          pathname: "/(auth)/verify",
          params: { email },
        });
      }}
      onAuthenticated={() => {
        router.replace("/(tabs)/feed");
      }}
      onLoginPress={() => {
        router.replace("/(auth)/sign-in");
      }}
    />
  );
}
