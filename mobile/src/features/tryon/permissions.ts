import * as ImagePicker from "expo-image-picker";

export async function requestGalleryAccess() {
  const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();

  return {
    granted: permission.granted,
    canAskAgain: permission.canAskAgain,
  };
}
