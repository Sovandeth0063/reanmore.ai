/**
 * Hardcoded Socratic Tutor Question Bank — WEG Primary Curriculum
 * 10 Math + 10 Science questions with 4-level hint ladders
 */

export type Subject = 'math' | 'science';
export type HintLevel = 0 | 1 | 2 | 3;

export interface Hint {
  level: HintLevel;
  eng: string;
  khmer: string;
}

export interface ExpectedResponse {
  pattern: string; // regex pattern to match student answer
  isCorrect: boolean;
  feedbackEng: string;
  feedbackKhmer: string;
  nextAction: 'next_step' | 'retry' | 'ask_why';
}

export interface TutorQuestion {
  id: string;
  subject: Subject;
  section: string;
  qNumber: string;
  grade: number;
  questionEng: string;
  questionKhmer: string;
  learningGoalEng: string;
  learningGoalKhmer: string;
  correctAnswer: string;
  acceptablePatterns: string[]; // regex patterns that count as correct
  hints: Hint[];
  whyFollowUpEng: string;
  whyFollowUpKhmer: string;
  expectedResponses: ExpectedResponse[];
}

// ═══════════════════════════════════════════════════════
//  SECTION 1 — MATHEMATICS
// ═══════════════════════════════════════════════════════

const MATH_Q1: TutorQuestion = {
  id: 'math-q1',
  subject: 'math',
  section: 'Addition & Number Bonds',
  qNumber: 'Q1a',
  grade: 2,
  questionEng: 'Solve: 9 + 2 + 3 + 1',
  questionKhmer: 'ដោះស្រាយ៖ ៩ + ២ + ៣ + ១',
  learningGoalEng: 'Addition and breaking numbers into easier groups.',
  learningGoalKhmer: 'ការបូក និងការបំបែកលេខជាក្រុមងាយស្រួល។',
  correctAnswer: '15',
  acceptablePatterns: ['15', 'fifteen'],
  hints: [
    {
      level: 0,
      eng: "Let's make this easier by grouping numbers that are easy to add. Which two numbers could you add together first?",
      khmer: "តោះធ្វើឱ្យងាយស្រួលដោយចងក្រុមលេខដែលងាយបូក។ តើលេខណាពីរអាចបូកគ្នាជាមុនសិន?",
    },
    {
      level: 1,
      eng: "Try adding the first two numbers first. Then add the third number, and finally the last number.",
      khmer: "សូមព្យាយាមបូកលេខពីរដំបូងជាមុនសិន។ បន្ទាប់មកបូកលេខទីបី ហើយចុងក្រោយលេខចុងក្រោយ។",
    },
    {
      level: 2,
      eng: "Start with 9 + 2. What does that give you? Now add 3. Then add 1.",
      khmer: "ចាប់ផ្តើមដោយ ៩ + ២។ តើវាទៅជាអ្វី? ឥឡូវបូក ៣។ បន្ទាប់មកបូក ១។",
    },
    {
      level: 3,
      eng: "9 + 2 = 11. Then 11 + 3 = 14. Finally 14 + 1 = ?",
      khmer: "៩ + ២ = ១១។ បន្ទាប់មក ១១ + ៣ = ១៤។ ចុងក្រោយ ១៤ + ១ = ?",
    },
  ],
  whyFollowUpEng: "Good! Can you explain why grouping numbers makes addition easier?",
  whyFollowUpKhmer: "ល្អ! តើអ្នកអាចពន្យល់បានទេថាហេតុអ្វីការចងក្រុមលេខធ្វើឱ្យការបូកងាយស្រួល?",
  expectedResponses: [
    {
      pattern: '15|fifteen',
      isCorrect: true,
      feedbackEng: "Excellent! 9 + 2 + 3 + 1 = 15. You did it step by step!",
      feedbackKhmer: "អស្ចារ្យ! ៩ + ២ + ៣ + ១ = ១៥។ អ្នកធ្វើវាជាជំហានៗ!",
      nextAction: 'ask_why',
    },
    {
      pattern: '14|16',
      isCorrect: false,
      feedbackEng: "Close! Double-check your last step. Count again carefully.",
      feedbackKhmer: "មិនឆ្ងាយទេ! ពិនិត្យជំហានចុងក្រោយឡើងវិញ។ រាប់ម្តងទៀតដោយប្រុងប្រយ័ត្ន។",
      nextAction: 'retry',
    },
  ],
};

