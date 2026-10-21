import React, { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useAuth } from "@/src/auth/AuthContext";
import { shadow, theme } from "@/src/theme";
import { T } from "@/src/components/Typography";
import ContentBackground from "@/src/components/ContentBackground";

/**
 * Regisztráció utáni e-mail megerősítés.
 *
 * Külön útvonal, hogy az állapot ne vesszen el: a regisztrációs oldal ide irányít,
 * a challenge és az email a query paraméterben jön. Újratöltésnél is működik, és
 * a kód a meglévő MFA-végpontra megy (/api/auth/mfa/verify).
 */
export default function VerifyEmailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ challenge?: string; email?: string }>();
  const { verifyMfa, resendVerification } = useAuth();

  const challengeId = String(params.challenge || "");
  const email = String(params.email || "");

  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [currentChallenge, setCurrentChallenge] = useState(challengeId);

  const submit = async () => {
    setError(null);
    const digits = code.replace(/[^0-9]/g, "");
    if (digits.length !== 6) {
      setError("Írd be a 6 jegyű kódot.");
      return;
    }
    if (!currentChallenge) {
      setError("Lejárt a megerősítés. Kérj új kódot.");
      return;
    }
    setBusy(true);
    try {
      const r = await verifyMfa(currentChallenge, digits, false);
      if (r.ok) router.replace("/");
      else setError(r.error || "Nem sikerült ellenőrizni a kódot.");
    } catch (e: any) {
      setError(e?.message || "Nem sikerült ellenőrizni a kódot.");
    } finally {
      setBusy(false);
    }
  };

  const resend = async () => {
    setError(null);
    setInfo(null);
    if (!email) {
      setError("Hiányzik az e-mail cím. Menj vissza a regisztrációhoz.");
      return;
    }
    setBusy(true);
    try {
      const r = await resendVerification(email);
      if (!r.ok) {
        setError(r.error || "Nem sikerült új kódot kérni.");
        return;
      }
      setInfo("Ha a cím létezik, új kódot küldtünk.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} testID="verify-email-screen">
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ContentBackground>
          <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
            <View style={styles.hero}>
              <T variant="caption" color={theme.accentSoft} style={styles.heroCaption}>ESV-MODELL</T>
              <T variant="display" color={theme.textOnDark} style={styles.heroTitle}>E-mail megerősítése</T>
              <T variant="body" color="rgba(245,249,255,0.72)" align="center" style={styles.heroSubtitle}>
                {email ? `Elküldtük a 6 jegyű kódot ide: ${email}` : "Írd be a 6 jegyű kódot, amit e-mailben kaptál."}
              </T>
            </View>

            <View style={styles.sheet}>
              <View style={[styles.card, shadow.card]}>
                <T variant="caption" color={theme.accentSoft} style={styles.lbl}>BIZTONSÁGI KÓD</T>
                <TextInput
                  style={styles.input}
                  value={code}
                  onChangeText={(v) => setCode(v.replace(/[^0-9]/g, "").slice(0, 6))}
                  placeholder="000000"
                  placeholderTextColor="rgba(247,251,255,0.48)"
                  keyboardType="number-pad"
                  maxLength={6}
                  autoFocus
                  testID="verify-code"
                />

                {error ? <T variant="small" color={theme.danger} style={styles.msg} testID="verify-error">{error}</T> : null}
                {info ? <T variant="small" color={theme.accentSoft} style={styles.msg}>{info}</T> : null}

                <TouchableOpacity style={styles.primaryBtn} onPress={submit} disabled={busy} testID="verify-submit" activeOpacity={0.88}>
                  <LinearGradient colors={[theme.accentDeep, theme.primarySoft]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.primaryGradient}>
                    {busy ? <ActivityIndicator color={theme.white} /> : <T variant="title" color={theme.white}>Megerősítés</T>}
                  </LinearGradient>
                </TouchableOpacity>

                <TouchableOpacity onPress={resend} disabled={busy} style={styles.resend} testID="verify-resend">
                  <T variant="small" color={theme.accentDeep}>Nem jött meg? Új kód kérése</T>
                </TouchableOpacity>

                <View style={styles.foot}>
                  <Pressable testID="verify-back" onPress={() => router.replace("/register")}>
                    <T variant="small" color="rgba(247,251,255,0.70)">Vissza a regisztrációhoz</T>
                  </Pressable>
                </View>
              </View>
            </View>
          </ScrollView>
        </ContentBackground>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.primaryDark },
  scroll: { flexGrow: 1 },
  hero: { alignItems: "center", paddingTop: 60, paddingBottom: 28, paddingHorizontal: 28 },
  heroCaption: { fontSize: 10, letterSpacing: 1.4 },
  heroTitle: { fontSize: 32, lineHeight: 38, textAlign: "center", marginTop: 14 },
  heroSubtitle: { maxWidth: 320, marginTop: 10 },
  sheet: { flex: 1, paddingHorizontal: 18, paddingBottom: 28 },
  card: {
    backgroundColor: "rgba(7,27,48,0.48)",
    borderRadius: 22,
    padding: 20,
    borderWidth: 1,
    borderColor: "rgba(79,209,197,0.22)",
    backdropFilter: "blur(20px)",
  } as any,
  lbl: { fontSize: 10, letterSpacing: 1.2, marginBottom: 8, marginTop: 6 },
  input: {
    backgroundColor: "rgba(255,255,255,0.06)",
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderWidth: 1,
    borderColor: "rgba(79,209,197,0.18)",
    fontSize: 24,
    textAlign: "center",
    letterSpacing: 10,
    color: theme.textOnDark,
  },
  msg: { marginTop: 12, textAlign: "center" },
  primaryBtn: { marginTop: 20, borderRadius: 14, overflow: "hidden" },
  primaryGradient: { paddingVertical: 15, alignItems: "center", justifyContent: "center" },
  resend: { marginTop: 16, alignItems: "center" },
  foot: { flexDirection: "row", justifyContent: "center", marginTop: 20, alignItems: "center" },
} as any);
