import { Grade, HomeworkProblem, Subject } from '../types';


export interface OCRProcessResult {
  success: boolean;
  problems: HomeworkProblem[];
  rawResponse?: any;
  error?: string;
}

export function stripQuestionPrefix(text: string): string {
  if (!text) return '';
  let cleaned = text.trim();
  const pattern = /^\s*(?:(?:[Qq]uestion|[Ee]xercise|[Ee]x|[Pp]roblem|[Qq]|លំហាត់ទី?|សំណួរ)\s*[\d១-៩]+[\.\)\:\-\s]*|\(?[\d១-៩]+[\.\)]\s*\(?[a-zA-Z]\)?\s*|\(?[\d១-៩]+\s*[a-zA-Z]?\)\s*|\(?[a-zA-Z]\)\s*|[\d១-៩]+\s*[\:\-]\s*(?=[a-zA-Z\u1780-\u17FF])|[\d១-៩]+\.\s+)\s*/i;
  let prev = '';
  while (prev !== cleaned) {
    prev = cleaned;
    cleaned = cleaned.replace(pattern, '').trim();
  }
  return cleaned || text.trim();
}

export function cleanOcrText(text: string): string {
  if (!text) return '';
  const withoutMd = text
    .replace(/\*\*/g, '')
    .replace(/__+/g, '')
    .replace(/^#+\s*/gm, '')
    .replace(/(\b\d+[\.\)]\s+)\1+/g, '$1')
    .trim();
  return stripQuestionPrefix(withoutMd);
}

// Extract full multi-part question text from all fields (title, prompt, instructions, elements, sub_questions)
function extractFullQuestionStatement(q: any, section?: any): string {
  const parts: string[] = [];

  const rawTitle = (q?.title || section?.title || '').trim();
  const title = stripQuestionPrefix(rawTitle);
  const rawPrompt = (q?.prompt || '').trim();
  const prompt = stripQuestionPrefix(rawPrompt);
  const instructions = (q?.instructions || section?.instructions || '').trim();

  // Extract from elements
  const elementTexts: string[] = [];
  const rawElements = q?.elements || section?.elements;
  if (Array.isArray(rawElements)) {
    for (const el of rawElements) {
      if (typeof el === 'string' && el.trim()) {
        elementTexts.push(el.trim());
      } else if (el?.text && typeof el.text === 'string' && el.text.trim()) {
        elementTexts.push(el.text.trim());
      }
    }
  }

  // Extract from sub_questions
  const subTexts: string[] = [];
  if (Array.isArray(q?.sub_questions)) {
    for (const sq of q.sub_questions) {
      const sqText = (sq?.prompt || sq?.text || sq?.instructions || '').trim();
      const sqNo = sq?.question_no ? `${sq.question_no}) ` : '';
      if (sqText) {
        subTexts.push(`${sqNo}${sqText}`);
      }
    }
  }

  // Assemble with clear hierarchy
  if (title) {
    parts.push(title);
  }

  if (prompt && prompt !== title) {
    parts.push(prompt);
  }

  if (instructions && instructions !== title && instructions !== prompt) {
    parts.push(instructions);
  }

  for (const et of elementTexts) {
    if (!parts.some(p => p.includes(et))) {
      parts.push(et);
    }
  }

  for (const st of subTexts) {
    if (!parts.some(p => p.includes(st))) {
      parts.push(st);
    }
  }

  const combined = parts.join('\n\n').trim();
  return combined || prompt || title || instructions || 'Worksheet Exercise';
}

/**
 * Parses raw JSON response from either Direct OCR (/process-homework)
 * or Backend Gateway (/api/upload/ocr or /api/upload/mock) into typed HomeworkProblem[].
 */
