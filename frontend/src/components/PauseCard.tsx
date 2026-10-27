import React from 'react';
import { Coffee, Sparkles, CheckCircle2, BookOpen, Home, Play } from 'lucide-react';

/**
 * PauseCard — Sprint 1.3 & Issue #11
 *
 * Full-screen pause/break overlay shown when:
 *   - Student's frustration score reaches ≥ 0.8 (backend signals take_a_break)
 *   - Student taps the Pause (⏸) button in the step widget header
 *   - Auto-triggered after N consecutive problems (configurable)
 *
 * The queue state is NOT cleared during pause. Tapping Resume restores
 * the exact step the student was on.
 *
 * Props:
 *   onResume      – Called when student taps "Resume"
 *   onExit        – Called when student taps "Exit to Home"
 *   problemTitle  – Title of the current problem (optional, shown for context)
 *   stepsLeft     – Number of steps remaining (optional)
 *   language      – 'km' | 'en'
 *   isFrustration – True if triggered by frustration detection (shows calming message)
 */
export interface PauseCardProps {
  onResume: () => void;
  onExit: () => void;
  problemTitle?: string;
  stepsLeft?: number;
  language?: 'km' | 'en';
  isFrustration?: boolean;
}

const LABELS = {
  en: {
    titleNormal: 'Taking a Break!',
    titleFrustration: 'It\'s OK to Pause!',
    normalMessage: 'Great work so far! Take a short break — stretch, drink some water, and come back fresh.',
    frustrationMessage: 'You\'ve been working really hard and trying your best! Everyone needs a moment to rest. Take a deep breath, get some water, and come back when you\'re ready.',
    stepsRemaining: 'steps remaining',
    progressSaved: 'Your progress is saved!',
    resume: 'Resume',
    exit: 'Exit to Home',
    encouragement: [
      'You\'re doing amazing!',
      'Every great learner takes breaks!',
      'Your brain is getting stronger!',
    ],
  },
  km: {
    titleNormal: 'ឈប់សំរាក!',
    titleFrustration: 'វាជារឿងធម្មតាទេ!',
    normalMessage: 'អ្នកបានធ្វើការបានល្អណាស់! ឈប់សំរាកបន្តិច — ស្ទ្រេចខ្លួន ផឹកទឹក ហើយត្រឡប់មកវិញថ្ងើមថ្ជើម។',
    frustrationMessage: 'អ្នកបានព្យាយាមយ៉ាងខ្លាំងណាស់! មនុស្សគ្រប់គ្នាត្រូវការពេលសំរាក។ ដកដង្ហើមជ្រៅ ផឹកទឹក ហើយត្រឡប់មកនៅពេលអ្នករួចរាល់។',
    stepsRemaining: 'ជំហានដែលនៅសល់',
    progressSaved: 'ដំណើរការរបស់អ្នកត្រូវបានរក្សាទុក!',
    resume: 'បន្ត',
    exit: 'ត្រឡប់ទៅផ្ទះ',
    encouragement: [
      'អ្នកធ្វើបានអស្ចារ្យណាស់!',
      'អ្នករៀនល្អតែងតែឈប់សំរាក!',
      'ខួរក្បាលអ្នកកំពុងខ្លាំងឡើង!',
    ],
  },
};

