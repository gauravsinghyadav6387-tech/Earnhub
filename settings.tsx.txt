import { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Switch } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '@/src/auth';
import { colors, spacing, radius, fontSize } from '@/src/theme';

export default function Settings() {
  const router = useRouter();
  const { logout } = useAuth();
  const [taskNotif, setTaskNotif] = useState(true);
  const [payNotif, setPayNotif] = useState(true);
  const [promo, setPromo] = useState(false);
  const [dark, setDark] = useState(false);
  const [twofa, setTwofa] = useState(false);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }} edges={['top']}>
      <ScrollView contentContainerStyle={{ paddingBottom: 60 }}>
        <View style={styles.headerRow}>
          <Pressable onPress={() => router.back()} testID="set-back"><Ionicons name="chevron-back" size={28} color={colors.onSurface} /></Pressable>
          <Text style={styles.h1}>Settings</Text>
        </View>
        <Section title="Account">
          <Item icon="person" label="Edit Profile" onPress={() => router.push('/edit-profile')} />
          <Item icon="call" label="Change Mobile" />
          <Item icon="mail" label="Change Email" />
          <Item icon="lock-closed" label="Change Password" onPress={() => router.push('/forgot')} />
        </Section>
        <Section title="Notifications">
          <Toggle icon="briefcase" label="Task Notifications" value={taskNotif} onChange={setTaskNotif} />
          <Toggle icon="cash" label="Payment Notifications" value={payNotif} onChange={setPayNotif} />
          <Toggle icon="megaphone" label="Promotions" value={promo} onChange={setPromo} />
        </Section>
        <Section title="Preferences">
          <Toggle icon="moon" label="Dark Mode" value={dark} onChange={setDark} />
          <Item icon="language" label="Language: English" />
          <Item icon="location" label="Location Permission" />
        </Section>
        <Section title="Security">
          <Toggle icon="shield-checkmark" label="Two Factor Authentication" value={twofa} onChange={setTwofa} />
          <Item icon="phone-portrait" label="Login Devices" />
        </Section>
        <Section title="Payments">
          <Item icon="card" label="Manage UPI / Bank" onPress={() => router.push('/withdraw')} />
        </Section>
        <Section title="Data">
          <Item icon="download" label="Download My Data" />
          <Item icon="trash" label="Clear Cache" />
        </Section>
        <Pressable style={styles.logout} onPress={async () => { await logout(); router.replace('/login'); }} testID="set-logout">
          <Ionicons name="log-out" size={20} color={colors.error} />
          <Text style={{ color: colors.error, fontWeight: '700' }}>Logout</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

function Section({ title, children }: any) {
  return <View style={{ marginBottom: spacing.lg }}>
    <Text style={styles.section}>{title}</Text>
    <View style={styles.sectionCard}>{children}</View>
  </View>;
}

function Item({ icon, label, onPress }: any) {
  return <Pressable style={styles.row} onPress={onPress} testID={`set-${label.toLowerCase().replace(/[^a-z]/g, '-')}`}>
    <View style={styles.left}><Ionicons name={icon} size={20} color={colors.brandSecondary} /><Text style={styles.label}>{label}</Text></View>
    <Ionicons name="chevron-forward" size={18} color={colors.muted} />
  </Pressable>;
}

function Toggle({ icon, label, value, onChange }: any) {
  return <View style={styles.row}>
    <View style={styles.left}><Ionicons name={icon} size={20} color={colors.brandSecondary} /><Text style={styles.label}>{label}</Text></View>
    <Switch value={value} onValueChange={onChange} trackColor={{ true: colors.brand }} />
  </View>;
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, padding: spacing.lg },
  h1: { fontSize: fontSize.xxl, fontWeight: '800', color: colors.onSurface },
  section: { paddingHorizontal: spacing.lg, fontSize: fontSize.sm, fontWeight: '700', color: colors.muted, textTransform: 'uppercase', marginBottom: spacing.sm },
  sectionCard: { marginHorizontal: spacing.lg, backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: 4 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: colors.border },
  left: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  label: { color: colors.onSurface, fontWeight: '500' },
  logout: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, marginHorizontal: spacing.lg, paddingVertical: 14, borderRadius: radius.md, borderWidth: 1, borderColor: colors.error, marginTop: spacing.md },
});
