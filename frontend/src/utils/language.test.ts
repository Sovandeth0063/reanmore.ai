import { describe, expect, it } from 'vitest';
import {
  answersMatch,
  isAnswerCorrect,
  normalizeWithKhmer,
} from './answerNormalization';
import { cleanBilingualOption, getDisplayName, t } from './language';

describe('normalizeWithKhmer', () => {
  it('maps Khmer digits to ASCII digits', () => {
    expect(normalizeWithKhmer('\u17e8')).toBe('8');
    expect(normalizeWithKhmer('\u17e1\u17e2')).toBe('12');
  });

  it('maps English number words to digits', () => {
    expect(normalizeWithKhmer('eight')).toBe('8');
  });
});

describe('answersMatch', () => {
  it('accepts exact and unit-suffixed numeric answers', () => {
    expect(answersMatch('8', '8')).toBe(true);
    expect(answersMatch('8 apples', '8')).toBe(true);
    expect(answersMatch('eight', '8')).toBe(true);
  });

  it('rejects wrong answers', () => {
    expect(answersMatch('9', '8')).toBe(false);
  });

  it('honours acceptable answer lists', () => {
    expect(isAnswerCorrect('7', '8', ['7'])).toBe(true);
    expect(isAnswerCorrect('8 apples', '8')).toBe(true);
  });
});

describe('language helpers', () => {
  it('returns the selected locale', () => {
    expect(t('en', 'KM', 'EN')).toBe('EN');
    expect(t('km', 'KM', 'EN')).toBe('KM');
  });

  it('strips bilingual options according to locale', () => {
    expect(cleanBilingualOption('Khmer (English)', 'en')).toBe('English');
    expect(cleanBilingualOption('Khmer (English)', 'km')).toBe('Khmer');
  });

  it('extracts display names according to locale', () => {
    expect(getDisplayName('Sochea (Sochea)', false)).toBe('Sochea');
  });
});
