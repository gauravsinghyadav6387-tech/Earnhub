import { useState } from 'react';
import { View, Text, StyleSheet, Pressable, Dimensions, FlatList } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, spacing, radius, fontSize } from '@/src/theme';

const { width } = Dimensions.get('window');

const slides = [
  { icon: 'search', title: 'Find Local Gigs', desc: 'Discover tasks near you - delivery, surveys, photography & more', color: '#0B1B6F' },
  { icon: 'cash', title: 'Earn Instantly', desc: 'Complete tasks, get paid directly to UPI, Bank or Paytm', color: '#16A34A' },
  { icon: 'trophy', title: 'Rise the Ranks', desc: 'Build streaks, climb leaderboards, refer friends for bonuses', color: '#0B1B6F' },
];

export default function Onboarding() {
  const router = useRouter();
  const [idx, setIdx] = useState(0);

  const next = () => {
    if (idx < slides.length - 1) setIdx(idx + 1);
    else router.replace('/login');
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <Pressable style={styles.skip} onPress={() => router.replace('/login')} testID="onboarding-skip">
        <Text style={styles.skipText}>Skip</Text>
      </Pressable>
      <FlatList
        data={slides}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        keyExtractor={(_, i) => String(i)}
        onMomentumScrollEnd={(e) => setIdx(Math.round(e.nativeEvent.contentOffset.x / width))}
        renderItem={({ item }) => (
          <View style={[styles.slide, { width }]}>
            <LinearGradient colors={[item.color, item.color === '#0B1B6F' ? '#16A34A' : '#0B1B6F']} style={styles.iconCircle}>
              <Ionicons name={item.icon as any} size={80} color="#fff" />
            </LinearGradient>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.desc}>{item.desc}</Text>
          </View>
        )}
      />
      <View style={styles.dots}>
        {slides.map((_, i) => (
          <View key={i} style={[styles.dot, i === idx && styles.dotActive]} />
        ))}
      </View>
      <Pressable style={styles.cta} onPress={next} testID="onboarding-next">
        <Text style={styles.ctaText}>{idx === slides.length - 1 ? 'Get Started' : 'Next'}</Text>
        <Ionicons name="arrow-forward" size={20} color="#fff" />
      </Pressable>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  skip: { position: 'absolute', top: 60, right: spacing.lg, zIndex: 10, padding: spacing.sm },
  skipText: { color: colors.muted, fontSize: fontSize.base, fontWeight: '600' },
  slide: { alignItems: 'center', justifyContent: 'center', paddingHorizontal: spacing.xl },
  iconCircle: { width: 200, height: 200, borderRadius: 100, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.xl },
  title: { fontSize: 28, fontWeight: '800', color: colors.onSurface, textAlign: 'center', marginBottom: spacing.md },
  desc: { fontSize: fontSize.lg, color: colors.muted, textAlign: 'center', lineHeight: 24, paddingHorizontal: spacing.lg },
  dots: { flexDirection: 'row', justifyContent: 'center', gap: 8, marginVertical: spacing.lg },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.border },
  dotActive: { width: 24, backgroundColor: colors.brand },
  cta: { backgroundColor: colors.brand, marginHorizontal: spacing.lg, marginBottom: spacing.lg, paddingVertical: 16, borderRadius: radius.lg, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  ctaText: { color: '#fff', fontSize: fontSize.lg, fontWeight: '700' },
});
