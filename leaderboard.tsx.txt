import { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '@/src/api';
import { colors, spacing, radius, fontSize } from '@/src/theme';

export default function Leaderboard() {
  const router = useRouter();
  const [rows, setRows] = useState<any[]>([]);
  useFocusEffect(useCallback(() => { api.get('/leaderboard').then(setRows); }, []));
  const top3 = rows.slice(0, 3); const rest = rows.slice(3);
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }} edges={['top']}>
      <ScrollView contentContainerStyle={{ paddingBottom: 60 }}>
        <View style={styles.headerRow}>
          <Pressable onPress={() => router.back()} testID="lb-back"><Ionicons name="chevron-back" size={28} color={colors.onSurface} /></Pressable>
          <Text style={styles.h1}>Leaderboard</Text>
        </View>
        <LinearGradient colors={['#0B1B6F', '#16A34A']} style={styles.top3}>
          {top3.length >= 2 && <Podium item={top3[1]} place={2} />}
          {top3.length >= 1 && <Podium item={top3[0]} place={1} />}
          {top3.length >= 3 && <Podium item={top3[2]} place={3} />}
        </LinearGradient>
        <View style={{ paddingHorizontal: spacing.lg }}>
          {rest.map((r) => (
            <View key={r.user_id} style={styles.row} testID={`lb-${r.rank}`}>
              <Text style={styles.rank}>#{r.rank}</Text>
              <View style={styles.av}><Text style={{ color: '#fff', fontWeight: '700' }}>{r.name?.[0]}</Text></View>
              <View style={{ flex: 1 }}>
                <Text style={styles.name}>{r.name}</Text>
                <Text style={styles.city}>{r.city} · {r.tasks_completed} tasks</Text>
              </View>
              <Text style={styles.earn}>₹{r.total_earned?.toFixed(0)}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function Podium({ item, place }: any) {
  const heights = { 1: 110, 2: 80, 3: 70 };
  const medals = { 1: '🥇', 2: '🥈', 3: '🥉' };
  return (
    <View style={{ alignItems: 'center', flex: 1 }}>
      <Text style={{ fontSize: 28 }}>{(medals as any)[place]}</Text>
      <View style={[ps.av, place === 1 && { width: 70, height: 70, borderRadius: 35 }]}><Text style={{ color: '#fff', fontWeight: '700', fontSize: place === 1 ? 24 : 18 }}>{item.name?.[0]}</Text></View>
      <Text style={ps.name} numberOfLines={1}>{item.name?.split(' ')[0]}</Text>
      <Text style={ps.earn}>₹{item.total_earned?.toFixed(0)}</Text>
      <View style={[ps.bar, { height: (heights as any)[place] }]} />
    </View>
  );
}

const ps = StyleSheet.create({
  av: { width: 56, height: 56, borderRadius: 28, backgroundColor: 'rgba(255,255,255,0.25)', alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: '#fff', marginVertical: 6 },
  name: { color: '#fff', fontWeight: '700', fontSize: 13 },
  earn: { color: '#fff', fontWeight: '800' },
  bar: { width: '70%', backgroundColor: 'rgba(255,255,255,0.18)', borderTopLeftRadius: 8, borderTopRightRadius: 8, marginTop: 8 },
});

const styles = StyleSheet.create({
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, padding: spacing.lg },
  h1: { fontSize: fontSize.xxl, fontWeight: '800', color: colors.onSurface },
  top3: { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: spacing.lg, paddingTop: spacing.lg, gap: 8, marginHorizontal: spacing.lg, borderRadius: radius.lg, marginBottom: spacing.lg },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border },
  rank: { fontWeight: '700', color: colors.onSurface, width: 36 },
  av: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.brandSecondary, alignItems: 'center', justifyContent: 'center' },
  name: { fontWeight: '700', color: colors.onSurface }, city: { fontSize: fontSize.sm, color: colors.muted },
  earn: { fontWeight: '800', color: colors.brand },
});