export function parseOCRResponse(data: any): OCRProcessResult {
  if (!data) {
    return {
      success: false,
      problems: [],
      error: 'Empty response received from OCR service.',
    };
  }

  const problems: HomeworkProblem[] = [];

  // Parse grade with support for Khmer numerals and text search
  let grade: Grade = 4;
  const KHMER_NUM_MAP: Record<string, number> = {
    '១': 1, '២': 2, '៣': 3, '៤': 4, '៥': 5, '៦': 6,
    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6
  };
  const rawTextBlob = JSON.stringify(data);
  const khmerGradeMatch = rawTextBlob.match(/ថ្នាក់ទី\s*([១-៦1-6])/);
  const engGradeMatch = rawTextBlob.match(/grade\s*([1-6])/i);

  if (khmerGradeMatch && khmerGradeMatch[1]) {
    grade = (KHMER_NUM_MAP[khmerGradeMatch[1]] || 4) as Grade;
  } else if (engGradeMatch && engGradeMatch[1]) {
    grade = parseInt(engGradeMatch[1], 10) as Grade;
  } else {
    const gradeStr = data.document?.grade_level || data.grade_level || '';
    const gradeMatch = gradeStr.match(/\d+/);
    if (gradeMatch) {
      const g = parseInt(gradeMatch[0], 10);
      if (g >= 1 && g <= 6) grade = g as Grade;
    }
  }

  // Parse subject
  let subject: Subject = 'math';
  const subStr = (data.document?.subject || data.detected_subject || data.subject || '').toLowerCase();
  if (subStr.includes('science') || subStr.includes('physic') || subStr.includes('bio') || subStr.includes('chem')) {
    subject = 'science';
  } else if (subStr.includes('eng') || subStr.includes('language') || subStr.includes('vocab')) {
    subject = 'english';
  }

  let problemCounter = 1;
  const pages = data.pages || [];

  // If pages are present (from direct OCR service), parse them
  if (pages.length > 0) {
    for (const page of pages) {
      // 1. Process Sections
      if (Array.isArray(page.sections) && page.sections.length > 0) {
        for (const sec of page.sections) {
          const secQuestions = Array.isArray(sec.questions) ? sec.questions : [];

          if (secQuestions.length > 0) {
            for (const q of secQuestions) {
              const fullStatement = extractFullQuestionStatement(q, sec);
              const qNo = q.question_no || sec.label || `Q${problemCounter}`;
              const cardTitle = q.title || sec.title || `Exercise ${qNo}`;

              problems.push({
                id: `ocr-p-${problemCounter}`,
                titleKhmer: `លំហាត់ ${qNo}: ${cardTitle}`,
                titleEng: `Problem ${qNo}: ${cardTitle}`,
                grade,
                subject,
                problemStatementKhmer: fullStatement,
                problemStatementEng: fullStatement,
                steps: [
                  {
                    id: `ocr-p-${problemCounter}-s1`,
                    stepNumber: 1,
                    totalSteps: 1,
                    questionKhmer: fullStatement,
                    questionEng: fullStatement,
                    inputFormat: 'text',
                    correctAnswer: '',
                    hint1: {
                      khmer: 'សូមអានសំណួរ និងការណែនាំដោយប្រុងប្រយ័ត្ន។',
                      eng: 'Read the instructions and numbers carefully.',
                    },
                    hint2: {
                      khmer: 'តើមានពាក្យគន្លឹះ ឬរូបមន្តអ្វីខ្លះនៅក្នុងសំណួរនេះ?',
                      eng: 'Look for keywords and calculations in the question.',
                    },
                    hint3: {
                      titleKhmer: 'ជំនួយពីទន្សាយ',
                      titleEng: 'Guidance from Tunsay',
                      exampleKhmer: 'សួរសំណួរទៅទន្សាយដើម្បីបំបែកលំហាត់ជាជំហានៗ!',
                      exampleEng: 'Ask Tunsay to break this problem down step-by-step!',
                    },
                    socraticPromptKhmer: `តោះយើងចាប់ផ្តើមដោះស្រាយ ${cardTitle} ទាំងអស់គ្នា!`,
                    socraticPromptEng: `Let's solve ${cardTitle} step by step!`,
                    explainDifferently: {
                      simpleKhmer: fullStatement,
                      simpleEng: fullStatement,
                      analogyTitle: 'ជំនួយការគិត',
                      analogyKhmer: 'តោះចាប់ផ្តើមដោះស្រាយជាមួយគ្នា។',
                      analogyEng: "Let's work through this step by step.",
                      analogyType: 'apples',
                    },
                  },
                ],
              });
              problemCounter++;
            }
          } else {
            // Section has no inner questions array — treat Section itself as a question card
            const secStatement = extractFullQuestionStatement(null, sec);
            const secNo = sec.label || `Q${problemCounter}`;
            const secTitle = sec.title || `Exercise ${secNo}`;

            problems.push({
              id: `ocr-p-${problemCounter}`,
              titleKhmer: `លំហាត់ ${secNo}: ${secTitle}`,
              titleEng: `Problem ${secNo}: ${secTitle}`,
              grade,
              subject,
              problemStatementKhmer: secStatement,
              problemStatementEng: secStatement,
              steps: [],
            });
            problemCounter++;
          }
        }
      }

      // 2. Process Top-Level page.questions
      if (Array.isArray(page.questions) && page.questions.length > 0) {
        for (const q of page.questions) {
          const fullStatement = extractFullQuestionStatement(q);
          const qNo = q.question_no || `Q${problemCounter}`;
          const title = q.title || `Exercise ${qNo}`;

          problems.push({
            id: `ocr-p-${problemCounter}`,
            titleKhmer: `លំហាត់ ${qNo}`,
            titleEng: title,
            grade,
            subject,
            problemStatementKhmer: fullStatement,
            problemStatementEng: fullStatement,
            steps: [],
          });
          problemCounter++;
        }
      }
    }
  } else if (Array.isArray(data.exercises) && data.exercises.length > 0) {
    // Structured exercises from Orchestrator Gateway (e.g. Q5, Q6, Q7)
    for (let exIdx = 0; exIdx < data.exercises.length; exIdx++) {
      const ex = data.exercises[exIdx];
      const rawStatement = ex.prompt || ex.scanned_text || ex.title || `Exercise ${problemCounter}`;
      const fullStatement = cleanOcrText(rawStatement);

      let cleanTitle = cleanOcrText(ex.title || '');
      const numStr = (ex.number || `Q${problemCounter}`).trim();
      const numDigits = numStr.replace(/[^\d]/g, '');
      const qPrefix = numDigits ? `Q${numDigits}` : numStr;

      if (numDigits) {
        cleanTitle = cleanTitle.replace(new RegExp(`^(?:Q?\\s*${numDigits}[\\.:\\s-]*)+`, 'i'), '').trim();
      }
      const titleEng = cleanTitle ? `${qPrefix}: ${cleanTitle}` : (ex.tab_label || `Exercise ${problemCounter}`);
      const titleKhmer = ex.tab_label_khmer ? `${ex.tab_label_khmer}${cleanTitle ? `: ${cleanTitle}` : ''}` : `លំហាត់ទី ${problemCounter}`;


      // Dynamic decomposition for any arbitrary exercise
      const steps: any[] = [];
      if (Array.isArray(ex.sub_questions) && ex.sub_questions.length > 0) {
        for (let sIdx = 0; sIdx < ex.sub_questions.length; sIdx++) {
          const sq = ex.sub_questions[sIdx];
          const sqPrompt = sq.prompt || `Part ${sq.question_no || sIdx + 1}`;
          const expectedAns = sq.expected_answer || sq.answer || '';
          steps.push({
            id: `${ex.exercise_id || `ocr-p-${problemCounter}`}-s${sIdx + 1}`,
            stepNumber: sIdx + 1,
            totalSteps: ex.sub_questions.length,
            questionKhmer: sqPrompt,
            questionEng: sqPrompt,
            inputFormat: sq.type === 'fill_blank' || sq.type === 'equation' ? 'number' : 'text',
            correctAnswer: expectedAns,
            hint1: {
              khmer: `សូមពិនិត្យមើលសំណួរទី ${sq.question_no || sIdx + 1}៖ ${sqPrompt}`,
              eng: sq.hint || `Look at part ${sq.question_no || sIdx + 1}: ${sqPrompt}`,
            },
            hint2: {
              khmer: 'តើមានពាក្យគន្លឹះ ឬលេខអ្វីខ្លះដែលត្រូវគណនា?',
              eng: 'Look at the numbers and operation.',
            },
            hint3: {
              titleKhmer: 'ជំនួយពីទន្សាយ',
              titleEng: 'Guidance from Tunsay',
              exampleKhmer: 'សួរសំណួរទៅទន្សាយដើម្បីបំបែកលំហាត់ជាជំហានៗ!',
              exampleEng: 'Ask Tunsay to break this problem down step-by-step!',
            },
            socraticPromptKhmer: `តោះដោះស្រាយ ${sqPrompt}!`,
            socraticPromptEng: `Let's solve ${sqPrompt}!`,
            explainDifferently: {
              simpleKhmer: sqPrompt,
              simpleEng: sqPrompt,
              analogyTitle: 'ជំនួយការគិត',
              analogyKhmer: 'តោះចាប់ផ្តើមដោះស្រាយជាមួយគ្នា។',
              analogyEng: "Let's work through this step by step.",
              analogyType: 'apples',
            },
          });
        }
      }

      problems.push({
        id: ex.exercise_id || `ocr-p-${problemCounter}`,
        titleKhmer,
        titleEng,
        grade,
        subject,
        problemStatementKhmer: fullStatement,
        problemStatementEng: fullStatement,
        steps,
      });
      problemCounter++;
    }
  }

  if (problems.length === 0) {
    const docTitle = data.document?.title || 'Scanned Worksheet';
    problems.push({
      id: `ocr-p-1`,
      titleKhmer: 'លំហាត់ស្កែនបាន',
      titleEng: docTitle,
      grade,
      subject,
      problemStatementKhmer: docTitle,
      problemStatementEng: docTitle,
      steps: [],
    });
  }

  return {
    success: true,
    problems,
    rawResponse: data,
  };
}

import { ocrApi } from '../api';

export async function processHomeworkImage(file: File): Promise<OCRProcessResult> {
  try {
    const data = await ocrApi.uploadAndExtract(file);
    if (!data || !data.success) {
      return {
        success: false,
        problems: [],
        error: data?.error || 'Worksheet scanner is temporarily unavailable. Please type your problem into the chat.',
      };
    }
    return parseOCRResponse(data);
  } catch (error: any) {
    console.error('OCR Processing failed:', error);
    return {
      success: false,
      problems: [],
      error: error?.message || 'Worksheet scanner is temporarily unavailable. Please type your problem into the chat.',
    };
  }
}