const MATH_Q2: TutorQuestion = {
  id: 'math-q2',
  subject: 'math',
  section: 'Number Patterns & Bridging',
  qNumber: 'Q2',
  grade: 2,
  questionEng: 'Solve: 54 + 7 (Use the known fact: 4 + 7 = 11)',
  questionKhmer: 'ដោះស្រាយ៖ ៥៤ + ៧ (ប្រើចំណេះដឹង៖ ៤ + ៧ = ១១)',
  learningGoalEng: 'Using known facts to bridge across tens.',
  learningGoalKhmer: 'ប្រើចំណេះដឹងដែលមានស្រាប់ដើម្បីឆ្លងតរភាគបញ្ជរ។',
  correctAnswer: '61',
  acceptablePatterns: ['61', 'sixty-one', 'sixty one'],
  hints: [
    {
      level: 0,
      eng: "Look at the ones digit in 54. Which part of the known fact 4 + 7 = 11 can help you?",
      khmer: "មើលខ្ទង់ខ្ទង់នៅក្នុង ៥៤។ ផ្នែកណានៃចំណេះដឹង ៤ + ៧ = ១១ អាចជួយអ្នក?",
    },
    {
      level: 1,
      eng: "Break 54 into 50 + 4. Can you first use 4 + 7?",
      khmer: "បំបែក ៥៤ ជា ៥០ + ៤។ តើអ្នកអាចប្រើ ៤ + ៧ ជាមុនសិនទេ?",
    },
    {
      level: 2,
      eng: "4 + 7 = 11. So you have 50 and 11. Put them together.",
      khmer: "៤ + ៧ = ១១។ ដូច្នេះអ្នកមាន ៥០ និង ១១។ បូកវាជាមួយគ្នា។",
    },
    {
      level: 3,
      eng: "54 + 7 = 50 + 4 + 7 = 50 + 11 = 61.",
      khmer: "៥៤ + ៧ = ៥០ + ៤ + ៧ = ៥០ + ១១ = ៦១។",
    },
  ],
  whyFollowUpEng: "Great! Why does breaking 54 into 50 + 4 make this easier?",
  whyFollowUpKhmer: "ល្អ! ហេតុអ្វីបានជាការបំបែក ៥៤ ជា ៥០ + ៤ ធ្វើឱ្យងាយស្រួល?",
  expectedResponses: [
    {
      pattern: '61|sixty[- ]?one',
      isCorrect: true,
      feedbackEng: "Perfect! 54 + 7 = 61. You used the known fact 4 + 7 = 11 brilliantly!",
      feedbackKhmer: "ល្អឥតខ្ចោះ! ៥៤ + ៧ = ៦១។ អ្នកប្រើចំណេះដឹង ៤ + ៧ = ១១ បានយ៉ាងឆ្លាតវៃ!",
      nextAction: 'ask_why',
    },
  ],
};

