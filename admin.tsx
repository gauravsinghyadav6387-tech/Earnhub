import { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, ActivityIndicator } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '@/src/api';
import { useAuth } from '@/src/auth';
import { colors, spacing, radius, fontSize } from '@/src/theme';
import { Toast } from '@/src/Toast';

export default function Admin() {
  const router = useRouter();
  const { logout } = useAuth();
  const [stats, setStats] = useState<any>({});
  const [tab, setTab] = useState<'withdrawals' | 'documents' | 'tasks' | 'tickets' | 'users'>('withdrawals');
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, i] = await Promise.all([
        api.get('/admin/stats'),
        api.get(tab === 'tasks' ? '/admin/task-submissions' : `/admin/${tab}`)
      ]);
      setStats(s); setItems(i);
    } catch (e: any) { setMsg(e.message); }
    setLoading(false);
  }, [tab]);
  useFocusEffect(useCallback(() => { load(); }, [load]));

  const act = async (id: string, action: 'approve' | 'reject') => {
    try {
      const endpoint = tab === 'tasks' ? `/admin/task-submissions/${id}` : `/admin/${tab}/${id}`;
      await api.post(endpoint, { action });
      setMsg(`${action}d`); setTimeout(() => setMsg(''), 1500);
      load();
    } catch (e: any) { setMsg(e.message); }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }} edges={['top']}>
      {msg ? <Toast message={msg} type="success" /> : null}
      <LinearGradient colors={['#0B1B6F', '#1E3A8A']} style={styles.top}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={styles.h1}>Admin Panel</Text>
          <Pressable onPress={async () => { await logout(); router.replace('/login'); }} testID="admin-logout">
            <Ionicons name="log-out" size={22} color="#fff" />
          </Pressable>
        </View>
        <View style={styles.statsGrid}>
          <Stat n={stats.users || 0} l="Users" />
          <Stat n={stats.tasks || 0} l="Tasks" />
          <Stat n={stats.pending_withdrawals || 0} l="Withdrawals" hot />
          <Stat n={stats.pending_documents || 0} l="Documents" hot />
        </View>
      </LinearGradient>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, padding: spacing.md }}>
        {(['withdrawals', 'documents', 'tasks', 'tickets', 'users'] as const).map((t) => (
          <Pressable key={t} style={[styles.chip, tab === t && styles.chipActive]} onPress={() => setTab(t)} testID={`admin-tab-${t}`}>
            <Text style={[styles.chipText, tab === t && { color: '#fff' }]}>{t[0].toUpperCase() + t.slice(1)}</Text>
          </Pressable>
        ))}
      </ScrollView>
      {loading ? <ActivityIndicator color={colors.brand} style={{ marginTop: 40 }} /> :
        <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 60 }}>
          {items.length === 0 && <Text style={styles.empty}>No items</Text>}
          {items.map((it) => (
            <View key={it.id} style={styles.card} testID={`admin-item-${it.id}`}>
              {tab === 'withdrawals' && <>
                <View style={styles.cardTop}><Text style={styles.cardTitle}>{it.user_name}</Text><Text style={styles.cardAmt}>₹{it.amount}</Text></View>
                <Text style={styles.cardSub}>{it.method.toUpperCase()} · {JSON.stringify(it.details)}</Text>
                <Text style={styles.cardSub}>Status: {it.status}</Text>
              </>}
              {tab === 'documents' && <>
                <Text style={styles.cardTitle}>{it.user_name} - {it.doc_type.toUpperCase()}</Text>
                <Text style={styles.cardSub}>Status: {it.status}</Text>
              </>}
              {tab === 'tasks' && <>
                <View style={styles.cardTop}><Text style={styles.cardTitle}>{it.task_title}</Text><Text style={styles.cardAmt}>₹{it.budget}</Text></View>
                <Text style={styles.cardSub}>By {it.user_name}</Text>
                <Text style={styles.cardSub}>Note: {it.note || '-'}</Text>
              </>}
              {tab === 'tickets' && <>
                <Text style={styles.cardTitle}>{it.category} - {it.user_name}</Text>
                <Text style={styles.cardSub}>{it.description}</Text>
                <Text style={styles.cardSub}>Status: {it.status}</Text>
              </>}
              {tab === 'users' && <>
                <Text style={styles.cardTitle}>{it.full_name}</Text>
                <Text style={styles.cardSub}>{it.email} · {it.city}, {it.state}</Text>
                <Text style={styles.cardSub}>Tasks: {it.tasks_completed} · Level: {it.level}</Text>
              </>}
              {(tab === 'withdrawals' || tab === 'documents' || tab === 'tasks') && it.status !== 'approved' && it.status !== 'verified' && it.status !== 'rejected' && (
                <View style={{ flexDirection: 'row', gap: 8, marginTop: spacing.sm }}>
                  <Pressable style={[styles.btn, { backgroundColor: colors.brand }]} onPress={() => act(it.id, 'approve')} testID={`approve-${it.id}`}>
                    <Text style={{ color: '#fff', fontWeight: '700' }}>Approve</Text>
                  </Pressable>
                  <Pressable style={[styles.btn, { backgroundColor: colors.error }]} onPress={() => act(it.id, 'reject')} testID={`reject-${it.id}`}>
                    <Text style={{ color: '#fff', fontWeight: '700' }}>Reject</Text>
                  </Pressable>
                </View>
              )}
            </View>
          ))}
        </ScrollView>
      }
    </SafeAreaView>
  );
}

function Stat({ n, l, hot }: any) {
  return <View style={styles.stat}>
    <Text style={[styles.statN, hot && n > 0 && { color: colors.warning }]}>{n}</Text>
    <Text style={styles.statL}>{l}</Text>
  </View>;
}

const styles = StyleSheet.create({
  top: { padding: spacing.lg },
  h1: { fontSize: fontSize.xxl, fontWeight: '800', color: '#fff' },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md },
  stat: { width: '48%', backgroundColor: 'rgba(255,255,255,0.12)', padding: spacing.md, borderRadius: radius.md },
  statN: { color: '#fff', fontSize: 28, fontWeight: '800' }, statL: { color: 'rgba(255,255,255,0.8)' },
  chip: { paddingHorizontal: spacing.md, height: 36, borderRadius: radius.pill, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border, alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  chipActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  chipText: { fontSize: fontSize.sm, fontWeight: '600', color: colors.onSurface },
  empty: { textAlign: 'center', color: colors.muted, marginTop: 40 },
  card: { padding: spacing.md, backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.border },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between' },
  cardTitle: { fontWeight: '700', color: colors.onSurface, flex: 1 },
  cardAmt: { fontWeight: '800', color: colors.brand },
  cardSub: { color: colors.muted, marginTop: 2, fontSize: fontSize.sm },
  btn: { flex: 1, paddingVertical: 10, borderRadius: radius.md, alignItems: 'center' },
});
