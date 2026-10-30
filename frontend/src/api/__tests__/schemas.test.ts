import { describe, it as test, expect } from 'vitest';
import { parseSocraticTurn } from '../schemas';

describe('Two-Stage Resilient Socratic Parser', () => {
  test('parses normal turn successfully', () => {
    const raw = {
      outcome: 'normal',
      textKhmer: 'ážáŸ„áŸ‡áž…áž¶áž”áŸ‹áž•áŸ’ážáž¾áž˜',
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
    expect(parsed).not.toBe(null);
    expect(parsed?.outcome).toBe('normal');
    expect(parsed?.textKhmer).toBe('ážáŸ„áŸ‡áž…áž¶áž”áŸ‹áž•áŸ’ážáž¾áž˜');
    expect(parsed?.stepWidget?.step_number).toBe(1);
    expect(parsed?.degraded).toBe(false);
    expect(parsed?.needsCrisisFallback).toBe(false);
  });

  test('Tier 2 crisis response renders crisisResource even if presentation fields are broken', () => {
    const rawWithBrokenPresentation = {
      outcome: 'safety_tier2_escalated',
      textKhmer: 'ážŸáž¼áž˜áž€áž»áŸ†áž”áž¶ážšáž˜áŸ’áž— áž™áž¾áž„áž“áŸ…áž‘áž¸áž“áŸáŸ‡ážŠáž¾áž˜áŸ’áž”áž¸áž‡áž½áž™',
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
    expect(parsed).not.toBe(null);
    expect(parsed?.outcome).toBe('safety_tier2_escalated');
    expect(parsed?.crisisResource?.helplineKhmer).toBe('1280');
    expect(parsed?.needsCrisisFallback).toBe(false);
    // Presentation fields degraded safely without throwing
    expect(parsed?.suggestedChips).toEqual([]);
    expect(parsed?.stepWidget).toBe(null);
    expect(parsed?.rewardsAwarded).toBe(null);
    expect(parsed?.degraded).toBe(true);
  });

  test('Tier 2 crisis response triggers needsCrisisFallback when crisisResource is missing', () => {
    const rawMissingHelpline = {
      outcome: 'safety_tier2_escalated',
      textKhmer: 'áž‡áŸ†áž“áž½áž™ážŸáž»ážœážáŸ’ážáž·áž—áž¶áž–',
      textEng: 'Safety help',
      crisisResource: null,
    };

    const parsed = parseSocraticTurn(rawMissingHelpline);
    expect(parsed?.outcome).toBe('safety_tier2_escalated');
    expect(parsed?.crisisResource).toBe(null);
    expect(parsed?.needsCrisisFallback).toBe(true);
  });

  test('Unknown outcome degrades to normal with degraded: false and capped anomaly', () => {
    const rawUnknown = {
      outcome: 'future_experimental_outcome_type_xyz',
      textKhmer: 'ážŸáž½ážŸáŸ’ážáž¸',
      textEng: 'Hello',
    };

    const parsed = parseSocraticTurn(rawUnknown);
    expect(parsed?.outcome).toBe('normal');
    expect(parsed?.degraded).toBe(false);
    expect(parsed?.issues.includes('outcome:unknown_value:future_experimental_outcome_type')).toBeTruthy();
  });

  test('stale_step outcome parses correctly with current_step', () => {
    const rawStale = {
      outcome: 'stale_step',
      textKhmer: 'áž‡áŸ†áž áž¶áž“áž“áŸáŸ‡áž”áž¶áž“áž€áž“áŸ’áž›áž„áž•áž»ážáž áž¾áž™',
      textEng: 'This step is already completed',
      current_step: 3,
    };

    const parsed = parseSocraticTurn(rawStale);
    expect(parsed?.outcome).toBe('stale_step');
    expect(parsed?.current_step).toBe(3);
  });

  test('parses real backend snake_case response and multi-step container step_widget', () => {
    const backendPayload = {
      category: 'math_tutoring',
      solution: 'ážáŸ„áŸ‡áž…áž¶áž”áŸ‹áž•áŸ’ážáž¾áž˜ážŠáŸ„áŸ‡ážŸáŸ’ážšáž¶áž™áž›áŸ†áž áž¶ážáŸ‹áž“áŸáŸ‡áž‘áž¶áŸ†áž„áž¢ážŸáŸ‹áž‚áŸ’áž“áž¶!',
      formatted_markdown: '**Our Mission:** ážšáž€áž•áž›áž”áž¼áž€ 25 + 17',
      is_deflected: false,
      is_problem_complete: false,
      current_step_index: 0,
      suggested_chips: ['ážŸáž»áŸ†ážáž˜áŸ’ážšáž»áž™', 'ážáŸ’áž‰áž»áŸ†áž™áž›áŸ‹áž áž¾áž™'],
      step_widget: {
        total_steps: 3,
        current_step_index: 0,
        completed_steps: [],
        steps: [
          {
            step_number: 1,
            title: 'áž”áž¼áž€ážáŸ’áž‘áž„áŸ‹ážšáž¶áž™',
            status: 'in_progress',
            mission: 'áž”áž¼áž€ 5 + 7',
            clue: '5 + 7 = 12',
            helpful_example: '5 áž•áŸ’áž›áŸ‚áž”áŸ‰áŸ„áž˜ + 7 áž•áŸ’áž›áŸ‚áž”áŸ‰áŸ„áž˜ = 12 áž•áŸ’áž›áŸ‚áž”áŸ‰áŸ„áž˜',
            your_turn: 'ážáž¾ 5 + 7 ážŸáŸ’áž˜áž¾áž“áž¹áž„áž”áŸ‰áž»áž“áŸ’áž˜áž¶áž“?',
            student_answer: null,
            hints: ['áž‚áž·ážáž¢áŸ†áž–áž¸áž›áŸáž 12'],
            current_hint_level: 0,
          },
        ],
      },
    };

    const parsed = parseSocraticTurn(backendPayload);
    expect(parsed).not.toBe(null);
    expect(parsed?.outcome).toBe('normal');
    expect(parsed?.textKhmer).toBe('ážáŸ„áŸ‡áž…áž¶áž”áŸ‹áž•áŸ’ážáž¾áž˜ážŠáŸ„áŸ‡ážŸáŸ’ážšáž¶áž™áž›áŸ†áž áž¶ážáŸ‹áž“áŸáŸ‡áž‘áž¶áŸ†áž„áž¢ážŸáŸ‹áž‚áŸ’áž“áž¶!');
    expect(parsed?.current_step).toBe(1);
    expect(parsed?.isProblemComplete).toBe(false);
    expect(parsed?.suggestedChips.length).toBe(2);
    expect(parsed?.stepWidget).not.toBe(null);
    // Verified container parsed properly with steps array
    expect(parsed?.stepWidget?.total_steps).toBe(3);
    expect(Array.isArray((parsed?.stepWidget as any)?.steps)).toBeTruthy();
    expect((parsed?.stepWidget as any)?.steps[0]?.step_number).toBe(1);
    expect(parsed?.degraded).toBe(false);
  });

  test('maps deflected backend response to safety_tier1_deflected', () => {
    const deflectedPayload = {
      category: 'guardrail_violation',
      solution: 'ážáŸ’áž‰áž»áŸ†áž˜áž·áž“áž¢áž¶áž…áž†áŸ’áž›áž¾áž™ážŸáŸ†ážŽáž½ážšáž“áŸáŸ‡áž”áž¶áž“áž‘áŸ ážáŸ„áŸ‡ážšáŸ€áž“áž˜áŸážšáŸ€áž“ážœáž·áž‘áŸ’áž™áž¶ážŸáž¶ážŸáŸ’ážáŸ’ážšážœáž·áž‰!',
      is_deflected: true,
      suggested_chips: [],
    };

    const parsed = parseSocraticTurn(deflectedPayload);
    expect(parsed).not.toBe(null);
    expect(parsed?.outcome).toBe('safety_tier1_deflected');
    expect(parsed?.textKhmer).toBe('ážáŸ’áž‰áž»áŸ†áž˜áž·áž“áž¢áž¶áž…áž†áŸ’áž›áž¾áž™ážŸáŸ†ážŽáž½ážšáž“áŸáŸ‡áž”áž¶áž“áž‘áŸ ážáŸ„áŸ‡ážšáŸ€áž“áž˜áŸážšáŸ€áž“ážœáž·áž‘áŸ’áž™áž¶ážŸáž¶ážŸáŸ’ážáŸ’ážšážœáž·áž‰!');
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
    expect(parsed).not.toBe(null);
    expect(parsed?.outcome).toBe('normal');
    expect(parsed?.current_step).toBe(1);
    expect(parsed?.isProblemComplete).toBe(false);
    expect(parsed?.stepWidget).not.toBe(null);
  });
});

