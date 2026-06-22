import { useState } from 'react';
import { View, Text, StyleSheet, TextInput, Pressable, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '@/src/auth';
import { colors, spacing, radius, fontSize } from '@/src/theme';
import { Toast } from '@/src/Toast';

export default function Login() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  const submit = async () => {
    setErr('');
    if (!email || !password) { setErr('Please fill all fields'); return; }
    setLoading(true);
    try {
      await login(email.trim(), password);
      router.push({ pathname: '/otp', params: { email: email.trim(), flow: 'login' } });
    } catch (e: any) {
      setErr(e.message || 'Login failed');
    } finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 60 }} keyboardShouldPersistTaps="handled">
          <View style={styles.logo}>
            <Ionicons name="rocket" size={32} color={colors.brand} />
            <Text style={styles.brand}>EarnHub</Text>
          </View>
          <Text style={styles.h1}>Welcome back</Text>
          <Text style={styles.sub}>Login to continue earning</Text>

          {err ? <Toast message={err} type="error" /> : null}

          <View style={styles.inputBox}>
            <Ionicons name="mail" size={20} color={colors.muted} />
            <TextInput style={styles.input} placeholder="Email" placeholderTextColor={colors.muted} value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" testID="login-email" />
          </View>
          <View style={styles.inputBox}>
            <Ionicons name="lock-closed" size={20} color={colors.muted} />
            <TextInput style={styles.input} placeholder="Password" placeholderTextColor={colors.muted} value={password} onChangeText={setPassword} secureTextEntry={!show} testID="login-password" />
            <Pressable onPress={() => setShow(!show)}>
              <Ionicons name={show ? 'eye-off' : 'eye'} size={20} color={colors.muted} />
            </Pressable>
          </View>

          <Pressable onPress={() => router.push('/forgot')} testID="login-forgot">
            <Text style={styles.forgot}>Forgot password?</Text>
          </Pressable>

          <Pressable style={[styles.cta, loading && { opacity: 0.6 }]} onPress={submit} disabled={loading} testID="login-submit">
            <Text style={styles.ctaText}>{loading ? 'Logging in...' : 'Login'}</Text>
          </Pressable>

          <View style={styles.row}>
            <Text style={{ color: colors.muted }}>Don't have an account? </Text>
            <Pressable onPress={() => router.push('/signup')} testID="login-go-signup">
              <Text style={styles.link}>Sign up</Text>
            </Pressable>
          </View>

          <View style={styles.hint} testID="demo-credentials-hint">
            <Text style={styles.hintTitle}>Demo Accounts</Text>
            <Text style={styles.hintText}>User: demo@earnhub.com / Demo@123</Text>
            <Text style={styles.hintText}>Admin: admin@earnhub.com / Admin@123</Text>
            <Text style={[styles.hintText, { marginTop: 4 }]}>OTP for all: 123456</Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  logo: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: spacing.lg, marginBottom: spacing.xl },
  brand: { fontSize: 24, fontWeight: '800', color: colors.onSurface },
  h1: { fontSize: 28, fontWeight: '800', color: colors.onSurface },
  sub: { fontSize: fontSize.base, color: colors.muted, marginTop: 4, marginBottom: spacing.xl },
  inputBox: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, paddingHorizontal: spacing.md, marginBottom: spacing.md, borderWidth: 1, borderColor: colors.border, height: 52 },
  input: { flex: 1, color: colors.onSurface, fontSize: fontSize.base },
  forgot: { color: colors.brand, fontWeight: '600', textAlign: 'right', marginBottom: spacing.lg },
  cta: { backgroundColor: colors.brand, paddingVertical: 16, borderRadius: radius.md, alignItems: 'center', marginTop: spacing.sm },
  ctaText: { color: '#fff', fontSize: fontSize.lg, fontWeight: '700' },
  row: { flexDirection: 'row', justifyContent: 'center', marginTop: spacing.lg },
  link: { color: colors.brand, fontWeight: '700' },
  hint: { marginTop: spacing.xl, padding: spacing.md, backgroundColor: colors.brandTertiary, borderRadius: radius.md },
  hintTitle: { fontWeight: '700', color: colors.onBrandTertiary, marginBottom: 4 },
  hintText: { color: colors.onBrandTertiary, fontSize: fontSize.sm },
});
