import { Alert, Platform } from "react-native";

export function showAlert(title: string, message: string): void {
  if (Platform.OS === "web") window.alert(`${title}\n\n${message}`);
  else Alert.alert(title, message);
}

export function confirmAction(title: string, message: string, confirmLabel: string): Promise<boolean> {
  if (Platform.OS === "web") return Promise.resolve(window.confirm(`${title}\n\n${message}`));
  return new Promise((resolve) => Alert.alert(title, message, [
    { text: "Mégse", style: "cancel", onPress: () => resolve(false) },
    { text: confirmLabel, style: "destructive", onPress: () => resolve(true) },
  ], { cancelable: true, onDismiss: () => resolve(false) }));
}