export const PauseCard: React.FC<PauseCardProps> = ({
  onResume,
  onExit,
  problemTitle,
  stepsLeft,
  language = 'km',
  isFrustration = false,
}) => {
  const l = LABELS[language];
  const encouragement = l.encouragement[Math.floor(Date.now() / 5000) % l.encouragement.length];

  return (
    <div style={styles.overlay}>
      <div style={styles.card}>

        {/* Animated icon */}
        <div style={styles.emojiPulse}>
          {isFrustration ? (
            <Sparkles style={{ width: 48, height: 48, color: '#F59E0B' }} />
          ) : (
            <Coffee style={{ width: 48, height: 48, color: '#D97706' }} />
          )}
        </div>

        {/* Title */}
        <h2 style={styles.title}>
          {isFrustration ? l.titleFrustration : l.titleNormal}
        </h2>

        {/* Message */}
        <p style={styles.message}>
          {isFrustration ? l.frustrationMessage : l.normalMessage}
        </p>

        {/* Encouragement badge */}
        <div style={styles.encouragementBadge}>
          {encouragement}
        </div>

        {/* Progress summary */}
        <div style={styles.progressRow}>
          <span style={styles.progressSaved}>
            <CheckCircle2 style={{ width: 14, height: 14, display: 'inline', marginRight: 4, verticalAlign: 'text-bottom' }} />
            {l.progressSaved}
          </span>
          {problemTitle && (
            <span style={styles.problemTitle} title={problemTitle}>
              <BookOpen style={{ width: 14, height: 14, display: 'inline', marginRight: 4, verticalAlign: 'text-bottom' }} />
              {problemTitle.length > 30 ? problemTitle.slice(0, 30) + '…' : problemTitle}
            </span>
          )}
          {typeof stepsLeft === 'number' && stepsLeft > 0 && (
            <span style={styles.stepsLeft}>
              {stepsLeft} {l.stepsRemaining}
            </span>
          )}
        </div>

        {/* Action buttons */}
        <div style={styles.actions}>
          <button
            id="pause-card-exit-btn"
            style={{ ...styles.btn, ...styles.exitBtn }}
            onClick={onExit}
          >
            <Home style={{ width: 16, height: 16, display: 'inline', marginRight: 6, verticalAlign: 'text-bottom' }} />
            {l.exit}
          </button>
          <button
            id="pause-card-resume-btn"
            style={{ ...styles.btn, ...styles.resumeBtn }}
            onClick={onResume}
          >
            <Play style={{ width: 16, height: 16, display: 'inline', marginRight: 6, verticalAlign: 'text-bottom' }} />
            {l.resume}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'linear-gradient(135deg, rgba(79,70,229,0.88), rgba(124,58,237,0.88))',
    backdropFilter: 'blur(12px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10000,
    padding: '24px',
  },
  card: {
    background: '#ffffff',
    borderRadius: '28px',
    padding: '40px 32px',
    maxWidth: '420px',
    width: '100%',
    boxShadow: '0 32px 96px rgba(0,0,0,0.32)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '20px',
    textAlign: 'center',
    animation: 'slideUpIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)',
  },
  emojiPulse: {
    fontSize: '64px',
    lineHeight: 1,
    animation: 'pulseSlow 2.5s ease-in-out infinite',
  },
  title: {
    margin: 0,
    fontSize: '26px',
    fontWeight: 800,
    color: '#1e1b4b',
    lineHeight: 1.2,
  },
  message: {
    margin: 0,
    fontSize: '15px',
    color: '#4b5563',
    lineHeight: 1.7,
    maxWidth: '360px',
  },
  encouragementBadge: {
    background: 'linear-gradient(135deg, #fef9c3, #fde68a)',
    border: '2px solid #f59e0b',
    borderRadius: '16px',
    padding: '10px 20px',
    fontSize: '15px',
    fontWeight: 700,
    color: '#92400e',
  },
  progressRow: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '6px',
    width: '100%',
  },
  progressSaved: {
    fontSize: '14px',
    color: '#16a34a',
    fontWeight: 600,
  },
  problemTitle: {
    fontSize: '13px',
    color: '#6b7280',
    fontStyle: 'italic',
  },
  stepsLeft: {
    fontSize: '13px',
    color: '#7c3aed',
    fontWeight: 600,
  },
  actions: {
    display: 'flex',
    gap: '12px',
    width: '100%',
    justifyContent: 'center',
    marginTop: '4px',
  },
  btn: {
    flex: 1,
    maxWidth: '180px',
    padding: '14px 20px',
    borderRadius: '16px',
    border: 'none',
    fontSize: '15px',
    fontWeight: 700,
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    fontFamily: 'inherit',
  },
  exitBtn: {
    background: '#f1f5f9',
    color: '#475569',
  },
  resumeBtn: {
    background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
    color: '#ffffff',
    boxShadow: '0 6px 20px rgba(124, 58, 237, 0.4)',
  },
};

export default PauseCard;
