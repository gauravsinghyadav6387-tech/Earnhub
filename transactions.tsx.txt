import { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '@/src/api';
import { colors, spacing, radius, fontSize } from '@/src/theme';

export default function Transactions() {
  const router = useRouter();
  const [wallet, setWallet] = useState<any>({});
  const [txns, setTxns] = useState<any[]>([]);
  const [tab, setTab] = useState<'all' | 'earning' | 'withdrawal' | 'pending'>('all');

  useFocusEffect(useCallback(() => {
    api.get('/wallet').then(setWallet);
    api.get('/transactions').then(setTxns);
  }, []));

  const filtered = txns.filter((t) => tab === 'all' || (tab === 'pending' ? t.status === 'pending' : t.type === tab));

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }} edges={['top']}>
      <ScrollView contentContainerStyle={{ paddingBottom: 60 }}>
        <View style={styles.headerRow}>
          <Pressable onPress={() => router.back()} testID="txn-back"><Ionicons name="chevron-back" size={28} color={colors.onSurface} /></Pressable>
          <Text style={styles.h1}>Payouts & Transactions</Text>
        </View>
        <LinearGradient colors={['#0B1B6F', '#1E3A8A']} style={styles.balCard}>
          <Text style={styles.balLab}>Wallet Balance</Text>
          <Text style={styles.balVal}>₹{wallet.balance?.toFixed(2) || '0.00'}</Text>
          <View style={styles.statsRow}>
            <View><Text style={styles.statLab}>Total Earned</Text><Text style={styles.statVal}>₹{wallet.total_earned?.toFixed(0) || 0}</Text></View>
            <View><Text style={styles.statLab}>Withdrawn</Text><Text style={styles.statVal}>₹{wallet.total_withdrawn?.toFixed(0) || 0}</Text></View>
            <View><Text style={styles.statLab}>Pending</Text><Text style={styles.statVal}>₹{wallet.pending?.toFixed(0) || 0}</Text></View>
          </View>
          <Pressable style={styles.wBtn} onPress={() => router.push('/withdraw')} testID="txn-withdraw">
            <Text style={{ color: '#0B1B6F', fontWeight: '700' }}>Withdraw</Text>
          </Pressable>
        </LinearGradient>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingHorizontal: spacing.lg, marginBottom: spacing.md }}>
          {(['all', 'earning', 'withdrawal', 'pending'] as const).map((t) => (
            <Pressable key={t} style={[styles.chip, tab === t && styles.chipActive]} onPress={() => setTab(t)} testID={`txn-tab-${t}`}>
              <Text style={[styles.chipText, tab === t && { color: '#fff' }]}>{t[0].toUpperCase() + t.slice(1)}</Text>
            </Pressable>
          ))}
        </ScrollView>

        <View style={{ paddingHorizontal: spacing.lg }}>
          {filtered.length === 0 && <Text style={styles.empty}>No transactions yet</Text>}
          {filtered.map((t) => (
            <View key={t.id} style={styles.txn} testID={`txn-${t.id}`}>
              <View style={[styles.txIcon, { backgroundColor: t.type === 'earning' ? colors.brandTertiary : t.type === 'referral' ? '#FEF3C7' : '#FEE2E2' }]}>
                <Ionicons name={t.type === 'earning' ? 'arrow-down' : t.type === 'referral' ? 'gift' : 'arrow-up'} size={20} color={t.type === 'earning' ? colors.brand : t.type === 'referral' ? colors.warning : colors.error} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.txTitle}>{t.note}</Text>
                <Text style={styles.txDate}>{new Date(t.created_at).toLocaleDateString()} · {t.status}</Text>
              </View>
              <Text style={[styles.txAmt, { color: t.amount > 0 ? colors.brand : colors.error }]}>{t.amount > 0 ? '+' : ''}₹{Math.abs(t.amount).toFixed(0)}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, padding: spacing.lg },
  h1: { fontSize: fontSize.xl, fontWeight: '800', color: colors.onSurface },
  balCard: { marginHorizontal: spacing.lg, padding: spacing.lg, borderRadius: radius.lg, marginBottom: spacing.lg },
  balLab: { color: 'rgba(255,255,255,0.8)' }, balVal: { color: '#fff', fontSize: 32, fontWeight: '800', marginTop: 4, marginBottom: spacing.md },
  statsRow: { flexDirection: 'row', justifyContent: 'space-between' },
  statLab: { color: 'rgba(255,255,255,0.7)', fontSize: 11 }, statVal: { color: '#fff', fontWeight: '700' },
  wBtn: { backgroundColor: '#fff', alignSelf: 'flex-start', paddingHorizontal: spacing.md, paddingVertical: 8, borderRadius: radius.pill, marginTop: spacing.md },
  chip: { paddingHorizontal: spacing.md, height: 36, borderRadius: radius.pill, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border, alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  chipActive: { backgroundColor: colors.brandSecondary, borderColor: colors.brandSecondary },
  chipText: { fontSize: fontSize.sm, fontWeight: '600', color: colors.onSurface },
  empty: { textAlign: 'center', color: colors.muted, marginTop: 40 },
  txn: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border },
  txIcon: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  txTitle: { color: colors.onSurface, fontWeight: '600' }, txDate: { color: colors.muted, fontSize: fontSize.sm, marginTop: 2 },
  txAmt: { fontWeight: '800', fontSize: fontSize.base },
});
