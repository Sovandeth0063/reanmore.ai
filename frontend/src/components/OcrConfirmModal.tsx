import React, { useState, useCallback } from 'react';

/**
 * OcrConfirmModal — Sprint 1.1: OCR Quality Gate
 *
 * Shows extracted text after a scan with a confidence badge.
 * The student (or helper adult) can:
 *   - Confirm the text looks right ("Looks Good ✅")
 *   - Edit the text inline before confirming
 *   - Retake the photo if the scan looks wrong
 *
 * Low confidence scans (< 0.70) show a cautionary badge and an automatic
 * suggestion to retake. High confidence scans default to "Looks Good".
 *
 * Props:
 *   extractedText   – Raw text from OCR
 *   confidence      – 0.0 to 1.0 confidence score
 *   segments        – Optional list of problem strings when multi-problem detected
 *   onConfirm       – Called with (finalText: string, selectedSegments: string[])
 *   onRetake        – Called when the student taps "Retake Photo"
 *   onClose         – Called on backdrop click or close button
 *   language        – 'km' | 'en' for UI labels
 */
export interface OcrConfirmModalProps {
  extractedText: string;
  confidence: number;
  segments?: string[];
  onConfirm: (finalText: string, selectedSegments: string[]) => void;
  onRetake: () => void;
  onClose: () => void;
  language?: 'km' | 'en';
}

const LABELS = {
  en: {
    title: 'Check Your Scanned Homework',
    subtitle: 'Please review the scanned text below. You can edit it if anything is inaccurate.',
    confidence: 'Scan Clarity',
    high: 'Clear Scan ✅',
    medium: 'Moderate Clarity 🟡',
    low: 'Needs Review ⚠️',
    lowHint: 'The scan clarity is low. Some characters might be misread — please double-check or retake a clearer photo.',
    multiTitle: 'Multiple exercises detected! Choose which ones to practice:',
    editLabel: 'Edit the scanned exercise text:',
    retake: '📷 Retake Photo',
    confirm: 'Looks Good, Let\'s Start! ✅',
    selectAll: 'Select All',
    deselectAll: 'Deselect All',
  },
  km: {
    title: 'ផ្ទៀងផ្ទាត់អត្ថបទដែលបានស្កែន',
    subtitle: 'សូមពិនិត្យអត្ថបទខាងក្រោម។ អ្នកអាចចុចកែសម្រួល ប្រសិនបើមានអក្សរណាខុស។',
    confidence: 'កម្រិតភាពច្បាស់',
    high: 'ច្បាស់ល្អ ✅',
    medium: 'មធ្យម 🟡',
    low: 'មិនសូវច្បាស់ ⚠️',
    lowHint: 'រូបភាពមិនសូវច្បាស់ទេ។ អក្សរមួយចំនួនអាចមិនត្រឹមត្រូវ — សូមពិនិត្យ ឬថតរូបម្តងទៀត។',
    multiTitle: 'រកឃើញលំហាត់ជាច្រើន! សូមជ្រើសរើសលំហាត់ដែលចង់អនុវត្ត៖',
    editLabel: 'កែសម្រួលអត្ថបទលំហាត់ដែលស្កែនបាន៖',
    retake: '📷 ថតរូបឡើងវិញ',
    confirm: 'ត្រឹមត្រូវហើយ តោះចាប់ផ្តើម! ✅',
    selectAll: 'ជ្រើសរើសទាំងអស់',
    deselectAll: 'ដកការជ្រើសរើស',
  },
};

function getConfidenceLabel(confidence: number, lang: 'km' | 'en') {
  const l = LABELS[lang];
  if (confidence >= 0.80) return { label: l.high, color: '#1B4332', bg: '#D8F3DC', border: '#40916C' };
  if (confidence >= 0.60) return { label: l.medium, color: '#854D0E', bg: '#FEF9C3', border: '#EAB308' };
  return { label: l.low, color: '#991B1B', bg: '#FEE2E2', border: '#EF4444' };
}

