import { HomeworkProblem } from '../types';

export const MOCK_PROBLEMS: HomeworkProblem[] = [
  {
    id: 'math-g4-apples',
    titleKhmer: 'ចំណោទគណិតវិទ្យា៖ ការគុណ',
    titleEng: 'Math Problem: Multiplication',
    grade: 4,
    subject: 'math',
    problemStatementKhmer: 'មាន ៥ ប្រអប់។ ប្រអប់នីមួយៗមានផ្លែប៉ោម ៨ ផ្លែ។ តើមានផ្លែប៉ោមសរុបប៉ុន្មានផ្លែ?',
    problemStatementEng: 'There are 5 boxes. Each box has 8 apples. How many apples are there altogether?',
    imageUri: 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&auto=format&fit=crop&q=80',
    steps: [
      {
        id: 'step-1',
        stepNumber: 1,
        totalSteps: 4,
        questionKhmer: 'តើមានប្រអប់ចំនួនប៉ុន្មាននៅក្នុងចំណោទនេះ?',
        questionEng: 'How many boxes are there in the question?',
        inputFormat: 'number',
        correctAnswer: '5',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើមានប្រអប់ចំនួនប៉ុន្មាននៅក្នុ...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`How many boxes are there in the question...'?'`,

        hint1: {
          khmer: 'សូមមើលលេខដំបូងនៅក្នុងសំណួរ។',
          eng: 'Look at the first number mentioned in the question.'
        },
        hint2: {
          khmer: 'សំណួរប្រាប់ថា "មាន ៥ ប្រអប់..."',
          eng: 'The question mentions "There are 5 boxes..."'
        },
        hint3: {
          titleKhmer: 'ឧទាហរណ៍ស្រដៀងគ្នា',
          titleEng: 'Similar Example',
          exampleKhmer: 'បើគេថា "មាន ៣ កញ្ចប់" នោះចំនួនកញ្ចប់គឺ ៣។ ដូច្នេះសម្រាប់សំណួរនេះ ចម្លើយគឺ ៥!',
          exampleEng: 'If it says "There are 3 packs", the count is 3. So for this question, the answer is 5!'
        },
        explainDifferently: {
          simpleKhmer: 'គិតថាជាប្រអប់កាតុងដែលដាក់នៅលើតុ។ រាប់ប្រអប់ទាំងនោះ៖ ១, ២, ៣, ៤, ៥។',
          simpleEng: 'Imagine cardboard boxes sitting on a table. Count them: 1, 2, 3, 4, 5.',
          analogyTitle: 'ប្រអប់ផ្លែឈើ (Fruit Boxes)',
          analogyKhmer: 'ស្រមៃមើលប្រអប់ចំនួន ៥ ត្រៀបគ្នានៅក្នុងហាងផលផ្លែឈើ។',
          analogyEng: 'Picture 5 boxes lined up on a fruit shelf.',
          analogyType: 'apples'
        }
      },
      {
        id: 'step-2',
        stepNumber: 2,
        totalSteps: 4,
        questionKhmer: 'តើប្រអប់នីមួយៗមានផ្លែប៉ោមចំនួនប៉ុន្មានផ្លែ?',
        questionEng: 'How many apples are in EACH box?',
        inputFormat: 'number',
        correctAnswer: '8',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើប្រអប់នីមួយៗមានផ្លែប៉ោមចំនួន...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`How many apples are in EACH box?...'?'`,

        hint1: {
          khmer: 'ពិនិត្យមើលចំនួនផ្លែប៉ោមនៅក្នុងប្រអប់មួយ។',
          eng: 'Check the number of apples inside one box.'
        },
        hint2: {
          khmer: 'សំណួរនិយាយថា "ប្រអប់នីមួយៗមានផ្លែប៉ោម ៨ ផ្លែ..."',
          eng: 'The sentence says "Each box has 8 apples..."'
        },
        hint3: {
          titleKhmer: 'ឧទាហរណ៍ស្រដៀងគ្នា',
          titleEng: 'Similar Example',
          exampleKhmer: 'បើក្នុងប្រអប់មួយមានស្ករគ្រាប់ ៤ គ្រាប់ ចំនួនគឺ ៤។ ចំពោះប្រអប់ផ្លែប៉ោមយើង ចំនួនគឺ ៨!',
          exampleEng: 'If one box holds 4 candies, the count is 4. For our apple box, the count is 8!'
        },
        explainDifferently: {
          simpleKhmer: 'បើអ្នកបើកប្រអប់ទី១ រាប់ផ្លែប៉ោមក្នុងនោះ អ្នកនឹងឃើញ ៨ ផ្លែ។',
          simpleEng: 'If you open Box #1 and count the apples inside, you see 8 apples.',
          analogyTitle: 'ការរាប់ក្នុងប្រអប់ (Inside one box)',
          analogyKhmer: 'ប្រអប់នីមួយៗមានផ្លែប៉ោម ៨ ផ្លែដូចៗគ្នា។',
          analogyEng: 'Every single box contains exactly 8 apples.',
          analogyType: 'apples'
        }
      },
      {
        id: 'step-3',
        stepNumber: 3,
        totalSteps: 4,
        questionKhmer: 'ដើម្បីរកចំនួនផ្លែប៉ោមសរុប តើយើងគួរបប្រើប្រមាណវិធីអ្វី?',
        questionEng: 'Which math operation should we use to find the total apples?',
        inputFormat: 'mcq',
        options: [
          'ការបូក ឬ ការគុណ (Addition or Multiplication)',
          'ការដក (Subtraction)',
          'ការចែក (Division)'
        ],
        correctAnswer: 'ការបូក ឬ ការគុណ (Addition or Multiplication)',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`ដើម្បីរកចំនួនផ្លែប៉ោមសរុប តើយើ...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`Which math operation should we use to fi...'?'`,

        hint1: {
          khmer: 'យើងមានក្រុមស្មើៗគ្នាដែលត្រូវរួមបញ្ចូលគ្នា។',
          eng: 'We are combining equal groups together.'
        },
        hint2: {
          khmer: 'ពេលយើងមាន ៥ ក្រុម ហើយក្រុមនីមួយៗមាន ៨ យើងអាចបូក ៨ ប្រាំដង ឬគុណ ៥ × ៨!',
          eng: 'When we have 5 groups of 8, we add 8 five times or multiply 5 × 8!'
        },
        hint3: {
          titleKhmer: 'ឧទាហរណ៍ប្រមាណវិធី',
          titleEng: 'Operation Example',
          exampleKhmer: '៣ ក្រុមនៃ ៤ = ៤ + ៤ + ៤ = ៣ × ៤ = ១២ (ប្រមាណវិធីគុណ!)',
          exampleEng: '3 groups of 4 = 4 + 4 + 4 = 3 × 4 = 12 (Multiplication operation!)'
        },
        explainDifferently: {
          simpleKhmer: 'ការគុណ គឺជាវិធីរហ័សនៃការបូកចំនួនដដែលៗជាច្រើនដង។',
          simpleEng: 'Multiplication is a shortcut for adding the same number repeatedly.',
          analogyTitle: 'ផ្លូវកាត់គណិតវិទ្យា (Math Shortcut)',
          analogyKhmer: 'ជំនួសឲ្យការបូក ៨+៨+៨+៨+៨ យើងអាចគុណ ៥ × ៨ យ៉ាងលឿន!',
          analogyEng: 'Instead of adding 8+8+8+8+8, we shortcut with 5 × 8!',
          analogyType: 'apples'
        }
      },
      {
        id: 'step-4',
        stepNumber: 4,
        totalSteps: 4,
        questionKhmer: 'ល្អណាស់! ឥឡូវគណនា ៥ × ៨ = ?',
        questionEng: 'Great job! Now calculate 5 × 8 = ?',
        inputFormat: 'number',
        correctAnswer: '40',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`ល្អណាស់! ឥឡូវគណនា ៥ × ៨ = ?...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`Great job! Now calculate 5 × 8 = ?...'?'`,

        hint1: {
          khmer: 'រាប់បន្ថែមម្តង ៥ ឬមើលមេគុណ ៥៖ ៥, ១០, ១៥, ២០, ២៥, ៣០, ៣៥...',
          eng: 'Count by 5s eight times: 5, 10, 15, 20, 25, 30, 35...'
        },
        hint2: {
          khmer: 'បន្ទាប់ពី ៣៥ បូក ៥ ទៀតគឺ...',
          eng: 'After 35, add 5 more to get...'
        },
        hint3: {
          titleKhmer: 'គន្លឹះមេគុណ ៥',
          titleEng: 'Times Table Trick',
          exampleKhmer: '៥ × ៧ = ៣៥ ដូច្នេះ ៥ × ៨ = ៣៥ + ៥ = ៤០!',
          exampleEng: '5 × 7 = 35 so 5 × 8 = 35 + 5 = 40!'
        },
        explainDifferently: {
          simpleKhmer: 'ប្រើម្រាមដៃរាប់មេ ៥ ចំនួន ៨ ដង៖ ៥, ១០, ១៥, ២០, ២៥, ៣០, ៣៥, ៤០!',
          simpleEng: 'Count by 5s eight times on your fingers: 5, 10, 15, 20, 25, 30, 35, 40!',
          analogyTitle: 'ការរាប់ជាក្រុម (Group Counting)',
          analogyKhmer: 'ផ្លែប៉ោមសរុបនៅក្នុងប្រអប់ទាំង ៥ គឺ ៤០ ផ្លែ!',
          analogyEng: 'Total apples in all 5 boxes equal 40 apples!',
          analogyType: 'apples'
        }
      }
    ]
  },
  {
    id: 'science-g4-water',
    titleKhmer: 'វិទ្យាសាស្ត្រ៖ សភាពនៃសារធាតុ និងការរលាយ',
    titleEng: 'Science: States of Matter & Melting',
    grade: 4,
    subject: 'science',
    problemStatementKhmer: 'នៅពេលដែលដុំទឹកកកត្រូវគេទុកក្នុងបន្ទប់ក្តៅ វាប្រែជាទឹក។ តើដំណើរការនេះហៅថាអ្វី ហើយវាប្តូរពីសភាពអ្វីទៅសភាពអ្វី?',
    problemStatementEng: 'When an ice cube is left in a warm room, it turns into water. What is this process called, and what state change happens?',
    imageUri: 'https://images.unsplash.com/photo-1548839140-29a749e1cf4e?w=600&auto=format&fit=crop&q=80',
    steps: [
      {
        id: 'sci-step-1',
        stepNumber: 1,
        totalSteps: 3,
        questionKhmer: 'តើដុំទឹកកកមុនពេលរលាយស្ថិតក្នុងសភាពអ្វី? (រឹង, រាវ, ឬ ឧស្ម័ន)',
        questionEng: 'What state of matter is the ice cube BEFORE it melts? (Solid, Liquid, or Gas)',
        inputFormat: 'mcq',
        options: ['សភាពរឹង (Solid)', 'សភាពរាវ (Liquid)', 'សភាពឧស្ម័ន (Gas)'],
        correctAnswer: 'សភាពរឹង (Solid)',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើដុំទឹកកកមុនពេលរលាយស្ថិតក្នុង...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`What state of matter is the ice cube BEF...'?'`,

        hint1: {
          khmer: 'ដុំទឹកកកមានរូបរាងច្បាស់លាស់ ហើយយើងអាចកាន់វាបាន។',
          eng: 'An ice cube has a fixed shape and you can hold it.'
        },
        hint2: {
          khmer: 'អ្វីៗដែលមានរូបរាងថេរមិនហូរ គឺជាសភាពរឹង!',
          eng: 'Things that keep their shape and do not flow are Solids!'
        },
        hint3: {
          titleKhmer: 'ឧទាហរណ៍សភាពរឹង',
          titleEng: 'Solid Examples',
          exampleKhmer: 'ថ្ម ឈើ និងដុំទឹកកក សុទ្ធតែជាសភាពរឹង (Solid)។',
          exampleEng: 'Rocks, wood, and ice cubes are all Solids.'
        },
        explainDifferently: {
          simpleKhmer: 'ទឹកកកគឺជារឹង ព្រោះវាមានរាងរឹងមាំ និងមិនហូរដូចទឹកឡើយ។',
          simpleEng: 'Ice is solid because it stays firm and doesn\'t flow around.',
          analogyTitle: 'ដុំទឹកកករឹង (Solid Ice)',
          analogyKhmer: 'ដូចជាដុំកែវ ឬដុំថ្មតូចមួយ។',
          analogyEng: 'Just like a marble or a small pebble.',
          analogyType: 'water'
        }
      },
      {
        id: 'sci-step-2',
        stepNumber: 2,
        totalSteps: 2,
        questionKhmer: 'តើដំណើរការនៃការប្រែប្រួលពី "សភាពរឹង" ទៅ "សភាពរាវ" ហៅថាអ្វី?',
        questionEng: 'What is the change from "Solid" to "Liquid" called?',
        inputFormat: 'mcq',
        options: ['ការរលាយ (Melting)', 'ការកក (Freezing)', 'ការរំហួត (Evaporation)'],
        correctAnswer: 'ការរលាយ (Melting)',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើដំណើរការនៃការប្រែប្រួលពី "សភ...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`What is the change from "Solid" to "Liqu...'?'`,

        hint1: {
          khmer: 'គិតពីប្រឡាក់ការ៉ែមនៅថ្ងៃក្តៅ។',
          eng: 'Think of an ice cream on a sunny day.'
        },
        hint2: {
          khmer: 'នៅពេលកម្ដៅធ្វើឲ្យទឹកកកក្លាយជាទឹក វាគឺ "ការរលាយ" (Melting)!',
          eng: 'When heat turns solid ice into liquid water, it is "Melting"!'
        },
        hint3: {
          titleKhmer: 'ពាក្យគន្លឹះវិទ្យាសាស្ត្រ',
          titleEng: 'Science Keyword',
          exampleKhmer: 'រឹង → រាវ = ការរលាយ (Melting)',
          exampleEng: 'Solid → Liquid = Melting'
        },
        explainDifferently: {
          simpleKhmer: 'កម្ដៅក្នុងបន្ទប់ធ្វើឲ្យភាគល្អិតទឹកកកមានថាមពល ហើយរលាយក្លាយជាទឹករាវ។',
          simpleEng: 'Heat gives energy to the ice particles, making them flow as liquid water.',
          analogyTitle: 'ការរលាយការ៉ែម (Ice Cream Melting)',
          analogyKhmer: 'ដូចជាការ៉ែមដែលស្រក់ចុះនៅពេលត្រូវពន្លឺព្រះអាទិត្យ។',
          analogyEng: 'Like ice cream dripping down under hot sunlight.',
          analogyType: 'water'
        }
      }
    ]
  },
  {
    id: 'english-g4-grammar',
    titleKhmer: 'ភាសាអង់គ្លេស៖ កិរិយាស័ព្ទ Present Simple',
    titleEng: 'English: Present Simple Verbs',
    grade: 4,
    subject: 'english',
    problemStatementKhmer: 'បំពេញចន្លោះក្នុងប្រយោគ៖ "ReanMore ___ (like) apples." តើត្រូវថែម "s" នៅចុងកិរិយាស័ព្ទ like ឬទេ?',
    problemStatementEng: 'Fill in the blank: "ReanMore ___ (like) apples." Should we add "s" to the verb like?',
    imageUri: 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=600&auto=format&fit=crop&q=80',
    steps: [
      {
        id: 'eng-step-1',
        stepNumber: 1,
        totalSteps: 2,
        questionKhmer: 'នៅក្នុងប្រយោគនេះ "ReanMore" គឺជាប្រធានឯកវចនៈ (Singular Subject, He/She/It)។ តើកិរិយាស័ព្ទត្រូវថែមអ្វី?',
        questionEng: 'In this sentence, "ReanMore" is a singular subject (He/She/It). What do we add to the verb?',
        inputFormat: 'mcq',
        options: ['ថែម -s (likes)', 'ថែម -ing (liking)', 'មិនថែមអ្វីទាំងអស់ (like)'],
        correctAnswer: 'ថែម -s (likes)',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`នៅក្នុងប្រយោគនេះ "ReanMore" គឺជា...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`In this sentence, "ReanMore" is a singular...'?'`,

        hint1: {
          khmer: 'សម្រាប់ He, She, It ឬឈ្មោះមនុស្សម្នាក់ (ReanMore) កិរិយាស័ព្ទត្រូវថែម -s!',
          eng: 'For He, She, It, or one person name (ReanMore), we add -s to the verb!'
        },
        hint2: {
          khmer: 'ReanMore like + s = ReanMore likes!',
          eng: 'ReanMore like + s = ReanMore likes!'
        },
        hint3: {
          titleKhmer: 'វិធានវេយ្យាករណ៍',
          titleEng: 'Grammar Rule',
          exampleKhmer: 'He plays, She reads, ReanMore likes!',
          exampleEng: 'He plays, She reads, ReanMore likes!'
        },
        explainDifferently: {
          simpleKhmer: 'ពេលនិយាយពីមនុស្សម្នាក់ ដូចជា ReanMore (ReanMore) យើងថែមអក្សរ "s" នៅខាងចុងពាក្យដូចជា likes!',
          simpleEng: 'When talking about one friend like ReanMore, we put an "s" at the end of the action word: likes!',
          analogyTitle: 'អក្សរ S សម្រាប់មិត្តម្នាក់ (The Letter S)',
          analogyKhmer: 'គិតថាអក្សរ S គឺជាកាដូជូនមិត្តម្នាក់!',
          analogyEng: 'Think of the letter "s" as a small gift for one person!',
          analogyType: 'apples'
        }
      },
      {
        id: 'eng-step-2',
        stepNumber: 2,
        totalSteps: 2,
        questionKhmer: 'តើប្រយោគពេញលេញដែលត្រឹមត្រូវគឺជាអ្វី?',
        questionEng: 'What is the correct full sentence?',
        inputFormat: 'mcq',
        options: ['ReanMore likes apples.', 'ReanMore liking apples.', 'ReanMore like apples.'],
        correctAnswer: 'ReanMore likes apples.',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើប្រយោគពេញលេញដែលត្រឹមត្រូវគឺជ...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`What is the correct full sentence?...'?'`,

        hint1: {
          khmer: 'ជ្រើសរើសប្រយោគដែលមានពាក្យ "likes"។',
          eng: 'Choose the sentence with "likes".'
        },
        hint2: {
          khmer: 'ReanMore + likes + apples!',
          eng: 'ReanMore + likes + apples!'
        },
        hint3: {
          titleKhmer: 'ចម្លើយចុងក្រោយ',
          titleEng: 'Final Answer',
          exampleKhmer: 'ReanMore likes apples.',
          exampleEng: 'ReanMore likes apples.'
        },
        explainDifferently: {
          simpleKhmer: 'ពូកែណាស់! ប្រយោគពេញលេញគឺ "ReanMore likes apples."',
          simpleEng: 'Awesome job! The complete sentence is "ReanMore likes apples."',
          analogyTitle: 'ប្រយោគពេញលេញ (Full Sentence)',
          analogyKhmer: 'ReanMoreចូលចិត្តញ៉ាំផ្លែប៉ោម!',
          analogyEng: 'ReanMore loves eating apples!',
          analogyType: 'apples'
        }
      }
    ]
  },
  {
    id: 'math-g3-perimeter',
    titleKhmer: 'គណិតវិទ្យា៖ រង្វាស់បរិមាត្រចតុគោណកែង',
    titleEng: 'Math: Perimeter of a Rectangle',
    grade: 3,
    subject: 'math',
    problemStatementKhmer: 'សួនច្បារសាលារៀនមួយមានរាងជាចតុគោណកែង ដែលមានបណ្តោយ ១០ ម៉ែត្រ និងទទឹង ៥ ម៉ែត្រ។ តើបរិមាត្រសរុបនៃសួនច្បារនេះស្មើនឹងប៉ុន្មានម៉ែត្រ?',
    problemStatementEng: 'A school garden is rectangular with a length of 10 meters and width of 5 meters. What is the total perimeter of the garden?',
    imageUri: 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=600&auto=format&fit=crop&q=80',
    steps: [
      {
        id: 'perim-step-1',
        stepNumber: 1,
        totalSteps: 3,
        questionKhmer: 'តើប្រវែងបណ្តោយ (Length) និងទទឹង (Width) នៃសួនច្បារមានប៉ុន្មានម៉ែត្រ?',
        questionEng: 'What are the length and width of the garden?',
        inputFormat: 'mcq',
        options: ['បណ្តោយ ១០m, ទទឹង ៥m', 'បណ្តោយ ៥m, ទទឹង ១០m', 'បណ្តោយ ១៥m, ទទឹង ០m'],
        correctAnswer: 'បណ្តោយ ១០m, ទទឹង ៥m',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើប្រវែងបណ្តោយ (Length) និងទទឹង...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`What are the length and width of the ga...'?'`,

        hint1: {
          khmer: 'មើលលេខនៅក្នុងប្រធានបទចំណោទ៖ "បណ្តោយ ១០ ម៉ែត្រ និងទទឹង ៥ ម៉ែត្រ"',
          eng: 'Look at the numbers given: length = 10m, width = 5m'
        },
        hint2: {
          khmer: 'ជ្រើសរើសចម្លើយដែលប្រាប់ថា បណ្តោយ ១០m និង ទទឹង ៥m!',
          eng: 'Select length 10m and width 5m!'
        },
        hint3: {
          titleKhmer: 'ប្រវែងជ្រុងចតុគោណកែង',
          titleEng: 'Rectangle Dimensions',
          exampleKhmer: 'ចតុគោណកែងមានជ្រុងទល់មុខស្មើគ្នា៖ បណ្តោយ២ និងទទឹង២',
          exampleEng: 'A rectangle has opposite equal sides: 2 lengths and 2 widths'
        },
        explainDifferently: {
          simpleKhmer: 'ស្រមៃមើលសួនច្បាររាងចតុកោណកែង៖ ជ្រុងវែង ១០m និងជ្រុងខ្លី ៥m!',
          simpleEng: 'Picture a rectangle garden: long side is 10m and short side is 5m!',
          analogyTitle: 'សួនច្បារសាលារៀន (School Garden)',
          analogyKhmer: 'យើងដើរជុំវិញសួនច្បារដែលមានជ្រុងវែង ២ និងជ្រុងខ្លី ២!',
          analogyEng: 'Walking around a garden with two long sides and two short sides!',
          analogyType: 'pizza'
        }
      },
      {
        id: 'perim-step-2',
        stepNumber: 2,
        totalSteps: 3,
        questionKhmer: 'តើរូបមន្តបរិមាត្រចតុគោណកែង (Perimeter) គឺជាអ្វី?',
        questionEng: 'What is the correct formula for the perimeter of a rectangle?',
        inputFormat: 'mcq',
        options: [
          'P = (បណ្តោយ + ទទឹង) × ២',
          'P = បណ្តោយ × ទទឹង',
          'P = បណ្តោយ - ទទឹង'
        ],
        correctAnswer: 'P = (បណ្តោយ + ទទឹង) × ២',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើរូបមន្តបរិមាត្រចតុគោណកែង (Pe...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`What is the correct formula for the peri...'?'`,

        hint1: {
          khmer: 'បរិមាត្រ គឺជាផលបូកនៃជ្រុងទាំង ៤ (បណ្តោយ + ទទឹង + បណ្តោយ + ទទឹង)',
          eng: 'Perimeter is the sum of all 4 sides (Length + Width + Length + Width)'
        },
        hint2: {
          khmer: 'យើងអាចបូកបណ្តោយនិងទទឹង រួចគុណនឹង ២!',
          eng: 'We add length and width then multiply by 2!'
        },
        hint3: {
          titleKhmer: 'រូបមន្តបរិមាត្រ',
          titleEng: 'Perimeter Formula',
          exampleKhmer: 'P = (L + W) × 2',
          exampleEng: 'P = (L + W) × 2'
        },
        explainDifferently: {
          simpleKhmer: 'បរិមាត្រគឺជាប្រវែងរវ៉ាត់ជុំវិញរាង។ (១០ + ៥ + ១០ + ៥)',
          simpleEng: 'Perimeter is the total boundary distance around the shape. (10 + 5 + 10 + 5)',
          analogyTitle: 'របងសួន (Garden Fence)',
          analogyKhmer: 'វាដូចជាការប្រមាណប្រវែងរបងសរុបដើម្បីព័ទ្ធជុំវិញសួន!',
          analogyEng: 'Like measuring the total fence length to surround the garden!',
          analogyType: 'pizza'
        }
      },
      {
        id: 'perim-step-3',
        stepNumber: 3,
        totalSteps: 3,
        questionKhmer: 'គណនាបរិមាត្រ P = (១០ + ៥) × ២ = ? (គិតជាម៉ែត្រ)',
        questionEng: 'Calculate the perimeter P = (10 + 5) × 2 = ? (in meters)',
        inputFormat: 'number',
        correctAnswer: '30',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`គណនាបរិមាត្រ P = (១០ + ៥) × ២ ...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`Calculate the perimeter P = (10 + 5) × 2...'?'`,

        hint1: {
          khmer: 'បូកក្នុងវង់ក្រចកមុន៖ ១០ + ៥ = ១៥',
          eng: 'Add inside parentheses first: 10 + 5 = 15'
        },
        hint2: {
          khmer: 'បន្ទាប់មកយក ១៥ គុណនឹង ២៖ ១៥ × ២ = ៣០',
          eng: 'Then multiply 15 by 2: 15 × 2 = 30'
        },
        hint3: {
          titleKhmer: 'គណនាតាមលំដាប់',
          titleEng: 'Step Calculation',
          exampleKhmer: '១០ + ៥ = ១៥, បន្ទាប់មក ១៥ × ២ = ៣០m!',
          exampleEng: '10 + 5 = 15, then 15 × 2 = 30m!'
        },
        explainDifferently: {
          simpleKhmer: '១៥ បូក ១៥ ស្មើនឹង ៣០! ដូច្នេះរបងព័ទ្ធជុំវិញមានប្រវែង ៣០ ម៉ែត្រ។',
          simpleEng: '15 plus 15 equals 30! So the total fence distance is 30 meters.',
          analogyTitle: 'ប្រវែងសរុប (Total Length)',
          analogyKhmer: 'បរិមាត្រសួនច្បារសរុបគឺ ៣០ ម៉ែត្រ!',
          analogyEng: 'Total garden perimeter is 30 meters!',
          analogyType: 'pizza'
        }
      }
    ]
  },
  {
    id: 'science-g5-plants',
    titleKhmer: 'វិទ្យាសាស្ត្រ៖ ដំណើរការរស្មីសំយោគរុក្ខជាតិ',
    titleEng: 'Science: Plant Photosynthesis Process',
    grade: 5,
    subject: 'science',
    problemStatementKhmer: 'តើរុក្ខជាតិបៃតងត្រូវការកត្តាសំខាន់ៗអ្វីខ្លះ មកពីដី បរិយាកាស និងព្រះអាទិត្យ ដើម្បីធ្វើរស្មីសំយោគបង្កើតអាហារ និងអុកស៊ីសែន?',
    problemStatementEng: 'What key ingredients do green plants collect from soil, air, and the sun for photosynthesis to create food and oxygen?',
    imageUri: 'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=600&auto=format&fit=crop&q=80',
    steps: [
      {
        id: 'plant-step-1',
        stepNumber: 1,
        totalSteps: 3,
        questionKhmer: 'តើរុក្ខជាតិបឺតស្រូបធាតុរាវអ្វីពីក្នុងដីតាមរយៈឬស?',
        questionEng: 'What liquid component do plant roots absorb from the soil?',
        inputFormat: 'mcq',
        options: ['ទឹក (Water)', 'ប្រេង (Oil)', 'ទឹកដោះគោ (Milk)'],
        correctAnswer: 'ទឹក (Water)',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើរុក្ខជាតិបឺតស្រូបធាតុរាវអ្វី...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`What liquid component do plant roots abs...'?'`,

        hint1: {
          khmer: 'ពេលយើងស្រោចដំណាំ យើងចាក់ធាតុរាវនេះទៅលើដី។',
          eng: 'When we water plants, we pour this liquid onto the soil.'
        },
        hint2: {
          khmer: 'ឬសបឺតស្រូប "ទឹក (Water)" និងសារធាតុរ៉ែពីដី!',
          eng: 'Roots absorb "Water" and minerals from soil!'
        },
        hint3: {
          titleKhmer: 'សារធាតុចម្បង',
          titleEng: 'Main Substance',
          exampleKhmer: 'រុក្ខជាតិត្រូវការទឹកជាចាំបាច់ដើម្បីរស់។',
          exampleEng: 'Plants essential liquid is water.'
        },
        explainDifferently: {
          simpleKhmer: 'ឬសដើរតួដូចបំពង់បឺត បឺតទឹកពីដីឡើងទៅកាន់ស្លឹក!',
          simpleEng: 'Roots act like drinking straws, sucking water up to the leaves!',
          analogyTitle: 'បំពង់បឺតរុក្ខជាតិ (Plant Straws)',
          analogyKhmer: 'បឺតទឹកពីដីឡើងលើ!',
          analogyEng: 'Sucking water up from the soil!',
          analogyType: 'plants'
        }
      },
      {
        id: 'plant-step-2',
        stepNumber: 2,
        totalSteps: 3,
        questionKhmer: 'តើរុក្ខជាតិស្រូបយកឧស្ម័នអ្វីពីខ្យល់អាកាសតាមរយៈស្លឹក?',
        questionEng: 'What gas do plant leaves take in from the air?',
        inputFormat: 'mcq',
        options: ['កាបូនិច (Carbon Dioxide)', 'អុកស៊ីសែន (Oxygen)', 'អាសូត (Nitrogen)'],
        correctAnswer: 'កាបូនិច (Carbon Dioxide)',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើរុក្ខជាតិស្រូបយកឧស្ម័នអ្វីពី...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`What gas do plant leaves take in from th...'?'`,

        hint1: {
          khmer: 'វាជាឧស្ម័នដែលមនុស្ស និងសត្វដកដង្ហើមចេញ។',
          eng: 'It is the gas humans and animals breathe out.'
        },
        hint2: {
          khmer: 'រុក្ខជាតិស្រូបយក "កាបូនិច" ហើយបញ្ចេញ "អុកស៊ីសែន" មកវិញ!',
          eng: 'Plants take in "Carbon Dioxide" and release "Oxygen"!'
        },
        hint3: {
          titleKhmer: 'ការផ្លាស់ប្តូរឧស្ម័ន',
          titleEng: 'Gas Exchange',
          exampleKhmer: 'ស្រូបកាបូនិច → បញ្ចេញអុកស៊ីសែន',
          exampleEng: 'Takes in CO2 → Releases O2'
        },
        explainDifferently: {
          simpleKhmer: 'ស្លឹកមានរន្ធតូចៗ (Stomata) សម្រាប់ស្រូបយកឧស្ម័នកាបូនិចពីខ្យល់!',
          simpleEng: 'Leaves have tiny mouth pores (stomata) to breathe in carbon dioxide!',
          analogyTitle: 'រន្ធដង្ហើមស្លឹក (Leaf Pores)',
          analogyKhmer: 'ស្រូបកាបូនិចដើម្បីធ្វើអាហារ!',
          analogyEng: 'Breathing in CO2 to make food!',
          analogyType: 'plants'
        }
      },
      {
        id: 'plant-step-3',
        stepNumber: 3,
        totalSteps: 3,
        questionKhmer: 'តើប្រភពថាមពលធម្មជាតិចម្បងអ្វីដែលជួយឲ្យស្លឹកធ្វើរស្មីសំយោគ?',
        questionEng: 'What main natural energy source powers the leaves during photosynthesis?',
        inputFormat: 'mcq',
        options: ['ពន្លឺព្រះអាទិត្យ (Sunlight)', 'ពន្លឺអំពូលអគ្គិសនី (Light bulb)', 'ខ្យល់ព្យុះ (Storm)'],
        correctAnswer: 'ពន្លឺព្រះអាទិត្យ (Sunlight)',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើប្រភពថាមពលធម្មជាតិចម្បងអ្វីដ...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`What main natural energy source powers t...'?'`,

        hint1: {
          khmer: 'វាចែងចាំងពីលើមេឃនៅពេលថ្ងៃ។',
          eng: 'It shines brightly from the sky during daytime.'
        },
        hint2: {
          khmer: 'រស្មីសំយោគត្រូវការ "ពន្លឺព្រះអាទិត្យ (Sunlight)" ជាថាមពល!',
          eng: 'Photosynthesis uses "Sunlight" as energy source!'
        },
        hint3: {
          titleKhmer: 'ថាមពលពន្លឺ',
          titleEng: 'Light Energy',
          exampleKhmer: 'ស្លឹកបៃតងចាប់យកពន្លឺព្រះអាទិត្យដោយសារជាតិក្លរ៉ូភីល',
          exampleEng: 'Green leaves capture sunlight using chlorophyll'
        },
        explainDifferently: {
          simpleKhmer: 'ពន្លឺព្រះអាទិត្យផ្តល់ថាមពលដូចជាចង្រ្កានបាយដែលចម្អិនអាហារឲ្យរុក្ខជាតិ!',
          simpleEng: 'Sunlight acts like a stove heater that cooks food for the plant!',
          analogyTitle: 'ចង្រ្កានបាយព្រះអាទិត្យ (Sun Stove)',
          analogyKhmer: 'ចម្អិនអាហារដោយពន្លឺព្រះអាទិត្យ!',
          analogyEng: 'Cooking food with sunlight energy!',
          analogyType: 'plants'
        }
      }
    ]
  },
  {
    id: 'english-g3-continuous',
    titleKhmer: 'ភាសាអង់គ្លេស៖ Present Continuous Actions',
    titleEng: 'English: Present Continuous Actions',
    grade: 3,
    subject: 'english',
    problemStatementKhmer: 'បំពេញចន្លោះក្នុងប្រយោគ៖ "Look! Sochea ___ (play) football in the school yard right now."',
    problemStatementEng: 'Fill in the blank: "Look! Sochea ___ (play) football in the school yard right now."',
    imageUri: 'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=600&auto=format&fit=crop&q=80',
    steps: [
      {
        id: 'cont-step-1',
        stepNumber: 1,
        totalSteps: 2,
        questionKhmer: 'សម្រាប់ប្រធានឯកវចនៈ Sochea (He) នៅក្នុង Present Continuous តើត្រូវប្រើ Verb to be មួយណា? (am, is, ឬ are?)',
        questionEng: 'For singular subject Sochea (He) in Present Continuous, which Verb to be do we use? (am, is, or are?)',
        inputFormat: 'mcq',
        options: ['is', 'are', 'am'],
        correctAnswer: 'is',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`សម្រាប់ប្រធានឯកវចនៈ Sochea (He...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`For singular subject Sochea (He) in Pres...'?'`,

        hint1: {
          khmer: 'He, She, It ឬឈ្មោះមនុស្សម្នាក់ (Sochea) ត្រូវប្រើ "is"!',
          eng: 'He, She, It, or one person name (Sochea) uses "is"!'
        },
        hint2: {
          khmer: 'Sochea + is!',
          eng: 'Sochea + is!'
        },
        hint3: {
          titleKhmer: 'វិធាន Verb to Be',
          titleEng: 'Verb to Be Rule',
          exampleKhmer: 'I am, He/She/Sochea is, They/We are',
          exampleEng: 'I am, He/She/Sochea is, They/We are'
        },
        explainDifferently: {
          simpleKhmer: 'សម្រាប់មិត្តម្នាក់ដូចជា សុជា យើងប្រើពាក្យ "is"!',
          simpleEng: 'For one friend like Sochea, we match with "is"!',
          analogyTitle: 'ការផ្គូផ្គង Verb to be (Matching is)',
          analogyKhmer: 'Sochea + is = Sochea is!',
          analogyEng: 'Sochea + is = Sochea is!',
          analogyType: 'apples'
        }
      },
      {
        id: 'cont-step-2',
        stepNumber: 2,
        totalSteps: 2,
        questionKhmer: 'តើកិរិយាស័ព្ទ play ត្រូវថែមអ្វីនៅខាងចុងដើម្បីបង្ហាញសកម្មភាពកំពុងធ្វើ? (playing, played, ឬ plays?)',
        questionEng: 'What ending do we add to "play" for present ongoing action? (playing, played, or plays?)',
        inputFormat: 'mcq',
        options: ['playing (-ing)', 'played (-ed)', 'plays (-s)'],
        correctAnswer: 'playing (-ing)',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`តើកិរិយាស័ព្ទ play ត្រូវថែមអ្វ...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`What ending do we add to "play" for pres...'?'`,

        hint1: {
          khmer: 'សកម្មភាពកំពុងកើតឡើងនៅពេលនេះ (right now) ត្រូវថែម -ing!',
          eng: 'Actions happening right now end with -ing!'
        },
        hint2: {
          khmer: 'play + ing = playing!',
          eng: 'play + ing = playing!'
        },
        hint3: {
          titleKhmer: 'វិធាន -ing',
          titleEng: '-ing Rule',
          exampleKhmer: 'is + verb + ing = is playing',
          exampleEng: 'is + verb + ing = is playing'
        },
        explainDifferently: {
          simpleKhmer: 'ពាក្យ -ing បង្ហាញថាសុជាកំពុងរត់លេងបាល់នៅពេលនេះ!',
          simpleEng: 'Adding -ing shows Sochea is playing right at this moment!',
          analogyTitle: 'សកម្មភាពកំពុងធ្វើ (Ongoing Action)',
          analogyKhmer: 'Sochea is playing football right now!',
          analogyEng: 'Sochea is playing football right now!',
          analogyType: 'apples'
        }
      }
    ]
  },
  {
    id: 'math-g4-fractions',
    titleKhmer: 'គណិតវិទ្យា៖ ការបូកប្រភាគភាគបែងដូចគ្នា',
    titleEng: 'Math: Adding Same Denominator Fractions',
    grade: 4,
    subject: 'math',
    problemStatementKhmer: 'សុខាបានញ៉ាំនំភីហ្សា ២/៨ ផ្ទាំង ហើយប្អូនស្រីរបស់គេញ៉ាំ ៣/៨ ផ្ទាំង។ តើអ្នកទាំងពីរញ៉ាំនំភីហ្សាសរុបស្មើនឹងភាគប៉ុន្មាននៃផ្ទាំង?',
    problemStatementEng: 'Sokha ate 2/8 of a pizza, and his sister ate 3/8. What fraction of the pizza did they eat in total?',
    imageUri: 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80',
    steps: [
      {
        id: 'frac-step-1',
        stepNumber: 1,
        totalSteps: 2,
        questionKhmer: 'ដោយសារភាគបែង (Denominator) ដូចគ្នាគឺ ៨ តើយើងត្រូវបូកតែភាគយក (Numerator) ឬបូកទាំងភាគបែង?',
        questionEng: 'Since denominators are equal (8), do we add only numerators (top numbers) or denominators too?',
        inputFormat: 'mcq',
        options: [
          'បូកតែភាគយកខាងលើ (២ + ៣) ហើយរក្សាភាគបែង ៨ ដដែល',
          'បូកទាំងភាគយក និងភាគបែង (២+៣)/(៨+៨)',
          'ដកភាគយក'
        ],
        correctAnswer: 'បូកតែភាគយកខាងលើ (២ + ៣) ហើយរក្សាភាគបែង ៨ ដដែល',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`ដោយសារភាគបែង (Denominator) ដូច...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`Since denominators are equal (8), do we ...'?'`,

        hint1: {
          khmer: 'វិធានបូកប្រភាគ៖ ពេលភាគបែងដូចគ្នា យើងបូកតែភាគយកខាងលើប៉ុណ្ណោះ!',
          eng: 'Fraction rule: When denominators are the same, add only top numbers!'
        },
        hint2: {
          khmer: 'ភាគបែង ៨ រក្សានៅដដែល!',
          eng: 'Denominator 8 stays the same!'
        },
        hint3: {
          titleKhmer: 'វិធានប្រភាគ',
          titleEng: 'Fraction Rule',
          exampleKhmer: 'a/c + b/c = (a + b) / c',
          exampleEng: 'a/c + b/c = (a + b) / c'
        },
        explainDifferently: {
          simpleKhmer: 'គិតពីចំណិតភីហ្សា៖ ភីហ្សាទាំងមូលចែកជា ៨ ចំណិត។ សុខា ២ ចំណិត + ប្អូន ៣ ចំណិត = ៥ ចំណិត នៃ ៨ ចំណិត!',
          simpleEng: 'Think of pizza slices: whole pizza has 8 slices. Sokha 2 slices + sister 3 slices = 5 slices out of 8!',
          analogyTitle: 'ចំណិតនំភីហ្សា (Pizza Slices)',
          analogyKhmer: '២ ចំណិត + ៣ ចំណិត = ៥ ចំណិតនៃភីហ្សា ៨ ចំណិត!',
          analogyEng: '2 slices + 3 slices = 5 slices of 8 total slices!',
          analogyType: 'pizza'
        }
      },
      {
        id: 'frac-step-2',
        stepNumber: 2,
        totalSteps: 2,
        questionKhmer: 'គណនា ២/៨ + ៣/៨ = ?',
        questionEng: 'Calculate 2/8 + 3/8 = ?',
        inputFormat: 'mcq',
        options: ['៥/៨ (5/8)', '៥/១៦ (5/16)', '១/៨ (1/8)'],
        correctAnswer: '៥/៨ (5/8)',
    socraticPromptKhmer: `តើអ្នកយល់ថាសំណួរ \`គណនា ២/៨ + ៣/៨ = ?...' ចាប់ផ្តើមដោយអ្វីជាដំបូង?'`,
    socraticPromptEng: `What do you think we need to find first for \`Calculate 2/8 + 3/8 = ?...'?'`,

        hint1: {
          khmer: 'ភាគយកខាងលើគឺ ២ + ៣ = ៥។ ភាគបែងខាងក្រោមគឺ ៨ ដដែល!',
          eng: 'Top number is 2 + 3 = 5. Bottom number stays 8!'
        },
        hint2: {
          khmer: 'ចម្លើយគឺ ៥/៨!',
          eng: 'The answer is 5/8!'
        },
        hint3: {
          titleKhmer: 'ចម្លើយចុងក្រោយ',
          titleEng: 'Final Fraction Answer',
          exampleKhmer: '២/៨ + ៣/៨ = ៥/៨',
          exampleEng: '2/8 + 3/8 = 5/8'
        },
        explainDifferently: {
          simpleKhmer: 'សរុបមក អ្នកទាំងពីរបានញ៉ាំនំភីហ្សា ៥/៨ ផ្ទាំង!',
          simpleEng: 'In total, they ate 5/8 of the pizza together!',
          analogyTitle: 'ភាគភីហ្សាសរុប (Total Pizza Fraction)',
          analogyKhmer: '៥ ភាគ ក្នុងចំណោម ៨ ភាគ!',
          analogyEng: '5 parts out of 8 parts!',
          analogyType: 'pizza'
        }
      }
    ]
  }
];

/**
 * Generates a realistic multi-turn scrollable chat history transcript for a given homework problem.
 * This allows students/parents to scroll down and view the full interactive learning session.
 */
export function generateHistoryChatForProblem(prob: HomeworkProblem, studentName: string): any[] {
  const displayName = studentName || 'សុជា';

  return [
    {
      id: `hist-1-${prob.id}`,
      sender: 'sayo',
      textKhmer: `សួស្តី ${displayName}! តោះដោះស្រាយលំហាត់ "${prob.titleKhmer}" ទាំងអស់គ្នា! ReanMoreនឹងជួយណែនាំអ្នកជាជំហានៗ។`,
      textEng: `Hi ${displayName}! Let's solve "${prob.titleEng}" together! ReanMore will guide you step-by-step.`,
      timestamp: '10:15 AM'
    },
    {
      id: `hist-2-${prob.id}`,
      sender: 'user',
      textKhmer: `ជំរាបសួរលោកគ្រូReanMore! ខ្ញុំបានអានចំណោទនេះហើយ ៖ "${prob.problemStatementKhmer}" ប៉ុន្តែខ្ញុំមិនទាន់ប្រាកដពីរបៀបចាប់ផ្តើមទេ! អាចជួយពន្យល់ខ្ញុំបន្តិចបានទេ?`,
      textEng: `Hello ReanMore! I read this question: "${prob.problemStatementEng}" but I'm not sure how to start! Can you help guide me?`,
      timestamp: '10:16 AM'
    },
    {
      id: `hist-3-${prob.id}`,
      sender: 'sayo',
      textKhmer: `ពូកែណាស់ ដែលហ៊ានសួរ! កុំបារម្ភអី យើងបំបែកចំណោទនេះជាជំហានតូចៗងាយៗ។ តោះពិនិត្យមើលជំហានដំបូងគេបង្អស់៖`,
      textEng: `Great job asking for guidance! Don't worry, we break this down into easy steps. Let's look at Step 1:`,
      timestamp: '10:16 AM'
    },
    {
      id: `hist-4-${prob.id}`,
      sender: 'user',
      textKhmer: `ចាស/បាទ! ខ្ញុំបានពិនិត្យមើលរូបភាព និងទិន្នន័យចំណោទរួចហើយ!`,
      textEng: `Yes! I checked the problem image and details carefully!`,
      timestamp: '10:17 AM'
    },
    {
      id: `hist-5-${prob.id}`,
      sender: 'sayo',
      textKhmer: `អស្ចារ្យណាស់! ឥឡូវសូមឆ្លើយសំណួរជំហានទី១ នៅលើប្រអប់អន្តរកម្មខាងក្រោមនេះ៖`,
      textEng: `Awesome! Now let me know your answer for Step 1 on the interactive card below:`,
      timestamp: '10:18 AM',
      problem: prob
    }
  ];
}

