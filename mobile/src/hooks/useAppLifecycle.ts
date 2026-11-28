import { useEffect, useRef } from "react";
import { AppState, type AppStateStatus } from "react-native";

type Callbacks = {
  onForeground?: () => void;
  onBackground?: () => void;
  onInactive?: () => void;
};

export function useAppLifecycle(callbacks: Callbacks) {
  const previousState = useRef<AppStateStatus>(AppState.currentState);
  const callbacksRef = useRef(callbacks);

  useEffect(() => {
    callbacksRef.current = callbacks;
  }, [callbacks]);

  useEffect(() => {
    const subscription = AppState.addEventListener("change", (nextState) => {
      const previous = previousState.current;

      if (nextState === "active" && previous !== "active") {
        callbacksRef.current.onForeground?.();
      } else if (nextState === "background") {
        callbacksRef.current.onBackground?.();
      } else if (nextState === "inactive") {
        callbacksRef.current.onInactive?.();
      }

      previousState.current = nextState;
    });

    return () => subscription.remove();
  }, []);
}
