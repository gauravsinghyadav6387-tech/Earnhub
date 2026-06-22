import { useState } from 'react';
import { View, Text, StyleSheet, TextInput, Pressable, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '@/src/auth';
import { colors, spacing, radius, fontSize } from '@/src/theme';
import { Toast } from '@/src/Toast';

export default function Signup() {
  const router = useRouter();
  const { signup } = useAuth();
  const [form, setForm] = useState({ full_name: '', mobile: '', email: '', password: '', city: '', state: '', referral_code: '' });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  const update = (k: string, v: string) => setForm({ ...form, [k]: v });

  const submit = async () => {
    setErr('');
    if (!form.full_name || !form.email || !form.password || !form.mobile || !form.city || !form.state) {
      setErr('Please fill all required fields'); return;
    }
    if (form.password.length < 6) { setErr('Password must be 6+ chars'); return; }
    setLoading(true);
    try {
      await signup({ ...form, referral_code: form.referral_code || null });
      router.push({ pathname: '/otp', params: { email: form.email.trim(), flow: 'signup' } });
    } catch (e: any) {
      setErr(e.message || 'Signup failed');
    } finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 80 }} keyboardShouldPersistTaps="handled">
          <Pressable onPress={() => router.back()} testID="signup-back" style={{ marginBottom: spacing.md }}>
            <Ionicons name="chevron-back" size={28} color={colors.onSurface} />
          </Pressable>
          <Text style={styles.h1}>Create account</Text>
          <Text style={styles.sub}>Start earning in minutes</Text>
          {err ? <Toast message={err} type="error" /> : null}

          {[
            { k: 'full_name', label: 'Full Name', icon: 'person', kb: 'default' },
            { k: 'mobile', label: 'Mobile Number', icon: 'call', kb: 'phone-pad' },
            { k: 'email', label: 'Email', icon: 'mail', kb: 'email-address' },
            { k: 'password', label: 'Password (6+ chars)', icon: 'lock-closed', kb: 'default', secure: true },
            { k: 'city', label: 'City', icon: 'business', kb: 'default' },
            { k: 'state', label: 'State', icon: 'map', kb: 'default' },
            { k: 'referral_code', label: 'Referral Code (optional)', icon: 'gift', kb: 'default' },
          ].map((f) => (
            <View key={f.k} style={styles.inputBox}>
              <Ionicons name={f.icon as any} size={20} color={colors.muted} />
              <TextInput
                style={styles.input}
                placeholder={f.label}
                placeholderTextColor={colors.muted}
                value={(form as any)[f.k]}
                onChangeText={(v) => update(f.k, v)}
                keyboardType={f.kb as any}
                secureTextEntry={!!f.secure}
                autoCapitalize={f.k === 'email' ? 'none' : 'words'}
                testID={`signup-${f.k}`}
              />
            </View>
          ))}

          <Pressable style={[styles.cta, loading && { opacity: 0.6 }]} onPress={submit} disabled={loading} testID="signup-submit">
            <Text style={styles.ctaText}>{loading ? 'Creating...' : 'Create Account'}</Text>
          </Pressable>

          <View style={styles.row}>
            <Text style={{ color: colors.muted }}>Already have an account? </Text>
            <Pressable onPress={() => router.replace('/login')} testID="signup-go-login">
              <Text style={styles.link}>Login</Text>
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  h1: { fontSize: 28, fontWeight: '800', color: colors.onSurface },
  sub: { fontSize: fontSize.base, color: colors.muted, marginTop: 4, marginBottom: spacing.lg },
  inputBox: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, paddingHorizontal: spacing.md, marginBottom: spacing.md, borderWidth: 1, borderColor: colors.border, height: 52 },
  input: { flex: 1, color: colors.onSurface, fontSize: fontSize.base },
  cta: { backgroundColor: colors.brand, paddingVertical: 16, borderRadius: radius.md, alignItems: 'center', marginTop: spacing.sm },
  ctaText: { color: '#fff', fontSize: fontSize.lg, fontWeight: '700' },
  row: { flexDirection: 'row', justifyContent: 'center', marginTop: spacing.lg },
  link: { color: colors.brand, fontWeight: '700' },
});
