import { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, TextInput, Linking } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '@/src/api';
import { colors, spacing, radius, fontSize } from '@/src/theme';
import { Toast } from '@/src/Toast';

const FAQS = [
  { q: 'How do I withdraw money?', a: 'Go to Wallet > Withdraw. Minimum ₹100. Approval within 24-48 hrs.' },
  { q: 'When do I get paid for a task?', a: 'After your proof is approved by the task poster or admin.' },
  { q: 'How does the referral work?', a: 'Share your code. When a friend signs up using it, you both get ₹50.' },
  { q: 'Why was my document rejected?', a: 'Common reasons: blurry image, wrong document type, name mismatch.' },
];

export default function Support() {
  const router = useRouter();
  const [tickets, setTickets] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const [cat, setCat] = useState('Payment');
  const [desc, setDesc] = useState('');
  const [msg, setMsg] = useState('');
  const [exp, setExp] = useState<number | null>(null);

  const load = useCallback(() => api.get('/tickets').then(setTickets), []);
  useFocusEffect(useCallback(() => { load(); }, [load]));

  const submit = async () => {
    if (!desc) return;
    try {
      await api.post('/tickets', { category: cat, description: desc });
      setMsg('Ticket raised!'); setOpen(false); setDesc('');
      load(); setTimeout(() => setMsg(''), 2000);
    } catch (e: any) { setMsg(e.message); }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }} edges={['top']}>
      {msg ? <Toast message={msg} type="success" /> : null}
      <ScrollView contentContainerStyle={{ padding: spacing.lg, paddingBottom: 80 }}>
        <View style={styles.headerRow}>
          <Pressable onPress={() => router.back()} testID="sup-back"><Ionicons name="chevron-back" size={28} color={colors.onSurface} /></Pressable>
          <Text style={styles.h1}>Help & Support</Text>
        </View>

        <View style={styles.contactRow}>
          <Pressable style={styles.contact} onPress={() => Linking.openURL('https://wa.me/919999999999')} testID="sup-whatsapp">
            <Ionicons name="logo-whatsapp" size={24} color="#25D366" />
            <Text style={styles.contactText}>WhatsApp</Text>
          </Pressable>
          <Pressable style={styles.contact} onPress={() => Linking.openURL('mailto:support@earnhub.com')} testID="sup-email">
            <Ionicons name="mail" size={24} color={colors.info} />
            <Text style={styles.contactText}>Email</Text>
          </Pressable>
          <Pressable style={styles.contact} onPress={() => Linking.openURL('tel:+919999999999')} testID="sup-call">
            <Ionicons name="call" size={24} color={colors.brand} />
            <Text style={styles.contactText}>Call</Text>
          </Pressable>
        </View>

        <Text style={styles.section}>FAQ</Text>
        {FAQS.map((f, i) => (
          <Pressable key={i} style={styles.faq} onPress={() => setExp(exp === i ? null : i)} testID={`faq-${i}`}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text style={styles.q}>{f.q}</Text>
              <Ionicons name={exp === i ? 'chevron-up' : 'chevron-down'} size={20} color={colors.muted} />
            </View>
            {exp === i && <Text style={styles.a}>{f.a}</Text>}
          </Pressable>
        ))}

        <Pressable style={styles.cta} onPress={() => setOpen(true)} testID="sup-raise">
          <Ionicons name="add-circle" size={20} color="#fff" />
          <Text style={styles.ctaText}>Raise Ticket</Text>
        </Pressable>

        {open && (
          <View style={styles.ticketForm}>
            <Text style={styles.formLabel}>Category</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
              {['Payment', 'Task', 'Account', 'Other'].map((c) => (
                <Pressable key={c} style={[styles.chip, cat === c && styles.chipActive]} onPress={() => setCat(c)}>
                  <Text style={[styles.chipText, cat === c && { color: '#fff' }]}>{c}</Text>
                </Pressable>
              ))}
            </ScrollView>
            <TextInput style={[styles.input, { height: 100, textAlignVertical: 'top' }]} placeholder="Describe your issue..." placeholderTextColor={colors.muted} value={desc} onChangeText={setDesc} multiline testID="ticket-desc" />
            <Pressable style={styles.cta} onPress={submit} testID="ticket-submit"><Text style={styles.ctaText}>Submit Ticket</Text></Pressable>
          </View>
        )}

        <Text style={styles.section}>Your Tickets</Text>
        {tickets.length === 0 && <Text style={{ color: colors.muted }}>No tickets yet</Text>}
        {tickets.map((t) => (
          <View key={t.id} style={styles.ticket} testID={`ticket-${t.id}`}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={styles.tCat}>{t.category}</Text>
              <Text style={[styles.tStatus, { color: t.status === 'closed' ? colors.success : colors.warning }]}>{t.status.toUpperCase()}</Text>
            </View>
            <Text style={styles.tDesc}>{t.description}</Text>
            <Text style={styles.tDate}>{new Date(t.created_at).toLocaleDateString()}</Text>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.lg },
  h1: { fontSize: fontSize.xxl, fontWeight: '800', color: colors.onSurface },
  contactRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.lg },
  contact: { flex: 1, padding: spacing.md, backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, alignItems: 'center', gap: 6 },
  contactText: { fontWeight: '600', color: colors.onSurface },
  section: { fontSize: fontSize.lg, fontWeight: '700', color: colors.onSurface, marginVertical: spacing.md },
  faq: { padding: spacing.md, backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, marginBottom: spacing.sm },
  q: { fontWeight: '700', color: colors.onSurface, flex: 1 },
  a: { color: colors.muted, marginTop: spacing.sm },
  cta: { flexDirection: 'row', gap: 8, backgroundColor: colors.brand, paddingVertical: 14, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', marginTop: spacing.md },
  ctaText: { color: '#fff', fontSize: fontSize.lg, fontWeight: '700' },
  ticketForm: { marginTop: spacing.md, padding: spacing.md, backgroundColor: colors.surfaceSecondary, borderRadius: radius.md },
  formLabel: { fontWeight: '600', marginBottom: 6 },
  chip: { paddingHorizontal: spacing.md, height: 36, borderRadius: radius.pill, backgroundColor: '#fff', borderWidth: 1, borderColor: colors.border, alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  chipActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  chipText: { fontSize: fontSize.sm, fontWeight: '600', color: colors.onSurface },
  input: { backgroundColor: '#fff', borderRadius: radius.md, padding: spacing.md, marginTop: spacing.md, borderWidth: 1, borderColor: colors.border, fontSize: fontSize.base },
  ticket: { padding: spacing.md, backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, marginBottom: spacing.sm },
  tCat: { fontWeight: '700', color: colors.brandSecondary }, tStatus: { fontWeight: '700', fontSize: fontSize.sm },
  tDesc: { color: colors.onSurface, marginTop: 4 }, tDate: { color: colors.muted, fontSize: fontSize.sm, marginTop: 4 },
});