const MATH_Q3: TutorQuestion = {
  id: 'math-q3',
  subject: 'math',
  section: 'Place Value & Expanded Form',
  qNumber: 'Q3',
  grade: 2,
  questionEng: 'What is 805 in expanded form? (Hundreds, tens, ones)',
  questionKhmer: 'តើ ៨០៥ មានទម្រង់ពង្រីកយ៉ាងណា? (រយ និចសិប ខ្ទង់)',
  learningGoalEng: 'Understanding hundreds, tens, and ones place values.',
  learningGoalKhmer: 'យល់ពីតម្លៃទីតាំងរយ និចសិប និងខ្ទង់។',
  correctAnswer: '800 + 0 + 5',
  acceptablePatterns: ['800\\s*\\+\\s*0\\s*\\+\\s*5', '8 hundreds', 'eight hundred'],
  hints: [
    {
      level: 0,
      eng: "What digit is in the hundreds place? What about the tens place? What about the ones place?",
      khmer: "តើខ្ទង់ណាស្ថិតនៅទីតាំងរយ? តើទីតាំងនិចសិបវិញ? ហើយទីតាំងខ្ទង់វិញ?",
    },
    {
      level: 1,
      eng: "In 805, the first digit is 8, the middle is 0, and the last is 5. What does each represent?",
      khmer: "ក្នុង ៨០៥ ខ្ទង់ទី១ គឺ ៨ ខ្ទង់កណ្តាលគឺ ០ និងខ្ទង់ចុងក្រោយគឺ ៥។ តើនីមួយៗតំណាងឱ្យអ្វី?",
    },
    {
      level: 2,
      eng: "Does the 0 represent any tens? How would you write each place-value part separately?",
      khmer: "តើ ០ តំណាងឱ្យនិចសិបទេ? តើអ្នកនឹងសរសេរផ្នែកតម្លៃទីតាំងនីមួយៗដោយឡើចារណ៍ដោយរបៀបណា?",
    },
    {
      level: 3,
      eng: "805 = 800 + 0 + 5. Eight hundreds, zero tens, and five ones.",
      khmer: "៨០៥ = ៨០០ + ០ + ៥។ ប្រាំបីរយ សូន្យនិចសិប និងប្រាំខ្ទង់។",
    },
  ],
  whyFollowUpEng: "Good! Why do we write the 0 even though it means zero tens?",
  whyFollowUpKhmer: "ល្អ! ហេតុអ្វីយើងសរសេរ ០ ទោះបីវាមានន័យថាសូន្យនិចសិប?",
  expectedResponses: [
    {
      pattern: '800\\s*\\+\\s*0\\s*\\+\\s*5|8\\s*hundreds.*0\\s*tens.*5\\s*ones|eight\\s*hundred',
      isCorrect: true,
      feedbackEng: "Excellent! 805 = 800 + 0 + 5. The 0 holds the tens place!",
      feedbackKhmer: "អស្ចារ្យ! ៨០៥ = ៨០០ + ០ + ៥។ ០ កាន់ទីតាំងនិចសិប!",
      nextAction: 'ask_why',
    },
  ],
};

const MATH_Q4A: TutorQuestion = {
  id: 'math-q4a',
  subject: 'math',
  section: 'Comparing & Ordering Numbers',
  qNumber: 'Q4a',
  grade: 2,
  questionEng: 'Order these from smallest to largest: 867, 876, 786',
  questionKhmer: 'តម្រៀបពីតូចទៅធំ៖ ៨៦៧, ៨៧៦, ៧៨៦',
  learningGoalEng: 'Comparing digits from left to right systematically.',
  learningGoalKhmer: 'ប្រៀបធៀបខ្ទង់ពីឆ្វេងទៅស្តាំដោយមានប្រព័ន្ធ។',
  correctAnswer: '786, 867, 876',
  acceptablePatterns: ['786.*867.*876', '7-8-6.*8-6-7.*8-7-6'],
  hints: [
    {
      level: 0,
      eng: "Before looking at the last two digits, compare the hundreds digits. Which number has the smallest hundreds digit?",
      khmer: "មុនពេលមើលខ្ទង់ចុងក្រោយពីរ សូមប្រៀបធៀបខ្ទង់រយ។ តើលេខណាមានខ្ទង់រយតូចបំផុត?",
    },
    {
      level: 1,
      eng: "Look at the hundreds digit of each number: 8, 8, and 7. Which is smallest?",
      khmer: "មើលខ្ទង់រយនៃលេខនីមួយៗ៖ ៨, ៨ និង ៧។ តើណាតូចបំផុត?",
    },
    {
      level: 2,
      eng: "786 is smallest. Now compare the two numbers starting with 8. Look at their tens digits: 6 and 7.",
      khmer: "៧៨៦ គឺតូចបំផុត។ ឥឡូវប្រៀបធៀបលេខពីរដែលចាប់ផ្តើមដោយ ៨។ មើលខ្ទង់និចសិបរបស់វា៖ ៦ និង ៧។",
    },
    {
      level: 3,
      eng: "786 < 867 < 876. The hundreds digits are 7, 8, 8. For 867 and 876, compare tens: 6 < 7.",
      khmer: "៧៨៦ < ៨៦៧ < ៨៧៦។ ខ្ទង់រយគឺ ៧, ៨, ៨។ សម្រាប់ ៨៦៧ និង ៨៧៦ ប្រៀបធៀបនិចសិប៖ ៦ < ៧។",
    },
  ],
  whyFollowUpEng: "Great! Why do we compare the hundreds digits first instead of the ones?",
  whyFollowUpKhmer: "ល្អ! ហេតុអ្វីយើងប្រៀបធៀបខ្ទង់រយជាមុនជាជាងខ្ទង់?",
  expectedResponses: [
    {
      pattern: '786.*867.*876|7.?8.?6.*8.?6.?7.*8.?7.?6',
      isCorrect: true,
      feedbackEng: "Perfect! 786 < 867 < 876. You compared the hundreds first, then tens!",
      feedbackKhmer: "ល្អឥតខ្ចោះ! ៧៨៦ < ៨៦៧ < ៨៧៦។ អ្នកប្រៀបធៀបរយជាមុន បន្ទាប់មកនិចសិប!",
      nextAction: 'ask_why',
    },
  ],
};

