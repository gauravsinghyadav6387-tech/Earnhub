import { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, Pressable } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '@/src/api';
import { colors, spacing, radius, fontSize } from '@/src/theme';
import { Toast } from '@/src/Toast';

export default function Withdraw() {
  const router = useRouter();
  const [wallet, setWallet] = useState<any>({ balance: 0 });
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState<'upi' | 'bank' | 'paytm'>('upi');
  const [upi, setUpi] = useState(''); const [acc, setAcc] = useState(''); const [ifsc, setIfsc] = useState(''); const [paytm, setPaytm] = useState('');
  const [msg, setMsg] = useState(''); const [err, setErr] = useState('');

  useFocusEffect(useCallback(() => { api.get('/wallet').then(setWallet); }, []));

  const submit = async () => {
    setErr(''); setMsg('');
    const amt = parseFloat(amount);
    if (!amt || amt < 100) { setErr('Min ₹100'); return; }
    if (amt > wallet.balance) { setErr('Insufficient balance'); return; }
    const details = method === 'upi' ? { upi } : method === 'bank' ? { account: acc, ifsc } : { paytm };
    if (method === 'upi' && !upi) { setErr('Enter UPI ID'); return; }
    if (method === 'bank' && (!acc || !ifsc)) { setErr('Enter bank details'); return; }
    if (method === 'paytm' && !paytm) { setErr('Enter Paytm number'); return; }
    try {
      await api.post('/wallet/withdraw', { amount: amt, method, details });
      setMsg('Withdrawal requested! Admin will approve shortly.');
      setTimeout(() => router.back(), 1500);
    } catch (e: any) { setErr(e.message); }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }} edges={['top']}>
      {msg ? <Toast message={msg} type="success" /> : null}
      {err ? <Toast message={err} type="error" /> : null}
      <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 80 }}>
        <View style={styles.headerRow}>
          <Pressable onPress={() => router.back()} testID="withdraw-back"><Ionicons name="chevron-back" size={28} color={colors.onSurface} /></Pressable>
          <Text style={styles.h1}>Withdraw</Text>
        </View>
        <LinearGradient colors={['#0B1B6F', '#1E3A8A']} style={styles.balCard}>
          <Text style={styles.balLab}>Available Balance</Text>
          <Text style={styles.balVal}>₹{wallet.balance?.toFixed(2)}</Text>
        </LinearGradient>

        <Text style={styles.label}>Method</Text>
        <View style={{ flexDirection: 'row', gap: 8 }}>
          {(['upi', 'bank', 'paytm'] as const).map((m) => (
            <Pressable key={m} style={[styles.methodCard, method === m && styles.methodActive]} onPress={() => setMethod(m)} testID={`method-${m}`}>
              <Ionicons name={m === 'upi' ? 'phone-portrait' : m === 'bank' ? 'business' : 'wallet'} size={22} color={method === m ? '#fff' : colors.onSurface} />
              <Text style={[styles.methodText, method === m && { color: '#fff' }]}>{m.toUpperCase()}</Text>
            </Pressable>
          ))}
        </View>

        {method === 'upi' && <TextInput style={styles.input} placeholder="UPI ID (eg: john@upi)" placeholderTextColor={colors.muted} value={upi} onChangeText={setUpi} autoCapitalize="none" testID="upi-input" />}
        {method === 'bank' && <>
          <TextInput style={styles.input} placeholder="Account Number" placeholderTextColor={colors.muted} value={acc} onChangeText={setAcc} keyboardType="numeric" testID="acc-input" />
          <TextInput style={styles.input} placeholder="IFSC Code" placeholderTextColor={colors.muted} value={ifsc} onChangeText={setIfsc} autoCapitalize="characters" testID="ifsc-input" />
        </>}
        {method === 'paytm' && <TextInput style={styles.input} placeholder="Paytm Mobile Number" placeholderTextColor={colors.muted} value={paytm} onChangeText={setPaytm} keyboardType="phone-pad" testID="paytm-input" />}

        <Text style={styles.label}>Amount</Text>
        <TextInput style={styles.input} placeholder="₹ 0" placeholderTextColor={colors.muted} value={amount} onChangeText={setAmount} keyboardType="numeric" testID="amount-input" />
        <View style={{ flexDirection: 'row', gap: 8, marginBottom: spacing.lg }}>
          {[100, 500, 1000].map((a) => (
            <Pressable key={a} style={styles.quick} onPress={() => setAmount(String(a))} testID={`quick-${a}`}><Text style={styles.quickText}>₹{a}</Text></Pressable>
          ))}
          <Pressable style={styles.quick} onPress={() => setAmount(String(Math.floor(wallet.balance)))} testID="quick-max"><Text style={styles.quickText}>Max</Text></Pressable>
        </View>

        <View style={styles.summary}>
          <View style={styles.sumRow}><Text style={styles.sumLab}>Amount</Text><Text style={styles.sumVal}>₹{amount || 0}</Text></View>
          <View style={styles.sumRow}><Text style={styles.sumLab}>Fee</Text><Text style={styles.sumVal}>₹0</Text></View>
          <View style={[styles.sumRow, { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: spacing.sm, marginTop: spacing.sm }]}><Text style={[styles.sumLab, { fontWeight: '700' }]}>You'll Receive</Text><Text style={[styles.sumVal, { color: colors.brand, fontSize: fontSize.lg, fontWeight: '800' }]}>₹{amount || 0}</Text></View>
        </View>

        <Pressable style={styles.cta} onPress={submit} testID="withdraw-submit">
          <Text style={styles.ctaText}>Request Withdrawal</Text>
        </Pressable>
        <Text style={styles.note}>Min ₹100. Processed within 24-48 hrs after admin approval.</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.md },
  h1: { fontSize: fontSize.xxl, fontWeight: '800', color: colors.onSurface },
  balCard: { padding: spacing.lg, borderRadius: radius.lg, marginBottom: spacing.lg },
  balLab: { color: 'rgba(255,255,255,0.8)' },
  balVal: { color: '#fff', fontSize: 32, fontWeight: '800', marginTop: 4 },
  label: { fontSize: fontSize.sm, fontWeight: '600', color: colors.onSurface, marginTop: spacing.md, marginBottom: 6 },
  methodCard: { flex: 1, paddingVertical: spacing.md, borderRadius: radius.md, alignItems: 'center', borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surfaceSecondary, gap: 4 },
  methodActive: { backgroundColor: colors.brandSecondary, borderColor: colors.brandSecondary },
  methodText: { fontWeight: '600', color: colors.onSurface, fontSize: fontSize.sm },
  input: { backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: 14, fontSize: fontSize.lg, color: colors.onSurface, borderWidth: 1, borderColor: colors.border, marginTop: spacing.sm },
  quick: { flex: 1, paddingVertical: 10, borderRadius: radius.md, backgroundColor: colors.brandTertiary, alignItems: 'center' },
  quickText: { color: colors.onBrandTertiary, fontWeight: '700' },
  summary: { backgroundColor: colors.surfaceSecondary, padding: spacing.md, borderRadius: radius.md },
  sumRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  sumLab: { color: colors.muted }, sumVal: { color: colors.onSurface, fontWeight: '600' },
  cta: { backgroundColor: colors.brand, paddingVertical: 16, borderRadius: radius.md, alignItems: 'center', marginTop: spacing.lg },
  ctaText: { color: '#fff', fontSize: fontSize.lg, fontWeight: '700' },
  note: { fontSize: fontSize.sm, color: colors.muted, textAlign: 'center', marginTop: spacing.md },
});
