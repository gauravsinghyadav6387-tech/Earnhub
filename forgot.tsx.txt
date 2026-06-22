import { useState } from 'react';
import { View, Text, StyleSheet, TextInput, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '@/src/api';
import { colors, spacing, radius, fontSize } from '@/src/theme';
import { Toast } from '@/src/Toast';

export default function Forgot() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPass, setNewPass] = useState('');
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  const sendOtp = async () => {
    setErr(''); setMsg(''); setLoading(true);
    try {
      const r = await api.post('/auth/forgot-password', { email });
      setMsg(r.message);
      setStep(2);
    } catch (e: any) { setErr(e.message); } finally { setLoading(false); }
  };

  const reset = async () => {
    setErr(''); setLoading(true);
    try {
      await api.post('/auth/reset-password', { email, otp, new_password: newPass });
      setMsg('Password reset. Please login.');
      setTimeout(() => router.replace('/login'), 1200);
    } catch (e: any) { setErr(e.message); } finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1, padding: spacing.lg }}>
        <Pressable onPress={() => router.back()} testID="forgot-back">
          <Ionicons name="chevron-back" size={28} color={colors.onSurface} />
        </Pressable>
        <Text style={styles.h1}>Reset Password</Text>
        <Text style={styles.sub}>{step === 1 ? 'Enter your email to receive OTP' : 'Enter OTP (123456) and new password'}</Text>
        {err ? <Toast message={err} type="error" /> : null}
        {msg ? <Toast message={msg} type="success" /> : null}

        <View style={styles.inputBox}>
          <Ionicons name="mail" size={20} color={colors.muted} />
          <TextInput style={styles.input} placeholder="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" testID="forgot-email" />
        </View>

        {step === 2 && (
          <>
            <View style={styles.inputBox}>
              <Ionicons name="keypad" size={20} color={colors.muted} />
              <TextInput style={styles.input} placeholder="OTP (123456)" value={otp} onChangeText={setOtp} keyboardType="numeric" testID="forgot-otp" />
            </View>
            <View style={styles.inputBox}>
              <Ionicons name="lock-closed" size={20} color={colors.muted} />
              <TextInput style={styles.input} placeholder="New Password" value={newPass} onChangeText={setNewPass} secureTextEntry testID="forgot-newpw" />
            </View>
          </>
        )}

        <Pressable style={styles.cta} onPress={step === 1 ? sendOtp : reset} disabled={loading} testID="forgot-submit">
          <Text style={styles.ctaText}>{loading ? '...' : step === 1 ? 'Send OTP' : 'Reset Password'}</Text>
        </Pressable>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  h1: { fontSize: 28, fontWeight: '800', color: colors.onSurface, marginTop: spacing.lg },
  sub: { fontSize: fontSize.base, color: colors.muted, marginTop: 4, marginBottom: spacing.xl },
  inputBox: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, paddingHorizontal: spacing.md, marginBottom: spacing.md, borderWidth: 1, borderColor: colors.border, height: 52 },
  input: { flex: 1, color: colors.onSurface, fontSize: fontSize.base },
  cta: { backgroundColor: colors.brand, paddingVertical: 16, borderRadius: radius.md, alignItems: 'center', marginTop: spacing.sm },
  ctaText: { color: '#fff', fontSize: fontSize.lg, fontWeight: '700' },
});