const MATH_Q4B: TutorQuestion = {
  id: 'math-q4b',
  subject: 'math',
  section: 'Comparing & Ordering Numbers',
  qNumber: 'Q4b',
  grade: 2,
  questionEng: 'Fill in the box: 426 [ ? ] 462 (use < or >)',
  questionKhmer: 'បំពេញប្រអប់៖ ៤២៦ [ ? ] ៤៦២ (ប្រើ < ឬ >)',
  learningGoalEng: 'Systematic comparison using place value.',
  learningGoalKhmer: 'ការប្រៀបធៀបប្រព័ន្ធដោយប្រើតម្លៃទីតាំង។',
  correctAnswer: '<',
  acceptablePatterns: ['<', 'less', 'smaller'],
  hints: [
    {
      level: 0,
      eng: "Start with the hundreds digit. Are they different or the same?",
      khmer: "ចាប់ផ្តើមដោយខ្ទង់រយ។ តើវាខុសគ្នា ឬដូចគ្នា?",
    },
    {
      level: 1,
      eng: "The hundreds are both 4. If they're the same, which place should we compare next?",
      khmer: "ខ្ទង់រយទាំងពីរគឺ ៤។ បើវាដូចគ្នា តើយើងគួរប្រៀបធៀបទីតាំងណាបន្ទាប់?",
    },
    {
      level: 2,
      eng: "Compare the tens digits: 2 and 6. Which tens digit is larger?",
      khmer: "ប្រៀបធៀបខ្ទង់និចសិប៖ ២ និង ៦។ តើខ្ទង់និចសិបណាធំជាង?",
    },
    {
      level: 3,
      eng: "426 < 462 because 2 tens < 6 tens. The hundreds are the same.",
      khmer: "៤២៦ < ៤៦២ ព្រោះ ២និចសិប < ៦និចសិប។ ខ្ទង់រយដូចគ្នា។",
    },
  ],
  whyFollowUpEng: "Good! Why does comparing the tens digit decide which number is bigger?",
  whyFollowUpKhmer: "ល្អ! ហេតុអ្វីការប្រៀបធៀបខ្ទង់និចសិបបានសម្រេចថាតើលេខណាធំជាង?",
  expectedResponses: [
    {
      pattern: '<|less|smaller',
      isCorrect: true,
      feedbackEng: "Correct! 426 < 462 because 2 tens is less than 6 tens!",
      feedbackKhmer: "ត្រឹមត្រូវ! ៤២៦ < ៤៦២ ព្រោះ ២និចសិប តូចជាង ៦និចសិប!",
      nextAction: 'ask_why',
    },
    {
      pattern: '>|greater|bigger',
      isCorrect: false,
      feedbackEng: "Not quite. Check the tens digits: 2 vs 6. Which is smaller?",
      feedbackKhmer: "មិនទាន់ត្រឹមត្រូវ។ ពិនិត្យខ្ទង់និចសិប៖ ២ ទល់នឹង ៦។ តើណាតូចជាង?",
      nextAction: 'retry',
    },
  ],
};

// ═══════════════════════════════════════════════════════
//  Export all questions
// ═══════════════════════════════════════════════════════

export const TUTOR_QUESTIONS: TutorQuestion[] = [
  MATH_Q1,
  MATH_Q2,
  MATH_Q3,
  MATH_Q4A,
  MATH_Q4B,
];

export function findQuestionById(id: string): TutorQuestion | undefined {
  return TUTOR_QUESTIONS.find((q) => q.id === id);
}

export function findQuestionsBySubject(subject: Subject): TutorQuestion[] {
  return TUTOR_QUESTIONS.filter((q) => q.subject === subject);
}
