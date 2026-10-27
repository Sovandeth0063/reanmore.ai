import { describe, it as test } from 'node:test';
import assert from 'node:assert/strict';
import { parseSocraticTurn } from '../schemas';

describe('Two-Stage Resilient Socratic Parser', () => {
  test('parses normal turn successfully', () => {
    const raw = {
      outcome: 'normal',
      textKhmer: 'តោះចាប់ផ្តើម',
      textEng: "Let's start",
      version: 1,
      crisisResource: null,
      suggestedChips: ['Hint please', 'I understand'],
      stepWidget: {
        step_number: 1,
        total_steps: 3,
        title: 'Step 1',
        prompt: 'What is 2 + 2?',
        input_type: 'number',
        hint_count: 0,
        unlocked_hints: [],
        is_final_step: false,
      },
      rewardsAwarded: { coins: 5, streakUpdated: true },
      isProblemComplete: false,
    };

    const parsed = parseSocraticTurn(raw);
    assert.notEqual(parsed, null);
    assert.equal(parsed?.outcome, 'normal');
    assert.equal(parsed?.textKhmer, 'តោះចាប់ផ្តើម');
    assert.equal(parsed?.stepWidget?.step_number, 1);
    assert.equal(parsed?.degraded, false);
    assert.equal(parsed?.needsCrisisFallback, false);
  });

  test('Tier 2 crisis response renders crisisResource even if presentation fields are broken', () => {
    const rawWithBrokenPresentation = {
      outcome: 'safety_tier2_escalated',
      textKhmer: 'សូមកុំបារម្ភ យើងនៅទីនេះដើម្បីជួយ',
      textEng: "Please don't worry, we are here to help",
      version: 2,
      crisisResource: {
        title: 'Child Helpline Cambodia',
        helplineKhmer: '1280',
        instructions: 'Call toll-free for free counseling',
      },
      // Broken presentation fields
      suggestedChips: 'INVALID_CHIPS_NOT_ARRAY',
      stepWidget: { invalid: true },
      rewardsAwarded: 'INVALID_REWARD',
    };

    const parsed = parseSocraticTurn(rawWithBrokenPresentation);
    assert.notEqual(parsed, null);
    assert.equal(parsed?.outcome, 'safety_tier2_escalated');
    assert.equal(parsed?.crisisResource?.helplineKhmer, '1280');
    assert.equal(parsed?.needsCrisisFallback, false);
    // Presentation fields degraded safely without throwing
    assert.deepEqual(parsed?.suggestedChips, []);
    assert.equal(parsed?.stepWidget, null);
    assert.equal(parsed?.rewardsAwarded, null);
    assert.equal(parsed?.degraded, true);
  });

  test('Tier 2 crisis response triggers needsCrisisFallback when crisisResource is missing', () => {
    const rawMissingHelpline = {
      outcome: 'safety_tier2_escalated',
      textKhmer: 'ជំនួយសុវត្ថិភាព',
      textEng: 'Safety help',
      crisisResource: null,
    };

    const parsed = parseSocraticTurn(rawMissingHelpline);
    assert.equal(parsed?.outcome, 'safety_tier2_escalated');
    assert.equal(parsed?.crisisResource, null);
    assert.equal(parsed?.needsCrisisFallback, true);
  });

  test('Unknown outcome degrades to normal with degraded: false and capped anomaly', () => {
    const rawUnknown = {
      outcome: 'future_experimental_outcome_type_xyz',
      textKhmer: 'សួស្តី',
      textEng: 'Hello',
    };

    const parsed = parseSocraticTurn(rawUnknown);
    assert.equal(parsed?.outcome, 'normal');
    assert.equal(parsed?.degraded, false);
    assert.ok(parsed?.issues.includes('outcome:unknown_value:future_experimental_outcome_type'));
  });

  test('stale_step outcome parses correctly with current_step', () => {
    const rawStale = {
      outcome: 'stale_step',
      textKhmer: 'ជំហាននេះបានកន្លងផុតហើយ',
      textEng: 'This step is already completed',
      current_step: 3,
    };

    const parsed = parseSocraticTurn(rawStale);
    assert.equal(parsed?.outcome, 'stale_step');
    assert.equal(parsed?.current_step, 3);
  });

  test('parses real backend snake_case response and multi-step container step_widget', () => {
    const backendPayload = {
      category: 'math_tutoring',
      solution: 'តោះចាប់ផ្តើមដោះស្រាយលំហាត់នេះទាំងអស់គ្នា!',
      formatted_markdown: '**Our Mission:** រកផលបូក 25 + 17',
      is_deflected: false,
      is_problem_complete: false,
      current_step_index: 0,
      suggested_chips: ['សុំតម្រុយ', 'ខ្ញុំយល់ហើយ'],
      step_widget: {
        total_steps: 3,
        current_step_index: 0,
        completed_steps: [],
        steps: [
          {
            step_number: 1,
            title: 'បូកខ្ទង់រាយ',
            status: 'in_progress',
            mission: 'បូក 5 + 7',
            clue: '5 + 7 = 12',
            helpful_example: '5 ផ្លែប៉ោម + 7 ផ្លែប៉ោម = 12 ផ្លែប៉ោម',
            your_turn: 'តើ 5 + 7 ស្មើនឹងប៉ុន្មាន?',
            student_answer: null,
            hints: ['គិតអំពីលេខ 12'],
            current_hint_level: 0,
          },
        ],
      },
    };

    const parsed = parseSocraticTurn(backendPayload);
    assert.notEqual(parsed, null);
    assert.equal(parsed?.outcome, 'normal');
    assert.equal(parsed?.textKhmer, 'តោះចាប់ផ្តើមដោះស្រាយលំហាត់នេះទាំងអស់គ្នា!');
    assert.equal(parsed?.current_step, 1);
    assert.equal(parsed?.isProblemComplete, false);
    assert.equal(parsed?.suggestedChips.length, 2);
    assert.notEqual(parsed?.stepWidget, null);
    // Verified container parsed properly with steps array
    assert.equal(parsed?.stepWidget?.total_steps, 3);
    assert.ok(Array.isArray((parsed?.stepWidget as any)?.steps));
    assert.equal((parsed?.stepWidget as any)?.steps[0]?.step_number, 1);
    assert.equal(parsed?.degraded, false);
  });

  test('maps deflected backend response to safety_tier1_deflected', () => {
    const deflectedPayload = {
      category: 'guardrail_violation',
      solution: 'ខ្ញុំមិនអាចឆ្លើយសំណួរនេះបានទេ តោះរៀនមេរៀនវិទ្យាសាស្ត្រវិញ!',
      is_deflected: true,
      suggested_chips: [],
    };

    const parsed = parseSocraticTurn(deflectedPayload);
    assert.notEqual(parsed, null);
    assert.equal(parsed?.outcome, 'safety_tier1_deflected');
    assert.equal(parsed?.textKhmer, 'ខ្ញុំមិនអាចឆ្លើយសំណួរនេះបានទេ តោះរៀនមេរៀនវិទ្យាសាស្ត្រវិញ!');
  });

  test('parses step answer response payload with is_correct and container widget', () => {
    const stepAnswerPayload = {
      session_id: 'sess-123',
      step_number: 1,
      student_answer: '12',
      is_correct: true,
      is_problem_complete: false,
      step_widget: {
        total_steps: 3,
        current_step_index: 1,
        completed_steps: [0],
        steps: [
          {
            step_number: 1,
            title: 'Step 1',
            status: 'completed',
          },
        ],
      },
    };

    const parsed = parseSocraticTurn(stepAnswerPayload);
    assert.notEqual(parsed, null);
    assert.equal(parsed?.outcome, 'normal');
    assert.equal(parsed?.current_step, 1);
    assert.equal(parsed?.isProblemComplete, false);
    assert.notEqual(parsed?.stepWidget, null);
  });
});