export const OcrConfirmModal: React.FC<OcrConfirmModalProps> = ({
  extractedText,
  confidence,
  segments,
  onConfirm,
  onRetake,
  onClose,
  language = 'km',
}) => {
  const l = LABELS[language];
  const [editedText, setEditedText] = useState(extractedText);
  const [selectedSegments, setSelectedSegments] = useState<Set<number>>(
    new Set(segments?.map((_, i) => i) ?? [])
  );

  const { label: confLabel, color: confColor, bg: confBg, border: confBorder } = getConfidenceLabel(confidence, language);
  const isMulti = segments && segments.length > 1;
  const isLowConfidence = confidence < 0.60;

  const handleConfirm = useCallback(() => {
    const segs = isMulti
      ? segments!.filter((_, i) => selectedSegments.has(i))
      : [];
    onConfirm(editedText.trim() || extractedText, segs);
  }, [editedText, extractedText, isMulti, segments, selectedSegments, onConfirm]);

  const toggleSegment = (i: number) => {
    setSelectedSegments(prev => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i); else next.add(i);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedSegments.size === segments!.length) {
      setSelectedSegments(new Set());
    } else {
      setSelectedSegments(new Set(segments!.map((_, i) => i)));
    }
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={styles.header}>
          <div style={styles.scanIcon}>🔍</div>
          <div>
            <h2 style={styles.title}>{l.title}</h2>
            <p style={styles.subtitle}>{l.subtitle}</p>
          </div>
          <button style={styles.closeBtn} onClick={onClose} aria-label="Close">✕</button>
        </div>

        {/* Confidence badge */}
        <div style={{ ...styles.confidenceBadge, background: confBg, borderColor: confBorder }}>
          <span style={{ color: confColor, fontWeight: 800 }}>{l.confidence}:</span>
          <span style={{ color: confColor, marginLeft: 6 }}>{confLabel}</span>
          <span style={{ ...styles.confPercent, color: confColor }}>
            {Math.round(confidence * 100)}%
          </span>
        </div>

        {/* Low confidence warning */}
        {isLowConfidence && (
          <div style={styles.lowConfWarning}>
            ⚠️ {l.lowHint}
          </div>
        )}

        {/* Multi-problem selector */}
        {isMulti ? (
          <div style={styles.segmentSection}>
            <div style={styles.segmentHeaderRow}>
              <span style={styles.sectionLabel}>{l.multiTitle}</span>
              <button type="button" style={styles.toggleAllBtn} onClick={toggleAll}>
                {selectedSegments.size === segments!.length ? l.deselectAll : l.selectAll}
              </button>
            </div>
            <div style={styles.segmentList}>
              {segments!.map((seg, i) => (
                <label key={i} style={{
                  ...styles.segmentItem,
                  background: selectedSegments.has(i) ? '#E8F5E9' : '#FFFFFF',
                  borderColor: selectedSegments.has(i) ? '#2D6A4F' : '#D1D5DB',
                }}>
                  <input
                    type="checkbox"
                    checked={selectedSegments.has(i)}
                    onChange={() => toggleSegment(i)}
                    style={styles.segmentCheckbox}
                  />
                  <span style={styles.segmentText}>{seg}</span>
                </label>
              ))}
            </div>
          </div>
        ) : (
          /* Single problem text editor */
          <div style={styles.editSection}>
            <label style={styles.sectionLabel}>{l.editLabel}</label>
            <textarea
              style={styles.textarea}
              value={editedText}
              onChange={e => setEditedText(e.target.value)}
              rows={5}
              spellCheck={false}
            />
          </div>
        )}

        {/* Action buttons */}
        <div style={styles.actions}>
          <button
            type="button"
            style={{ ...styles.btn, ...styles.retakeBtn }}
            onClick={onRetake}
          >
            {l.retake}
          </button>
          <button
            type="button"
            style={{
              ...styles.btn,
              ...styles.confirmBtn,
              opacity: (isMulti && selectedSegments.size === 0) ? 0.5 : 1,
              cursor: (isMulti && selectedSegments.size === 0) ? 'not-allowed' : 'pointer',
            }}
            onClick={handleConfirm}
            disabled={isMulti && selectedSegments.size === 0}
          >
            {l.confirm}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Styles — Forest Theme Consistent
// ─────────────────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(27, 67, 50, 0.65)',
    backdropFilter: 'blur(5px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
    padding: '16px',
  },
  modal: {
    background: '#ffffff',
    borderRadius: '24px',
    padding: '24px',
    maxWidth: '540px',
    width: '100%',
    maxHeight: '90vh',
    overflowY: 'auto',
    border: '3px solid #1B4332',
    boxShadow: '6px 6px 0px #1B4332',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  header: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
  },
  scanIcon: {
    fontSize: '32px',
    lineHeight: 1,
  },
  title: {
    margin: 0,
    fontSize: '18px',
    fontWeight: 900,
    color: '#1B4332',
    lineHeight: 1.3,
  },
  subtitle: {
    margin: '4px 0 0',
    fontSize: '13px',
    fontWeight: 600,
    color: '#52796F',
    lineHeight: 1.4,
  },
  closeBtn: {
    marginLeft: 'auto',
    background: '#E8F5E9',
    border: '2px solid #1B4332',
    fontSize: '14px',
    fontWeight: 900,
    cursor: 'pointer',
    color: '#1B4332',
    padding: '4px 8px',
    borderRadius: '8px',
    lineHeight: 1,
  },
  confidenceBadge: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 14px',
    borderRadius: '14px',
    border: '2px solid',
    fontSize: '13px',
    fontWeight: 700,
    gap: '4px',
  },
  confPercent: {
    marginLeft: 'auto',
    fontSize: '13px',
    fontWeight: 900,
  },
  lowConfWarning: {
    background: '#FFFBEB',
    border: '2px solid #F59E0B',
    borderRadius: '14px',
    padding: '10px 14px',
    fontSize: '13px',
    fontWeight: 600,
    color: '#92400E',
    lineHeight: 1.5,
  },
  sectionLabel: {
    fontWeight: 800,
    fontSize: '13px',
    color: '#1B4332',
    display: 'block',
  },
  segmentSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  segmentHeaderRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  toggleAllBtn: {
    background: '#E8F5E9',
    border: '1.5px solid #2D6A4F',
    borderRadius: '8px',
    padding: '3px 10px',
    color: '#1B4332',
    fontSize: '12px',
    fontWeight: 800,
    cursor: 'pointer',
  },
  segmentList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    maxHeight: '220px',
    overflowY: 'auto',
  },
  segmentItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px',
    padding: '10px 12px',
    borderRadius: '12px',
    border: '2px solid',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  segmentCheckbox: {
    marginTop: '2px',
    width: '16px',
    height: '16px',
    accentColor: '#2D6A4F',
    flexShrink: 0,
  },
  segmentText: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#1B4332',
    lineHeight: 1.5,
  },
  editSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  textarea: {
    width: '100%',
    border: '2px solid #1B4332',
    borderRadius: '14px',
    padding: '12px',
    fontSize: '14px',
    fontFamily: 'inherit',
    color: '#1B4332',
    background: '#F8FAF9',
    resize: 'vertical',
    outline: 'none',
    boxSizing: 'border-box',
    lineHeight: 1.6,
  },
  actions: {
    display: 'flex',
    gap: '10px',
    justifyContent: 'flex-end',
    paddingTop: '6px',
  },
  btn: {
    padding: '10px 20px',
    borderRadius: '14px',
    border: '2px solid #1B4332',
    fontSize: '14px',
    fontWeight: 800,
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    fontFamily: 'inherit',
    boxShadow: '2px 2px 0px #1B4332',
  },
  retakeBtn: {
    background: '#FFFFFF',
    color: '#1B4332',
  },
  confirmBtn: {
    background: '#2D6A4F',
    color: '#FFFFFF',
  },
};

export default OcrConfirmModal;
