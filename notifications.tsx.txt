import { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '@/src/api';
import { colors, spacing, radius, fontSize } from '@/src/theme';

export default function Notifications() {
  const router = useRouter();
  const [items, setItems] = useState<any[]>([]);
  const load = useCallback(() => api.get('/notifications').then(setItems), []);
  useFocusEffect(useCallback(() => { load(); }, [load]));
  const markRead = async (id: string) => { await api.post(`/notifications/${id}/read`); load(); };
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }} edges={['top']}>
      <View style={styles.headerRow}>
        <Pressable onPress={() => router.back()} testID="notif-back"><Ionicons name="chevron-back" size={28} color={colors.onSurface} /></Pressable>
        <Text style={styles.h1}>Notifications</Text>
      </View>
      <ScrollView contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: 60 }}>
        {items.length === 0 && <Text style={styles.empty}>No notifications yet</Text>}
        {items.map((n) => (
          <Pressable key={n.id} style={[styles.item, !n.read && styles.unread]} onPress={() => markRead(n.id)} testID={`notif-${n.id}`}>
            <View style={[styles.icon, { backgroundColor: colors.brandTertiary }]}><Ionicons name={n.type === 'referral' ? 'gift' : n.type === 'withdrawal' ? 'cash' : n.type === 'document' ? 'document' : 'briefcase'} size={20} color={colors.brand} /></View>
            <View style={{ flex: 1 }}>
              <Text style={styles.title}>{n.title}</Text>
              <Text style={styles.body}>{n.body}</Text>
              <Text style={styles.date}>{new Date(n.created_at).toLocaleString()}</Text>
            </View>
            {!n.read && <View style={styles.dot} />}
          </Pressable>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, padding: spacing.lg },
  h1: { fontSize: fontSize.xxl, fontWeight: '800', color: colors.onSurface },
  empty: { textAlign: 'center', color: colors.muted, marginTop: 40 },
  item: { flexDirection: 'row', gap: spacing.md, padding: spacing.md, backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.border },
  unread: { borderColor: colors.brand, backgroundColor: colors.brandTertiary + '40' },
  icon: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  title: { fontWeight: '700', color: colors.onSurface }, body: { color: colors.muted, marginTop: 2 },
  date: { color: colors.muted, fontSize: fontSize.sm, marginTop: 4 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.brand, alignSelf: 'center' },
});
