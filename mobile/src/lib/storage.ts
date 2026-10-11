import * as SecureStore from "expo-secure-store";
import AsyncStorage from "@react-native-async-storage/async-storage";

const ENCRYPTION_KEY_ALIAS = "fashx_auth_encryption_key";

/**
 * Retrieves or generates an encryption key stored securely in Expo SecureStore.
 */
async function getOrCreateKey(): Promise<string> {
  let key = await SecureStore.getItemAsync(ENCRYPTION_KEY_ALIAS);
  if (!key) {
    // Generate a secure random hex key (256-bit)
    const array = new Uint8Array(32);
    if (typeof crypto !== "undefined" && crypto.getRandomValues) {
      crypto.getRandomValues(array);
    } else {
      for (let i = 0; i < 32; i++) {
        array[i] = Math.floor(Math.random() * 256);
      }
    }
    key = Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join("");
    await SecureStore.setItemAsync(ENCRYPTION_KEY_ALIAS, key);
  }
  return key;
}

/**
 * Symmetric stream encryption/decryption using the SecureStore-held key.
 * Ensures session tokens never reside in plaintext inside AsyncStorage.
 */
function xorCipher(text: string, keyHex: string): string {
  const keyBytes: number[] = [];
  for (let i = 0; i < keyHex.length; i += 2) {
    keyBytes.push(parseInt(keyHex.substring(i, i + 2), 16) || 0);
  }
  const encoder = new TextEncoder();
  const textBytes = encoder.encode(text);
  const encryptedBytes = new Uint8Array(textBytes.length);

  for (let i = 0; i < textBytes.length; i++) {
    const tb = textBytes[i] ?? 0;
    const kb = keyBytes[i % keyBytes.length] ?? 0;
    encryptedBytes[i] = tb ^ kb;
  }

  let binary = "";
  for (let i = 0; i < encryptedBytes.byteLength; i++) {
    binary += String.fromCharCode(encryptedBytes[i] ?? 0);
  }
  return btoa(binary);
}

function xorDecipher(base64Text: string, keyHex: string): string {
  const binary = atob(base64Text);
  const encryptedBytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    encryptedBytes[i] = binary.charCodeAt(i);
  }

  const keyBytes: number[] = [];
  for (let i = 0; i < keyHex.length; i += 2) {
    keyBytes.push(parseInt(keyHex.substring(i, i + 2), 16) || 0);
  }

  const decryptedBytes = new Uint8Array(encryptedBytes.length);
  for (let i = 0; i < encryptedBytes.length; i++) {
    const eb = encryptedBytes[i] ?? 0;
    const kb = keyBytes[i % keyBytes.length] ?? 0;
    decryptedBytes[i] = eb ^ kb;
  }

  const decoder = new TextDecoder();
  return decoder.decode(decryptedBytes);
}

/**
 * Large Secure Store Adapter for Supabase:
 * Encryption key resides in SecureStore; encrypted payload resides in AsyncStorage.
 */
export const LargeSecureStore = {
  async getItem(key: string): Promise<string | null> {
    try {
      const encryptedValue = await AsyncStorage.getItem(key);
      if (!encryptedValue) return null;
      const encryptionKey = await getOrCreateKey();
      return xorDecipher(encryptedValue, encryptionKey);
    } catch {
      return null;
    }
  },

  async setItem(key: string, value: string): Promise<void> {
    try {
      const encryptionKey = await getOrCreateKey();
      const encryptedValue = xorCipher(value, encryptionKey);
      await AsyncStorage.setItem(key, encryptedValue);
    } catch (e) {
      console.warn("LargeSecureStore failed to set item:", e);
    }
  },

  async removeItem(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
    } catch (e) {
      console.warn("LargeSecureStore failed to remove item:", e);
    }
  },
};
