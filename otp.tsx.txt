import { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TextInput, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '@/src/auth';
import { colors, spacing, radius, fontSize } from '@/src/theme';
import { Toast } from '@/src/Toast';

export default function OTP() {
  const router = useRouter();
  const { email } = useLocalSearchParams<{ email: string; flow: string }>();
  const { verifyOtp } = useAuth();
  const [digits, setDigits] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const refs = useRef<(TextInput | null)[]>([]);
  const [seconds, setSeconds] = useState(30);

  useEffect(() => {
    const t = setInterval(() => setSeconds((s) => (s > 0 ? s - 1 : 0)), 1000);
    return () => clearInterval(t);
  }, []);

  const setDigit = (i: number, v: string) => {
    const c = v.slice(-1);
    const next = [...digits];
    next[i] = c;
    setDigits(next);
    if (c && i < 5) refs.current[i + 1]?.focus();
  };

  const submit = async () => {
    setErr('');
    const code = digits.join('');
    if (code.length !== 6) { setErr('Enter 6-digit OTP'); return; }
    setLoading(true);
    try {
      const u = await verifyOtp(String(email), code);
      if (u.role === 'admin') router.replace('/admin');
      else router.replace('/(tabs)/home');
    } catch (e: any) {
      setErr(e.message || 'Invalid OTP');
    } finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1, padding: spacing.lg }}>
        <Pressable onPress={() => router.back()} testID="otp-back">
          <Ionicons name="chevron-back" size={28} color={colors.onSurface} />
        </Pressable>
        <Text style={styles.h1}>Verify OTP</Text>
        <Text style={styles.sub}>Enter the 6-digit code sent to {email}. {'\n'}Use <Text style={{ fontWeight: '700', color: colors.brand }}>123456</Text> for demo.</Text>

        {err ? <Toast message={err} type="error" /> : null}

        <View style={styles.otpRow}>
          {digits.map((d, i) => (
            <TextInput
              key={i}
              ref={(r) => { refs.current[i] = r; }}
              style={styles.cell}
              value={d}
              onChangeText={(v) => setDigit(i, v)}
              keyboardType="numeric"
              maxLength={1}
              testID={`otp-digit-${i}`}
              onKeyPress={({ nativeEvent }) => {
                if (nativeEvent.key === 'Backspace' && !digits[i] && i > 0) refs.current[i - 1]?.focus();
              }}
            />
          ))}
        </View>

        <Pressable style={[styles.cta, loading && { opacity: 0.6 }]} onPress={submit} disabled={loading} testID="otp-submit">
          <Text style={styles.ctaText}>{loading ? 'Verifying...' : 'Verify & Continue'}</Text>
        </Pressable>

        <Text style={styles.resend}>
          {seconds > 0 ? `Resend in ${seconds}s` : <Text onPress={() => setSeconds(30)} style={{ color: colors.brand, fontWeight: '700' }}>Resend OTP</Text>}
        </Text>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  h1: { fontSize: 28, fontWeight: '800', color: colors.onSurface, marginTop: spacing.lg },
  sub: { fontSize: fontSize.base, color: colors.muted, marginTop: 4, marginBottom: spacing.xl, lineHeight: 22 },
  otpRow: { flexDirection: 'row', gap: 10, marginBottom: spacing.xl, justifyContent: 'space-between' },
  cell: { flex: 1, height: 64, borderRadius: radius.md, borderWidth: 2, borderColor: colors.border, textAlign: 'center', fontSize: 24, fontWeight: '700', color: colors.onSurface, backgroundColor: colors.surfaceSecondary },
  cta: { backgroundColor: colors.brand, paddingVertical: 16, borderRadius: radius.md, alignItems: 'center' },
  ctaText: { color: '#fff', fontSize: fontSize.lg, fontWeight: '700' },
  resend: { textAlign: 'center', marginTop: spacing.lg, color: colors.muted },
});
