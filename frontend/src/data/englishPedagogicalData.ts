/**
 * englishPedagogicalData.ts
 * Complete, kid-friendly English pedagogical dictionary for all Math & Science hardcoded cases (61 exercises).
 *
 * Designed specifically for early primary students (Grade 1 - 4):
 * 1. Simple, cheerful, age-appropriate language (ReanMore mascot voice).
 * 2. 1-to-1 step-aligned hints: Hint 1 (gentle clue), Hint 2 (strategy), Hint 3 (concrete example with emojis).
 * 3. Socratic guiding prompts that foster active thinking without spoiling the answer.
 * 4. Multi-modal support with kid-friendly multiple choice options and broad acceptable answer matching.
 */

export interface StepEnglishData {
  questionEng: string;
  socraticPromptEng: string;
  hint1Eng: string;
  hint2Eng: string;
  hint3Eng: string;
  explainEng?: string;
  analogyEng?: string;
  acceptableAnswers?: string[];
  options?: string[];
}

export interface CaseEnglishData {
  titleEng?: string;
  statementEng: string;
  hintsEng: string[];
  explainEng: {
    messageEng: string;
    questionEng: string;
  };
  steps: StepEnglishData[];
}

export const HARDCODED_ENGLISH_PEDAGOGY: Record<string, CaseEnglishData> = {
  // =========================================================================
  // MATH HOMEWORK 1 (Page 1) - Grade 1-2 Addition & Number Bonds
  // =========================================================================

  "math_p1_a1": {
    statementEng: "4 + 5 + 6 = ___",
    hintsEng: [
      "Add two friendly numbers together first, then add the third number.",
      "Look for numbers that can easily make a 10, or start with the biggest numbers.",
      "Example: 3 + 4 + 5 → (3 + 4 = 7), then 7 + 5 = 12! "
    ],
    explainEng: {
      messageEng: "You can group numbers in any order! 4 + 6 makes 10 quickly, and 10 + 5 makes 15!",
      questionEng: "Can you spot two numbers that add up to 10 first?"
    },
    steps: [
      {
        questionEng: "Let's start with the first two numbers. What is 4 + 5?",
        socraticPromptEng: "What do you get when you combine 4 and 5 together?",
        hint1Eng: "Start from the bigger number 5, then count on 4 more.",
        hint2Eng: "Hold 5 in your mind and tap 4 fingers forward: 6, 7, 8...",
        hint3Eng: "Think of 4 green apples  + 5 red apples  = 9 apples!",
        explainEng: "Adding from the larger number is fastest: 5 + 4 = 9.",
        analogyEng: "Picture 4 toy blocks and add 5 more blocks to build a stack of 9.",
        acceptableAnswers: ["9", "nine"]
      },
      {
        questionEng: "Awesome! Now we have 9. What should we do with the last number 6?",
        socraticPromptEng: "Which math action brings 9 and 6 together?",
        hint1Eng: "Look at the original problem 4 + 5 + 6: we have already added 4 and 5.",
        hint2Eng: "Take our sum 9 and add the remaining number 6 to it.",
        hint3Eng: "Example: If you have 7 and a leftover 3, you add them: 7 + 3.",
        explainEng: "We take the result from our first step and add the remaining number.",
        analogyEng: "We have 9 blocks in our tower, now we add 6 more on top.",
        acceptableAnswers: ["add 6", "add", "plus 6", "plus", "+ 6", "+6", "6"],
        options: ["Add 6 (+)", "Subtract 6 (-)", "Multiply by 6 (×)"]
      },
      {
        questionEng: "What is 9 + 6?",
        socraticPromptEng: "9 is almost 10! Can you take 1 from 6 to make 10, then add what is left?",
        hint1Eng: "9 only needs 1 more to become a friendly 10!",
        hint2Eng: "Borrow 1 from 6 to make 9 into 10. That leaves 5. Now think what 10 + 5 makes!",
        hint3Eng: "Similar example: 9 + 4 = 13 (because 9 + 1 = 10, and 10 + 3 = 13). So 9 + 6 = 15!",
        explainEng: "Making 10 makes adding easy: 9 + 1 = 10, and 10 + 5 = 15.",
        analogyEng: "A 10-egg carton has 9 eggs. Put 1 egg in from your 6 eggs to fill it, leaving 5 outside: 10 + 5 = 15!",
        acceptableAnswers: ["15", "fifteen"]
      }
    ]
  },

  "math_p1_a2": {
    statementEng: "7 + 3 + 2 + 5 = ___",
    hintsEng: [
      "Search for number pairs that add up to 10 first!",
      "Combine the remaining numbers, then add them to 10.",
      "Example: 6 + 4 + 3 + 5 → (6+4=10) and (3+5=8) → 10+8 = 18! "
    ],
    explainEng: {
      messageEng: "Making groups of 10 makes long addition fast and super fun!",
      questionEng: "Isn't adding 10 to any number much easier than counting from 1?"
    },
    steps: [
      {
        questionEng: "Which two numbers from 7, 3, 2, and 5 make 10 when added together?",
        socraticPromptEng: "Look for two numbers that are '10-buddies'!",
        hint1Eng: "Start with 7: how many more fingers do you need to make 10?",
        hint2Eng: "Hold up 7 fingers. How many fingers are tucked down?",
        hint3Eng: "10-pairs to remember: 8 + 2 = 10, 9 + 1 = 10, and 7 + 3 = 10!",
        explainEng: "7 and 3 make 10. Spotting 10-pairs is a secret math superpower!",
        analogyEng: "7 and 3 are like puzzle pieces that click together to form a shiny 10.",
        acceptableAnswers: ["7 and 3", "3 and 7", "7, 3", "3, 7", "7 3", "3 7", "7+3", "3+7"]
      },
      {
        questionEng: "After pairing 7 and 3 to make 10, which two numbers are left?",
        socraticPromptEng: "Cross out 7 and 3. What numbers are still waiting to be added?",
        hint1Eng: "Look at the problem: 7 + 3 + 2 + 5. Take away 7 and 3.",
        hint2Eng: "Find the two numbers sitting between the last plus sign.",
        hint3Eng: "Example: In 6 + 4 + 1 + 3, after using 6 and 4, the leftover numbers are 1 and 3.",
        explainEng: "Keep track of what you used: 7 and 3 are in the 10-group, so 2 and 5 are left.",
        analogyEng: "Two friends joined the 10-club, and two friends (2 and 5) are next in line!",
        acceptableAnswers: ["2 and 5", "5 and 2", "2, 5", "5, 2", "2 5", "5 2", "2+5", "5+2"]
      },
      {
        questionEng: "What is 2 + 5?",
        socraticPromptEng: "Start with 5 and count on 2 more!",
        hint1Eng: "Start with the bigger number 5 and add 2.",
        hint2Eng: "Count 2 forward from 5: 6...",
        hint3Eng: "Example: 2 + 4 = 6, so 2 + 5 is 1 more: 7! ",
        explainEng: "5 + 2 is simple: jump 2 steps past 5 to reach 7.",
        analogyEng: "A bunny sits on step 5 and hops forward 2 steps to step 7.",
        acceptableAnswers: ["7", "seven"]
      },
      {
        questionEng: "Now combine our 10-group with the 7. What is 10 + 7?",
        socraticPromptEng: "What do you get when you put 1 ten and 7 ones together?",
        hint1Eng: "Add our 10-group and our 7.",
        hint2Eng: "Combine 1 ten and 7 ones to find the teen number.",
        hint3Eng: "Example: 10 + 4 = 14, 10 + 5 = 15, so 10 + 7 = 17!",
        explainEng: "One ten (10) and seven ones (7) makes 17.",
        analogyEng: "A box of 10 crayons plus 7 single crayons equals 17 crayons!",
        acceptableAnswers: ["17", "seventeen"]
      }
    ]
  },

  "math_p1_a3": {
    statementEng: "8 + 1 + 4 = ___",
    hintsEng: [
      "Add 8 + 1 first, then add the remaining number.",
      "Adding 1 just means moving to the very next counting number!",
      "Example: 7 + 1 + 3 → 8 + 3 = 11! "
    ],
    explainEng: {
      messageEng: "You can also think: 8 needs 2 from 4 to make 10, leaving 2 + 1 = 3, so 10 + 3 = 13!",
      questionEng: "Can you see how close 8 is to 10?"
    },
    steps: [
      {
        questionEng: "What is 8 + 1?",
        socraticPromptEng: "What is the next counting number right after 8?",
        hint1Eng: "Adding 1 is just one step forward from 8.",
        hint2Eng: "Count: 7, 8...",
        hint3Eng: "Example: 5 + 1 = 6, 6 + 1 = 7, so 8 + 1 = 9.",
        explainEng: "Any number plus 1 gives the next counting number: 8 + 1 = 9.",
        analogyEng: "If you have 8 coins and find 1 more, you now have 9 coins.",
        acceptableAnswers: ["9", "nine"]
      },
      {
        questionEng: "Now add the remaining 4. What is 9 + 4?",
        socraticPromptEng: "9 is 1 away from 10! What is 10 + 3?",
        hint1Eng: "Start at 9 and count 4 steps forward.",
        hint2Eng: "Take 1 from 4 to make 9 into 10. That leaves 3. Now add 10 and 3!",
        hint3Eng: "Example: 9 + 3 = 12, so 9 + 4 is one more: 13.",
        explainEng: "9 + 1 = 10, plus 3 remaining = 13.",
        analogyEng: "Hop 4 steps forward from 9 on your number line: 10, 11, 12, 13!",
        acceptableAnswers: ["13", "thirteen"]
      }
    ]
  },

  "math_p1_a4": {
    statementEng: "9 + 2 + 3 + 1 = ___",
    hintsEng: [
      "Look for a pair of numbers that makes 10 first!",
      "9 needs only 1 more to make 10.",
      "Example: 9 + 1 = 10, and 2 + 3 = 5, so 10 + 5 = 15! "
    ],
    explainEng: {
      messageEng: "Pairing 9 and 1 makes 10 right away. Then 2 + 3 = 5, making the grand total 15!",
      questionEng: "Which pair did you find first?"
    },
    steps: [
      {
        questionEng: "Which two numbers can you pair up to make 10?",
        socraticPromptEng: "9 is almost 10! Which number should it buddy up with?",
        hint1Eng: "9 needs only 1 more to reach 10.",
        hint2Eng: "Look at the numbers: 9, 2, 3, 1. Pair 9 with the smallest number.",
        hint3Eng: "10-pair rule: 9 + 1 = 10!",
        explainEng: "9 + 1 = 10 is the quickest pair to spot.",
        analogyEng: "9 friends welcome 1 more friend to complete a soccer team of 10!",
        acceptableAnswers: ["9 and 1", "1 and 9", "9, 1", "1, 9", "9 1", "1 9", "9+1", "1+9"]
      },
      {
        questionEng: "What two numbers are left over to add?",
        socraticPromptEng: "We used 9 and 1. Which two numbers are still waiting?",
        hint1Eng: "Look at the middle of 9 + 2 + 3 + 1.",
        hint2Eng: "Find the two numbers between 9 and 1.",
        hint3Eng: "Example: If 9 and 1 are in the 10-box, 2 and 3 are outside.",
        explainEng: "The unused numbers are 2 and 3.",
        analogyEng: "2 puppies and 3 kittens are waiting to play!",
        acceptableAnswers: ["2 and 3", "3 and 2", "2, 3", "3, 2", "2 3", "3 2", "2+3", "3+2"]
      },
      {
        questionEng: "What is 2 + 3?",
        socraticPromptEng: "Add the two leftover numbers: 2 + 3.",
        hint1Eng: "Start with 3 and count 2 more.",
        hint2Eng: "Count: 3... 4...",
        hint3Eng: "Example: 2 fingers on one hand + 3 on the other = 5 fingers!",
        explainEng: "2 + 3 = 5.",
        analogyEng: "2 red marbles + 3 blue marbles = 5 marbles total.",
        acceptableAnswers: ["5", "five"]
      },
      {
        questionEng: "Now combine our 10-group and 5. What is 10 + 5?",
        socraticPromptEng: "What do you get when you put 10 and 5 together?",
        hint1Eng: "Add 10 and 5.",
        hint2Eng: "Think of 1 ten and 5 ones.",
        hint3Eng: "Example: 10 + 4 = 14, so 10 + 5 = 15!",
        explainEng: "10 + 5 = 15.",
        analogyEng: "A full 10-pack of cookies plus 5 loose cookies = 15 cookies!",
        acceptableAnswers: ["15", "fifteen"]
      }
    ]
  },

  "math_p1_a5": {
    statementEng: "6 + 6 + 4 = ___",
    hintsEng: [
      "You can make 10 with 6 + 4, or double 6 to get 12 first!",
      "Look for friends of 10: 6 + 4 = 10.",
      "Example: (6 + 4 = 10) + 6 = 16! "
    ],
    explainEng: {
      messageEng: "6 + 4 makes 10 right away, and adding the other 6 makes 16!",
      questionEng: "Did you spot the 6 and 4 pair that makes 10?"
    },
    steps: [
      {
        questionEng: "What is 6 + 4?",
        socraticPromptEng: "Can you combine 6 and 4 to make a friendly 10?",
        hint1Eng: "Start with 6 and count 4 more.",
        hint2Eng: "6 + 4 makes a clean, full group of ten!",
        hint3Eng: "Hold up 6 fingers. Raise 4 more to make all 10 fingers!",
        explainEng: "6 and 4 are number partners that make 10.",
        analogyEng: "6 apples in a basket + 4 more apples fills the 10-apple basket!",
        acceptableAnswers: ["10", "ten"]
      },
      {
        questionEng: "Which number is left over from 6 + 6 + 4?",
        socraticPromptEng: "We paired one 6 with the 4. Which number is still waiting?",
        hint1Eng: "Look back at 6 + 6 + 4.",
        hint2Eng: "We used one 6 and the 4. What number did we not touch yet?",
        hint3Eng: "Example: In a pair of twin 6s, one is used and one remains.",
        explainEng: "The remaining number is 6.",
        analogyEng: "One twin 6 went into the 10-house, the other twin 6 is knocking on the door!",
        acceptableAnswers: ["6", "six"]
      },
      {
        questionEng: "Now add 10 and 6. What is 10 + 6?",
        socraticPromptEng: "What is 1 ten and 6 ones together?",
        hint1Eng: "Add 10 and 6.",
        hint2Eng: "Think of 1 ten and 6 ones to name the teen number.",
        hint3Eng: "Example: 10 + 5 = 15, so 10 + 6 = 16!",
        explainEng: "1 ten + 6 ones = 16.",
        analogyEng: "10 stars in the sky + 6 more twinkle = 16 stars!",
        acceptableAnswers: ["16", "sixteen"]
      }
    ]
  },

  // =========================================================================
  // MATH HOMEWORK 1 (Part B: Bonds to 100)
  // =========================================================================

  "math_p1_b1": {
    statementEng: "30 + [ ] = 100",
    hintsEng: [
      "Think about counting by tens from 30 to 100.",
      "How many tens do you need to add to 3 tens to make 10 tens?",
      "Example: 3 tens + 7 tens = 10 tens (100), so the answer is 70! "
    ],
    explainEng: {
      messageEng: "100 is 10 tens. Since you already have 3 tens (30), you need 7 more tens, which is 70!",
      questionEng: "How many tens are in 100?"
    },
    steps: [
      {
        questionEng: "What target number are we trying to reach?",
        socraticPromptEng: "Look at the right side of the equals sign: 30 + [ ] = ?",
        hint1Eng: "Look at the number at the end of the equation.",
        hint2Eng: "It is the three-digit number after the equals sign.",
        hint3Eng: "Example: In 20 + [ ] = 100, the target is 100.",
        explainEng: "The goal of this number bond is to reach 100.",
        analogyEng: "Imagine a 100-meter race track!",
        acceptableAnswers: ["100", "hundred", "one hundred"]
      },
      {
        questionEng: "Start at 30 and count by tens toward 100 (40, 50, 60...). How many tens do you need?",
        socraticPromptEng: "You have 3 tens. How many more tens make 10 tens?",
        hint1Eng: "Count on your fingers by tens: 40, 50, 60, 70, 80, 90, 100.",
        hint2Eng: "Look at how many fingers you raised while counting up to 100.",
        hint3Eng: "Think: 3 + ? = 10. Since 3 + 7 = 10, 3 tens + 7 tens = 10 tens.",
        explainEng: "3 tens + 7 tens = 10 tens (100).",
        analogyEng: "A jar holds 10 rolls of coins. 3 rolls are inside, so you need 7 more rolls.",
        acceptableAnswers: ["7 tens", "7", "70"]
      },
      {
        questionEng: "What number is 7 tens?",
        socraticPromptEng: "Count 7 groups of 10: 10, 20, 30, 40, 50, 60, 70!",
        hint1Eng: "7 groups of 10 has a name ending in '-ty'.",
        hint2Eng: "Write a 7 with a 0 at the end.",
        hint3Eng: "Example: 5 tens = 50, 6 tens = 60, so 7 tens = 70!",
        explainEng: "7 tens is written as 70.",
        analogyEng: "7 ten-dollar bills equal 70 dollars!",
        acceptableAnswers: ["70", "seventy"]
      }
    ]
  },

  "math_p1_b2": {
    statementEng: "20 + [ ] = 100",
    hintsEng: [
      "Count up by tens from 20 to 100.",
      "2 tens plus how many tens make 10 tens?",
      "Example: 20 + 80 = 100! "
    ],
    explainEng: {
      messageEng: "100 is 10 tens. If you already have 2 tens (20), you need 8 more tens (80)!",
      questionEng: "Can you count backward from 100 by 20?"
    },
    steps: [
      {
        questionEng: "What is our target number?",
        socraticPromptEng: "What number is after the equals sign?",
        hint1Eng: "Look at the final number after the equals sign.",
        hint2Eng: "It is the three-digit century number.",
        hint3Eng: "Target: 100.",
        explainEng: "The target total is 100.",
        analogyEng: "We are trying to fill a 100-piece puzzle!",
        acceptableAnswers: ["100", "hundred", "one hundred"]
      },
      {
        questionEng: "How many tens are there from 20 to 100?",
        socraticPromptEng: "Think: 2 + ? = 10. How many tens do we need?",
        hint1Eng: "Count by tens from 20: 30, 40, 50, 60, 70, 80, 90, 100.",
        hint2Eng: "Check how many jumps of ten you took.",
        hint3Eng: "2 tens + 8 tens = 10 tens (100).",
        explainEng: "It takes 8 tens to go from 20 to 100.",
        analogyEng: "Take 8 giant steps of 10 on the playground!",
        acceptableAnswers: ["8 tens", "8", "80"]
      },
      {
        questionEng: "What number is 8 tens?",
        socraticPromptEng: "Write 8 groups of ten as a number.",
        hint1Eng: "8 tens is written with an 8 and a 0.",
        hint2Eng: "Think of the number that means 8 tens.",
        hint3Eng: "Example: 7 tens = 70, so 8 tens = 80!",
        explainEng: "8 tens = 80.",
        analogyEng: "8 dimes (each worth 10 cents) equal 80 cents!",
        acceptableAnswers: ["80", "eighty"]
      }
    ]
  },

  "math_p1_b3": {
    statementEng: "35 + [ ] = 100",
    hintsEng: [
      "Jump to the nearest ten first: 35 + 5 = 40.",
      "Then jump from 40 to 100: 40 + 60 = 100.",
      "Add the two jumps together: 5 + 60 = 65! "
    ],
    explainEng: {
      messageEng: "Using friendly jumps makes missing numbers easy: 5 jumps to 40, and 60 jumps to 100. 5 + 60 = 65!",
      questionEng: "What jump do you make first to reach a multiple of 10?"
    },
    steps: [
      {
        questionEng: "How much does 35 need to reach the next friendly ten (40)?",
        socraticPromptEng: "Look at the 5 in 35. How many more make 10?",
        hint1Eng: "Count up from 35 to 40: 36, 37, 38, 39...",
        hint2Eng: "5 plus what number makes 10?",
        hint3Eng: "That small jump is 5 (35 + 5 = 40).",
        explainEng: "35 needs 5 to reach the round number 40.",
        analogyEng: "A frog takes 5 tiny hops to reach lily pad 40.",
        acceptableAnswers: ["5", "five"]
      },
      {
        questionEng: "After reaching 40, how much more is needed to reach 100?",
        socraticPromptEng: "Now count by tens from 40 to 100: 50, 60, 70, 80, 90, 100.",
        hint1Eng: "From 40 to 100 is 6 tens.",
        hint2Eng: "Think: 4 tens + how many tens makes 10 tens?",
        hint3Eng: "Think: 4 + 6 = 10, so 40 + 60 = 100.",
        explainEng: "40 needs 60 to reach 100.",
        analogyEng: "The frog takes a big leap of 60 to reach the end of the pond!",
        acceptableAnswers: ["60", "sixty", "6 tens"]
      },
      {
        questionEng: "Combine those two jumps: what is 5 + 60?",
        socraticPromptEng: "Add your small jump of 5 and your big jump of 60.",
        hint1Eng: "Put 60 and 5 together.",
        hint2Eng: "Combine 6 tens with 5 ones to find the total.",
        hint3Eng: "Example: 50 + 5 = 55, so 60 + 5 = 65!",
        explainEng: "The total missing number is 5 + 60 = 65.",
        analogyEng: "Combine 5 small steps and 60 big steps to get 65 steps total!",
        acceptableAnswers: ["65", "sixty-five", "sixty five"]
      }
    ]
  },

  "math_p1_b4": {
    statementEng: "48 + [ ] = 100",
    hintsEng: [
      "Jump from 48 to 50 first: that is 2.",
      "Then jump from 50 to 100: that is 50.",
      "Combine your jumps: 2 + 50 = 52! "
    ],
    explainEng: {
      messageEng: "48 + 2 = 50, and 50 + 50 = 100. Adding 2 and 50 gives 52!",
      questionEng: "Can you see how 50 is halfway to 100?"
    },
    steps: [
      {
        questionEng: "How much does 48 need to reach the friendly ten 50?",
        socraticPromptEng: "Count up from 48 to 50. How many steps is that?",
        hint1Eng: "Count: 48... 49...",
        hint2Eng: "Think: 8 + what makes 10?",
        hint3Eng: "48 needs 2 to reach 50.",
        explainEng: "48 is only 2 away from 50.",
        analogyEng: "You need 2 more stickers to complete page 50 of your album!",
        acceptableAnswers: ["2", "two"]
      },
      {
        questionEng: "From 50, how much more is needed to reach 100?",
        socraticPromptEng: "50 is half of 100! What is the other half?",
        hint1Eng: "Count by tens from 50 to 100: 60, 70, 80, 90...",
        hint2Eng: "Think what number you add to 50 to make 100.",
        hint3Eng: "50 + 50 = 100.",
        explainEng: "50 is exactly halfway to 100.",
        analogyEng: "Half a pizza has 50 pepperonis, the other half has 50 too!",
        acceptableAnswers: ["50", "fifty", "5 tens"]
      },
      {
        questionEng: "Now add both jumps together: what is 2 + 50?",
        socraticPromptEng: "Combine your jump of 2 and your jump of 50.",
        hint1Eng: "Add 50 and 2.",
        hint2Eng: "Combine 5 tens with 2 ones.",
        hint3Eng: "Example: 50 + 1 = 51, so 50 + 2 = 52!",
        explainEng: "2 + 50 = 52, which is our missing number.",
        analogyEng: "50 big steps plus 2 baby steps = 52 steps!",
        acceptableAnswers: ["52", "fifty-two", "fifty two"]
      }
    ]
  },

  "math_p1_b5": {
    statementEng: "67 + [ ] = 100",
    hintsEng: [
      "Jump from 67 to 70: that is 3.",
      "Jump from 70 to 100: that is 30.",
      "Combine the jumps: 3 + 30 = 33! "
    ],
    explainEng: {
      messageEng: "67 + 3 = 70, and 70 + 30 = 100. Put 3 and 30 together to get 33!",
      questionEng: "How much did you add to 67 to reach 70?"
    },
    steps: [
      {
        questionEng: "How much does 67 need to reach the friendly ten 70?",
        socraticPromptEng: "Look at the 7 in 67. How many more make 10?",
        hint1Eng: "Count up from 67 to 70: 68, 69...",
        hint2Eng: "7 + what number makes 10?",
        hint3Eng: "67 needs 3 to reach 70.",
        explainEng: "67 needs 3 to reach 70.",
        analogyEng: "Hop 3 steps forward to land on stone 70.",
        acceptableAnswers: ["3", "three"]
      },
      {
        questionEng: "From 70, how much is needed to reach 100?",
        socraticPromptEng: "Count by tens from 70 to 100: 80, 90, 100.",
        hint1Eng: "From 70 to 100 is 3 tens.",
        hint2Eng: "Think how many tens go from 7 tens to 10 tens.",
        hint3Eng: "Think: 7 + 3 = 10, so 70 + 30 = 100.",
        explainEng: "70 needs 30 to reach 100.",
        analogyEng: "A 30-meter dash takes you from marker 70 to the 100 finish line!",
        acceptableAnswers: ["30", "thirty", "3 tens"]
      },
      {
        questionEng: "Combine both jumps: what is 3 + 30?",
        socraticPromptEng: "Put 30 and 3 together.",
        hint1Eng: "Add 30 and 3.",
        hint2Eng: "Combine 3 tens with 3 ones.",
        hint3Eng: "Example: 3 tens and 3 ones is thirty-three (33).",
        explainEng: "3 + 30 = 33, our missing number!",
        analogyEng: "30 large blocks + 3 small blocks = 33 blocks!",
        acceptableAnswers: ["33", "thirty-three", "thirty three"]
      }
    ]
  },

  "math_p1_b6": {
    statementEng: "54 + [ ] = 100",
    hintsEng: [
      "Jump from 54 to 60: that is 6.",
      "Jump from 60 to 100: that is 40.",
      "Combine the jumps: 6 + 40 = 46! "
    ],
    explainEng: {
      messageEng: "54 + 6 = 60, and 60 + 40 = 100. 6 + 40 = 46!",
      questionEng: "What is 100 minus 60?"
    },
    steps: [
      {
        questionEng: "How much does 54 need to reach the friendly ten 60?",
        socraticPromptEng: "Think: 4 + ? = 10. How many more does 54 need?",
        hint1Eng: "Count up from 54 to 60: 55, 56, 57, 58, 59...",
        hint2Eng: "Think: 4 ones plus how many ones makes a full 10?",
        hint3Eng: "54 needs 6 to reach 60 (54 + 6 = 60).",
        explainEng: "54 needs 6 to reach 60.",
        analogyEng: "6 more petals make a complete flower of 60!",
        acceptableAnswers: ["6", "six"]
      },
      {
        questionEng: "From 60, how much is needed to reach 100?",
        socraticPromptEng: "Count by tens from 60 to 100: 70, 80, 90, 100.",
        hint1Eng: "From 60 to 100 is 4 tens.",
        hint2Eng: "Think how many tens are between 6 tens and 10 tens.",
        hint3Eng: "Think: 6 + 4 = 10, so 60 + 40 = 100.",
        explainEng: "60 needs 40 to reach 100.",
        analogyEng: "A 40-step staircase takes you up to floor 100!",
        acceptableAnswers: ["40", "forty", "4 tens"]
      },
      {
        questionEng: "Combine both jumps: what is 6 + 40?",
        socraticPromptEng: "Put 40 and 6 together.",
        hint1Eng: "Add 40 and 6.",
        hint2Eng: "Combine 4 tens with 6 ones.",
        hint3Eng: "Example: 4 tens and 6 ones = 46!",
        explainEng: "6 + 40 = 46.",
        analogyEng: "40 blue beads + 6 yellow beads = 46 beads total.",
        acceptableAnswers: ["46", "forty-six", "forty six"]
      }
    ]
  },

  // =========================================================================
  // MATH HOMEWORK 8 (Page 8) - Place Value & Mental Arithmetic
  // =========================================================================

  "math_p8_a1": {
    statementEng: "Write the hundreds, tens, and ones. Then write 10 more and 10 less: 146",
    hintsEng: [
      "Read digits from left to right: hundreds, tens, ones.",
      "Adding or subtracting 10 changes the tens place!",
      "Example: For 146, hundreds is 1, tens is 4, ones is 6. 10 more is 156, 10 less is 136! "
    ],
    explainEng: {
      messageEng: "146 has 1 hundred, 4 tens, and 6 ones. Adding 1 ten makes 156, and taking away 1 ten makes 136.",
      questionEng: "Which digit changes when you add 10?"
    },
    steps: [
      {
        questionEng: "In 146, what digit is in the hundreds place?",
        socraticPromptEng: "Look at the first digit on the left in 146.",
        hint1Eng: "Hundreds is the first digit on the left in a 3-digit number.",
        hint2Eng: "Look at the leftmost digit in 146.",
        hint3Eng: "Example: In 245, hundreds is 2. In 146, hundreds is 1.",
        explainEng: "The hundreds digit is 1, representing 100.",
        analogyEng: "1 big flat tray holding 100 cookies.",
        acceptableAnswers: ["1", "one"]
      },
      {
        questionEng: "What digit is in the tens place?",
        socraticPromptEng: "Look at the middle digit of 146.",
        hint1Eng: "The tens digit is in the middle.",
        hint2Eng: "Find the digit between the hundreds and ones.",
        hint3Eng: "Example: 4 tens means 40. Tens digit is 4.",
        explainEng: "The tens digit is 4, representing 40.",
        analogyEng: "4 stacks of 10 cookies.",
        acceptableAnswers: ["4", "four"]
      },
      {
        questionEng: "What digit is in the ones place?",
        socraticPromptEng: "Look at the last digit on the right in 146.",
        hint1Eng: "The ones digit is on the far right.",
        hint2Eng: "Find the very last digit in 146.",
        hint3Eng: "Example: 6 single units. Ones digit is 6.",
        explainEng: "The ones digit is 6.",
        analogyEng: "6 single cookies on a plate.",
        acceptableAnswers: ["6", "six"]
      },
      {
        questionEng: "What is 10 more than 146? (Add 1 ten)",
        socraticPromptEng: "Increase the tens digit 4 by 1. What number do you get?",
        hint1Eng: "Only the tens digit changes: 4 tens becomes 5 tens.",
        hint2Eng: "Add 10 to 146: keep the hundreds and ones, increase the tens.",
        hint3Eng: "Hundreds stays 1, ones stays 6, tens becomes 5: 156!",
        explainEng: "Adding 10 increases the tens place by 1: 146 → 156.",
        analogyEng: "Add 1 stack of 10 cookies to your 4 stacks, making 5 stacks: 156 total!",
        acceptableAnswers: ["156", "tens", "the tens digit", "tens digit"]
      },
      {
        questionEng: "What is 10 less than 146? (Take away 1 ten)",
        socraticPromptEng: "Decrease the tens digit 4 by 1. What number do you get?",
        hint1Eng: "Only the tens digit changes: 4 tens minus 1 ten is 3 tens.",
        hint2Eng: "Subtract 10 from 146: keep hundreds and ones, reduce the tens.",
        hint3Eng: "Hundreds stays 1, ones stays 6, tens becomes 3: 136!",
        explainEng: "Subtracting 10 decreases the tens place by 1: 146 → 136.",
        analogyEng: "Eat 1 stack of 10 cookies, leaving 3 stacks: 136 total!",
        acceptableAnswers: ["136", "tens", "the tens digit", "tens digit"]
      }
    ]
  },

  "math_p8_a2": {
    statementEng: "Write the hundreds, tens, and ones. Then write 10 more and 10 less: 308",
    hintsEng: [
      "In 308, 0 means there are zero tens.",
      "10 more than 308 is 318. 10 less than 308 is 298!",
      "Example: 300 + 8 = 308. Adding 10 makes 318! "
    ],
    explainEng: {
      messageEng: "When adding 10 to 308, the 0 tens becomes 1 ten: 318. When subtracting 10 from 308, we borrow from 300 to get 298!",
      questionEng: "What happens when 0 tens increases by 1 ten?"
    },
    steps: [
      {
        questionEng: "In 308, which digit is in the hundreds place?",
        socraticPromptEng: "Look at the first digit on the left in 308.",
        hint1Eng: "The hundreds digit is on the left.",
        hint2Eng: "Find the first digit in 308.",
        hint3Eng: "3 represents 300.",
        explainEng: "The hundreds digit is 3.",
        analogyEng: "3 giant boxes of 100 marbles each.",
        acceptableAnswers: ["3", "three"]
      },
      {
        questionEng: "Which digit is in the tens place?",
        socraticPromptEng: "Look at the middle digit of 308.",
        hint1Eng: "The tens digit is in the middle.",
        hint2Eng: "Look at the digit between 3 and 8.",
        hint3Eng: "0 means there are zero groups of ten.",
        explainEng: "The tens digit is 0.",
        analogyEng: "An empty bag holding 0 tens.",
        acceptableAnswers: ["0", "zero"]
      },
      {
        questionEng: "Which digit is in the ones place?",
        socraticPromptEng: "Look at the last digit on the right in 308.",
        hint1Eng: "The ones digit is on the far right.",
        hint2Eng: "Look at the last digit in 308.",
        hint3Eng: "8 represents 8 single units.",
        explainEng: "The ones digit is 8.",
        analogyEng: "8 shiny marbles on the table.",
        acceptableAnswers: ["8", "eight"]
      },
      {
        questionEng: "What is 10 more than 308? (Add 1 ten)",
        socraticPromptEng: "Increase the tens digit 0 by 1. What number do you get?",
        hint1Eng: "0 tens + 1 ten = 1 ten.",
        hint2Eng: "Increase the middle tens digit from 0 to 1.",
        hint3Eng: "Hundreds stays 3, tens becomes 1, ones stays 8: 318!",
        explainEng: "Adding 10 gives 318.",
        analogyEng: "Add 1 bag of 10 marbles to your 300 marbles: 318!",
        acceptableAnswers: ["318", "tens", "the tens place increases by 1"]
      },
      {
        questionEng: "What is 10 less than 308? (Take away 1 ten)",
        socraticPromptEng: "Count backward 10 from 308: 308 - 10 = ?",
        hint1Eng: "Think: 300 - 10 = 290. Now add the 8 ones back.",
        hint2Eng: "Step back 10 from 308 into the two-hundreds.",
        hint3Eng: "308 - 10 = 298!",
        explainEng: "Subtracting 10 from 308 gives 298.",
        analogyEng: "Step back 10 steps on the number line to 298.",
        acceptableAnswers: ["298", "tens", "the number decreases by 10"]
      }
    ]
  },

  "math_p8_a3": {
    statementEng: "Write the hundreds, tens, and ones. Then write 10 more and 10 less: 235",
    hintsEng: [
      "235 = 2 hundreds, 3 tens, and 5 ones.",
      "10 more is 245. 10 less is 225!",
      "Example: 3 tens + 1 ten = 4 tens (245). 3 tens - 1 ten = 2 tens (225)! "
    ],
    explainEng: {
      messageEng: "In 235, adding 10 changes 3 tens to 4 tens (245). Taking away 10 changes 3 tens to 2 tens (225).",
      questionEng: "Do the hundreds or ones change when you add or subtract 10?"
    },
    steps: [
      {
        questionEng: "What digit is in the hundreds place of 235?",
        socraticPromptEng: "Look at the left digit of 235.",
        hint1Eng: "The first digit on the left is the hundreds place.",
        hint2Eng: "Find the leftmost digit in 235.",
        hint3Eng: "2 hundreds = 200.",
        explainEng: "The hundreds digit is 2.",
        analogyEng: "2 treasure chests of 100 gold coins each.",
        acceptableAnswers: ["2", "two"]
      },
      {
        questionEng: "What digit is in the tens place?",
        socraticPromptEng: "Look at the middle digit of 235.",
        hint1Eng: "The middle digit is the tens place.",
        hint2Eng: "Look at the digit between 2 and 5.",
        hint3Eng: "3 tens = 30.",
        explainEng: "The tens digit is 3.",
        analogyEng: "3 coin bags of 10 coins each.",
        acceptableAnswers: ["3", "three"]
      },
      {
        questionEng: "What digit is in the ones place?",
        socraticPromptEng: "Look at the rightmost digit of 235.",
        hint1Eng: "The ones digit is on the right.",
        hint2Eng: "Find the last digit in 235.",
        hint3Eng: "5 single units.",
        explainEng: "The ones digit is 5.",
        analogyEng: "5 loose gold coins in your hand.",
        acceptableAnswers: ["5", "five"]
      },
      {
        questionEng: "What is 10 more than 235? (Add 1 ten)",
        socraticPromptEng: "Increase the tens digit 3 by 1.",
        hint1Eng: "3 tens + 1 ten = 4 tens.",
        hint2Eng: "Increase the middle digit from 3 to 4.",
        hint3Eng: "Hundreds stays 2, tens becomes 4, ones stays 5: 245!",
        explainEng: "Adding 10 makes 245.",
        analogyEng: "Collect 1 more bag of 10 coins to have 245 coins!",
        acceptableAnswers: ["245", "tens", "the tens digit increases by 1"]
      },
      {
        questionEng: "What is 10 less than 235? (Take away 1 ten)",
        socraticPromptEng: "Decrease the tens digit 3 by 1.",
        hint1Eng: "3 tens - 1 ten = 2 tens.",
        hint2Eng: "Decrease the middle digit from 3 to 2.",
        hint3Eng: "Hundreds stays 2, tens becomes 2, ones stays 5: 225!",
        explainEng: "Subtracting 10 makes 225.",
        analogyEng: "Give away 1 bag of 10 coins, leaving 225 coins!",
        acceptableAnswers: ["225", "tens", "the tens digit decreases by 1"]
      }
    ]
  },

  "math_p8_a4": {
    statementEng: "Write the hundreds, tens, and ones. Then write 10 more and 10 less: 472",
    hintsEng: [
      "472 = 4 hundreds, 7 tens, and 2 ones.",
      "10 more is 482. 10 less is 462!",
      "Example: 7 tens + 1 ten = 8 tens (482). 7 tens - 1 ten = 6 tens (462)! "
    ],
    explainEng: {
      messageEng: "In 472, the tens digit is 7. 10 more increases 7 tens to 8 tens (482), and 10 less decreases it to 6 tens (462).",
      questionEng: "Which place value changes when you add 10?"
    },
    steps: [
      {
        questionEng: "Which digit represents the hundreds in 472?",
        socraticPromptEng: "Look at the first digit on the left in 472.",
        hint1Eng: "Hundreds is the first digit on the left.",
        hint2Eng: "Find the leftmost digit in 472.",
        hint3Eng: "4 represents 400.",
        explainEng: "The hundreds digit is 4.",
        analogyEng: "4 big packs of 100 stickers each.",
        acceptableAnswers: ["4", "four"]
      },
      {
        questionEng: "Which digit represents the tens in 472?",
        socraticPromptEng: "Look at the middle digit of 472.",
        hint1Eng: "Tens is the middle digit.",
        hint2Eng: "Look at the digit between 4 and 2.",
        hint3Eng: "7 represents 70.",
        explainEng: "The tens digit is 7.",
        analogyEng: "7 sheets of 10 stickers each.",
        acceptableAnswers: ["7", "seven"]
      },
      {
        questionEng: "Which digit represents the ones in 472?",
        socraticPromptEng: "Look at the rightmost digit of 472.",
        hint1Eng: "Ones is the digit on the far right.",
        hint2Eng: "Look at the final digit in 472.",
        hint3Eng: "2 represents 2 single stickers.",
        explainEng: "The ones digit is 2.",
        analogyEng: "2 single stickers.",
        acceptableAnswers: ["2", "two"]
      },
      {
        questionEng: "What is 10 more than 472? (Add 1 ten)",
        socraticPromptEng: "Increase the tens digit 7 by 1.",
        hint1Eng: "7 tens + 1 ten = 8 tens.",
        hint2Eng: "Increase the middle digit from 7 to 8.",
        hint3Eng: "Hundreds stays 4, tens becomes 8, ones stays 2: 482!",
        explainEng: "Adding 10 makes 482.",
        analogyEng: "Add 1 sheet of 10 stickers: 482 stickers total!",
        acceptableAnswers: ["482", "tens", "the tens place changes"]
      },
      {
        questionEng: "What is 10 less than 472? (Take away 1 ten)",
        socraticPromptEng: "Decrease the tens digit 7 by 1.",
        hint1Eng: "7 tens - 1 ten = 6 tens.",
        hint2Eng: "Decrease the middle digit from 7 to 6.",
        hint3Eng: "Hundreds stays 4, tens becomes 6, ones stays 2: 462!",
        explainEng: "Subtracting 10 makes 462.",
        analogyEng: "Use up 1 sheet of 10 stickers, leaving 462 stickers!",
        acceptableAnswers: ["462", "tens", "the tens place changes"]
      }
    ]
  },

  "math_p8_b2": {
    statementEng: "35 + 9 = ___",
    hintsEng: [
      "9 is super close to 10!",
      "Add 10 first (35 + 10 = 45), then subtract 1 to adjust.",
      "45 - 1 = 44! "
    ],
    explainEng: {
      messageEng: "Adding 9 is the same as adding 10 and then subtracting 1. 35 + 10 = 45, and 45 - 1 = 44!",
      questionEng: "Why is adding 10 easier than adding 9 directly?"
    },
    steps: [
      {
        questionEng: "What friendly number is 9 super close to?",
        socraticPromptEng: "What round number comes right after 9?",
        hint1Eng: "9 is just 1 away from this round number.",
        hint2Eng: "Think of the round ten number right after 9.",
        hint3Eng: "10 is our friendly helper number.",
        explainEng: "9 is close to 10.",
        analogyEng: "9 is one step away from 10 on the number line.",
        acceptableAnswers: ["10", "ten"]
      },
      {
        questionEng: "If you add 10 to 35 instead of 9, what is 35 + 10?",
        socraticPromptEng: "Add 1 ten to 35. 3 tens becomes 4 tens.",
        hint1Eng: "35 + 10 increases the tens place by 1.",
        hint2Eng: "Count 10 up from 35: 35...",
        hint3Eng: "Example: 25 + 10 = 35, so 35 + 10 = 45.",
        explainEng: "35 + 10 = 45.",
        analogyEng: "Jump 10 steps forward from 35 to land on 45.",
        acceptableAnswers: ["45", "forty-five", "forty five"]
      },
      {
        questionEng: "Because we added 10 instead of 9, we added 1 too many! What should we do?",
        socraticPromptEng: "Since we added 1 extra, how do we fix it?",
        hint1Eng: "We added 1 extra, so we must take it away.",
        hint2Eng: "Subtract 1 to balance it out.",
        hint3Eng: "Option: Subtract 1 (-1).",
        explainEng: "We take away the extra 1 that we added.",
        analogyEng: "If a friend gives you 1 cookie too many, you give 1 back!",
        acceptableAnswers: ["subtract 1", "subtract", "take away 1", "-1", "- 1", "minus 1", "1"],
        options: ["Subtract 1 (-1)", "Add 1 (+1)", "Multiply by 1"]
      },
      {
        questionEng: "What is 45 - 1?",
        socraticPromptEng: "What number comes right before 45?",
        hint1Eng: "Take 1 away from 45.",
        hint2Eng: "Count 1 step backward from 45.",
        hint3Eng: "Example: 5 - 1 = 4, so 45 - 1 = 44!",
        explainEng: "45 - 1 = 44, which is our final answer.",
        analogyEng: "Step back 1 step from 45 to reach 44!",
        acceptableAnswers: ["44", "forty-four", "forty four"]
      }
    ]
  },

  "math_p8_b6": {
    statementEng: "74 - 9 = ___",
    hintsEng: [
      "9 is close to 10!",
      "Subtract 10 first (74 - 10 = 64), then add 1 back because you took away too much.",
      "64 + 1 = 65! "
    ],
    explainEng: {
      messageEng: "Subtracting 9 is like subtracting 10, then giving 1 back. 74 - 10 = 64, and 64 + 1 = 65!",
      questionEng: "Why do we add 1 back after subtracting 10?"
    },
    steps: [
      {
        questionEng: "What friendly number is 9 close to?",
        socraticPromptEng: "What round number is 1 away from 9?",
        hint1Eng: "9 is just 1 less than this number.",
        hint2Eng: "Think of the round ten number that comes right after 9.",
        hint3Eng: "10 is our friendly helper number.",
        explainEng: "9 is close to 10.",
        analogyEng: "10 is 9's friendly big brother.",
        acceptableAnswers: ["10", "ten"]
      },
      {
        questionEng: "What is 74 - 10?",
        socraticPromptEng: "Subtract 1 ten from 74. 7 tens becomes 6 tens.",
        hint1Eng: "Decrease the tens digit 7 by 1.",
        hint2Eng: "Subtract 1 ten from 7 tens, keeping the 4 ones.",
        hint3Eng: "Example: 54 - 10 = 44, so 74 - 10 = 64.",
        explainEng: "74 - 10 = 64.",
        analogyEng: "Hop backward 10 steps from 74 to land on 64.",
        acceptableAnswers: ["64", "sixty-four", "sixty four"]
      },
      {
        questionEng: "We subtracted 10 instead of 9, so we took away 1 too many! What should we do?",
        socraticPromptEng: "We took 1 extra away, so should we add 1 back?",
        hint1Eng: "We only needed to take 9, but we took 10.",
        hint2Eng: "Add 1 back to make it right.",
        hint3Eng: "Action: Add 1 (+1).",
        explainEng: "Since we took away 1 too many, we add 1 back.",
        analogyEng: "If you accidentally gave someone 1 extra toy, you take 1 back!",
        acceptableAnswers: ["add 1", "add", "+1", "+ 1", "plus 1", "1"],
        options: ["Add 1 (+1)", "Subtract 1 (-1)"]
      },
      {
        questionEng: "What is 64 + 1?",
        socraticPromptEng: "What number comes right after 64?",
        hint1Eng: "Add 1 to 64.",
        hint2Eng: "Count 1 number up from 64.",
        hint3Eng: "Count: 64, 65!",
        explainEng: "64 + 1 = 65, our final answer!",
        analogyEng: "Step forward 1 step to reach 65.",
        acceptableAnswers: ["65", "sixty-five", "sixty five"]
      }
    ]
  },

  "math_p8_b3": {
    statementEng: "58 + 11 = ___",
    hintsEng: [
      "Break 11 into 10 + 1.",
      "Add 10 first: 58 + 10 = 68.",
      "Then add 1: 68 + 1 = 69! "
    ],
    explainEng: {
      messageEng: "11 is just 10 plus 1. Add 10 to 58 to get 68, then add 1 to get 69!",
      questionEng: "How can breaking 11 into tens and ones help?"
    },
    steps: [
      {
        questionEng: "How can we split 11 into tens and ones?",
        socraticPromptEng: "11 is made of 1 ten and how many ones?",
        hint1Eng: "11 = 10 + something.",
        hint2Eng: "Split 11 into a group of 10 and single ones.",
        hint3Eng: "1 ten and 1 one (10 + 1).",
        explainEng: "11 breaks down into 10 + 1.",
        analogyEng: "A package of 10 pencils plus 1 single pencil.",
        acceptableAnswers: ["10 + 1", "10 and 1", "1 ten and 1 one", "10, 1", "11"]
      },
      {
        questionEng: "What is 58 + 10?",
        socraticPromptEng: "Add 1 ten to 58. 5 tens becomes 6 tens.",
        hint1Eng: "58 + 10 increases the tens digit by 1.",
        hint2Eng: "Count 10 up from 58: 58...",
        hint3Eng: "Example: 48 + 10 = 58, so 58 + 10 = 68.",
        explainEng: "58 + 10 = 68.",
        analogyEng: "Jump 10 steps forward from 58 to reach 68.",
        acceptableAnswers: ["68", "sixty-eight", "sixty eight"]
      },
      {
        questionEng: "Now add the remaining 1: what is 68 + 1?",
        socraticPromptEng: "What number comes right after 68?",
        hint1Eng: "Add 1 to 68.",
        hint2Eng: "Count 1 number forward from 68.",
        hint3Eng: "Count: 68, 69!",
        explainEng: "68 + 1 = 69.",
        analogyEng: "One tiny step forward from 68 lands on 69.",
        acceptableAnswers: ["69", "sixty-nine", "sixty nine"]
      }
    ]
  },

  "math_p8_b7": {
    statementEng: "52 - 11 = ___",
    hintsEng: [
      "Break 11 into 10 + 1.",
      "Subtract 10 first: 52 - 10 = 42.",
      "Then subtract 1: 42 - 1 = 41! "
    ],
    explainEng: {
      messageEng: "Subtract 10 first to get 42, then subtract the last 1 to get 41!",
      questionEng: "Which digit changes when you subtract 10?"
    },
    steps: [
      {
        questionEng: "How can we split 11 into tens and ones?",
        socraticPromptEng: "11 is made of 10 and what other number?",
        hint1Eng: "11 is 10 plus 1.",
        hint2Eng: "Split 11 into a group of 10 and single ones.",
        hint3Eng: "10 + 1.",
        explainEng: "11 = 10 + 1.",
        analogyEng: "A full 10-pack plus 1 loose item.",
        acceptableAnswers: ["10 + 1", "10 and 1", "1 ten and 1 one", "10, 1", "11"]
      },
      {
        questionEng: "What is 52 - 10?",
        socraticPromptEng: "Take away 1 ten from 52. 5 tens becomes 4 tens.",
        hint1Eng: "Decrease the tens digit 5 by 1.",
        hint2Eng: "Subtract 1 ten from 5 tens, keeping the 2 ones.",
        hint3Eng: "Example: 62 - 10 = 52, so 52 - 10 = 42.",
        explainEng: "52 - 10 = 42.",
        analogyEng: "Hop backward 10 steps from 52 to 42.",
        acceptableAnswers: ["42", "forty-two", "forty two"]
      },
      {
        questionEng: "Now subtract the remaining 1: what is 42 - 1?",
        socraticPromptEng: "What number comes right before 42?",
        hint1Eng: "Take 1 away from 42.",
        hint2Eng: "Count 1 number backward from 42.",
        hint3Eng: "Count backward: 42, 41!",
        explainEng: "42 - 1 = 41.",
        analogyEng: "Step back 1 step from 42 to land on 41.",
        acceptableAnswers: ["41", "forty-one", "forty one"]
      }
    ]
  },

  "math_p8_b4": {
    statementEng: "27 + 30 = ___",
    hintsEng: [
      "30 is 3 groups of ten.",
      "Add the tens together: 2 tens + 3 tens = 5 tens (50).",
      "Add the 7 ones: 50 + 7 = 57! "
    ],
    explainEng: {
      messageEng: "Adding 30 only changes the tens place: 2 tens + 3 tens = 5 tens, and the 7 ones stay the same, giving 57!",
      questionEng: "Does the ones digit 7 change when you add 30?"
    },
    steps: [
      {
        questionEng: "How many tens are in 30?",
        socraticPromptEng: "Count by tens to 30: 10, 20, 30. How many tens?",
        hint1Eng: "Look at the tens digit in 30.",
        hint2Eng: "Count by tens: 10, 20, 30. How many groups?",
        hint3Eng: "3 tens = 30.",
        explainEng: "30 means 3 tens.",
        analogyEng: "3 rolls of 10 coins.",
        acceptableAnswers: ["3", "three", "3 tens"]
      },
      {
        questionEng: "Add 3 tens (30) to 2 tens (20). What is 20 + 30?",
        socraticPromptEng: "What is 2 tens plus 3 tens?",
        hint1Eng: "2 + 3 = 5, so 20 + 30 is 5 tens.",
        hint2Eng: "Combine 2 tens and 3 tens.",
        hint3Eng: "Example: 2 tens + 3 tens = 5 tens (50).",
        explainEng: "Combining the tens gives 50.",
        analogyEng: "2 bags of 10 plus 3 bags of 10 = 5 bags of 10 (50 coins).",
        acceptableAnswers: ["50", "fifty", "5 tens", "the tens increase by 3"]
      },
      {
        questionEng: "Now add the 7 ones: what is 50 + 7?",
        socraticPromptEng: "Put 50 and 7 together.",
        hint1Eng: "50 plus 7 ones.",
        hint2Eng: "Put 5 tens and 7 ones together.",
        hint3Eng: "Example: 5 tens and 7 ones = 57!",
        explainEng: "50 + 7 = 57, our final answer!",
        analogyEng: "50 dollars plus 7 dollars = 57 dollars.",
        acceptableAnswers: ["57", "fifty-seven", "fifty seven"]
      }
    ]
  },

  "math_p8_b8": {
    statementEng: "91 - 20 = ___",
    hintsEng: [
      "20 is 2 groups of ten.",
      "Subtract 2 tens from 9 tens: 9 tens - 2 tens = 7 tens (70).",
      "Keep the 1 one: 70 + 1 = 71! "
    ],
    explainEng: {
      messageEng: "Subtracting 20 only changes the tens place: 9 tens minus 2 tens leaves 7 tens, so 91 becomes 71!",
      questionEng: "Can you count backward by tens from 91?"
    },
    steps: [
      {
        questionEng: "How many tens are in 20?",
        socraticPromptEng: "How many groups of 10 make 20?",
        hint1Eng: "Look at the tens digit in the number 20.",
        hint2Eng: "Count: 10... next is 20. How many tens?",
        hint3Eng: "2 tens = 20.",
        explainEng: "There are 2 tens in 20.",
        analogyEng: "2 stacks of 10 cards.",
        acceptableAnswers: ["2", "two", "2 tens"]
      },
      {
        questionEng: "Subtract 2 tens (20) from 9 tens (90). What is 90 - 20?",
        socraticPromptEng: "What is 9 tens minus 2 tens?",
        hint1Eng: "9 - 2 = 7, so 90 - 20 has 7 tens.",
        hint2Eng: "Take 2 tens away from 9 tens.",
        hint3Eng: "Example: 90 - 10 = 80, 80 - 10 = 70.",
        explainEng: "Subtracting 2 tens leaves 70.",
        analogyEng: "Remove 2 stacks of 10 from 9 stacks, leaving 7 stacks (70).",
        acceptableAnswers: ["70", "seventy", "7 tens", "the tens decrease by 2"]
      },
      {
        questionEng: "Now add the 1 one back: what is 70 + 1?",
        socraticPromptEng: "Combine 70 and the 1 one.",
        hint1Eng: "70 plus 1.",
        hint2Eng: "Count 1 number forward from 70.",
        hint3Eng: "Example: Count 1 after 70: 71!",
        explainEng: "70 + 1 = 71, our final answer!",
        analogyEng: "70 points + 1 point = 71 points!",
        acceptableAnswers: ["71", "seventy-one", "seventy one"]
      }
    ]
  },

  // =========================================================================
  // MATH HOMEWORK 16 (Page 16) - Calendar & Time Facts
  // =========================================================================

  "math_p16_a1": {
    statementEng: "How many days are in this month?",
    hintsEng: [
      "Look at the name of the month at the top of the calendar.",
      "Find the very last date number printed in the month.",
      "August ends on 31, so there are 31 days! "
    ],
    explainEng: {
      messageEng: "A calendar page lists every day from 1 to the end. The last number tells you the total days in the month!",
      questionEng: "What number does the August calendar finish on?"
    },
    steps: [
      {
        questionEng: "What month is shown at the top of the calendar?",
        socraticPromptEng: "Read the big word at the very top of the worksheet calendar.",
        hint1Eng: "It begins with the letter 'A'.",
        hint2Eng: "It is the month after July: August.",
        hint3Eng: "Look at the title: August.",
        explainEng: "The calendar displays August.",
        analogyEng: "August is often a warm summer month of vacation!",
        acceptableAnswers: ["August", "august"]
      },
      {
        questionEng: "What is the last numbered date shown in August?",
        socraticPromptEng: "Look near the bottom right of the calendar squares. What is the highest number?",
        hint1Eng: "Look at the bottom row of the calendar.",
        hint2Eng: "Find the largest date number.",
        hint3Eng: "The last date is 31.",
        explainEng: "The last date on the calendar is 31.",
        analogyEng: "The final page number in a chapter.",
        acceptableAnswers: ["31", "thirty-one", "thirty one"]
      },
      {
        questionEng: "So how many days does this month have in total?",
        socraticPromptEng: "If the dates count from 1 up to 31, how many days is that?",
        hint1Eng: "The last date tells you the total number of days.",
        hint2Eng: "Check the largest date you found in August.",
        hint3Eng: "Total days = 31.",
        explainEng: "August has 31 days.",
        analogyEng: "31 sunrise and sunset days in August!",
        acceptableAnswers: ["31", "thirty-one", "thirty one", "31 days"]
      }
    ]
  },

  "math_p16_a2": {
    statementEng: "What day of the week is 14 August?",
    hintsEng: [
      "Find the number 14 on the calendar grid.",
      "Trace your finger straight up to the column heading.",
      "14 August is in the Friday column! "
    ],
    explainEng: {
      messageEng: "To find the weekday for any date, find the number on the calendar and follow the column straight up to the day name!",
      questionEng: "Which column heading sits right above 14?"
    },
    steps: [
      {
        questionEng: "Find the number 14 on the calendar. What column heading is right above it?",
        socraticPromptEng: "Put your finger on 14, then slide straight up to the top row.",
        hint1Eng: "Trace straight up from number 14.",
        hint2Eng: "The weekday starts with 'F'.",
        hint3Eng: "It is Friday!",
        explainEng: "Directly above 14 is the Friday column.",
        analogyEng: "Like an elevator going straight up from floor 14 to the Friday roof!",
        acceptableAnswers: ["Friday", "friday"],
        options: ["Friday", "Thursday", "Saturday", "Sunday"]
      },
      {
        questionEng: "So what day of the week is 14 August?",
        socraticPromptEng: "What weekday did our column tell us?",
        hint1Eng: "Look at the column heading we just found.",
        hint2Eng: "It is the day right before the weekend.",
        hint3Eng: "Answer: Friday.",
        explainEng: "14 August falls on Friday.",
        analogyEng: "Friday is the fun day right before the weekend!",
        acceptableAnswers: ["Friday", "friday"],
        options: ["Friday", "Thursday", "Saturday", "Sunday"]
      },
      {
        questionEng: "Which day comes right after Friday?",
        socraticPromptEng: "What is the very next weekday?",
        hint1Eng: "It is the first day of the weekend.",
        hint2Eng: "It starts with 'S': Saturday.",
        hint3Eng: "Friday is followed by Saturday.",
        explainEng: "Saturday comes after Friday.",
        analogyEng: "Saturday morning cartoons come right after Friday night!",
        acceptableAnswers: ["Saturday", "saturday"],
        options: ["Saturday", "Sunday", "Monday"]
      }
    ]
  },

  "math_p16_a3": {
    statementEng: "What date is one week after 8 August?",
    hintsEng: [
      "One week has exactly 7 days.",
      "Add 7 days to August 8: 8 + 7 = 15.",
      "One week after 8 August is 15 August! "
    ],
    explainEng: {
      messageEng: "Since a week has 7 days, you can add 7 to the date, or just move down one row in the same column on the calendar!",
      questionEng: "What is 8 + 7?"
    },
    steps: [
      {
        questionEng: "How many days are in 1 full week?",
        socraticPromptEng: "Count the days: Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday.",
        hint1Eng: "Count the weekdays in a row.",
        hint2Eng: "There are between 5 and 10 days in a week.",
        hint3Eng: "1 week = 7 days.",
        explainEng: "Every week has 7 days.",
        analogyEng: "7 colors in a rainbow, 7 days in a week!",
        acceptableAnswers: ["7", "seven", "7 days"]
      },
      {
        questionEng: "Start at 8 August. What is 8 + 7?",
        socraticPromptEng: "Add 7 days to the date 8.",
        hint1Eng: "Start from 8 and count 7 more: 9, 10, 11...",
        hint2Eng: "Think: 8 + 2 = 10, then add 5 more.",
        hint3Eng: "8 + 7 = 15.",
        explainEng: "8 + 7 = 15.",
        analogyEng: "Hop 7 calendar squares forward from 8 to land on 15.",
        acceptableAnswers: ["15", "fifteen"]
      },
      {
        questionEng: "So what date is one week after 8 August?",
        socraticPromptEng: "Combine the month August and your date 15.",
        hint1Eng: "Write the date in August.",
        hint2Eng: "Look at the day number you just calculated.",
        hint3Eng: "Answer: 15 August.",
        explainEng: "One week after 8 August is 15 August.",
        analogyEng: "Exactly the same weekday, one row down on the calendar!",
        acceptableAnswers: ["15 August", "15", "August 15", "15th", "15th August"]
      }
    ]
  },

  "math_p16_a4": {
    statementEng: "Circle 31 August.",
    hintsEng: [
      "Look near the bottom right of the calendar grid.",
      "31 is the very last day of August.",
      "Find the number 31 and tap or circle it! "
    ],
    explainEng: {
      messageEng: "August ends on date 31. Look at the last numbered box on the calendar!",
      questionEng: "Where do you look for the end of the month?"
    },
    steps: [
      {
        questionEng: "What date number are you looking for?",
        socraticPromptEng: "Check the question: Circle ___ August.",
        hint1Eng: "Look at the number written in the instructions.",
        hint2Eng: "Check the problem title: Circle ___ August.",
        hint3Eng: "Number: 31.",
        explainEng: "The goal is to find 31.",
        analogyEng: "Finding page 31 in a storybook.",
        acceptableAnswers: ["31", "thirty-one", "thirty one"]
      },
      {
        questionEng: "Look at the calendar. Where is 31 located?",
        socraticPromptEng: "Is 31 at the start, middle, or end of the month?",
        hint1Eng: "31 is the largest date number.",
        hint2Eng: "It is the very last day of August.",
        hint3Eng: "Look at the bottom row.",
        explainEng: "31 is the final date of the month.",
        analogyEng: "The last stepping stone on the path.",
        acceptableAnswers: ["end", "last", "bottom", "31", "at the end"]
      },
      {
        questionEng: "Confirm the date: what number did you find to circle?",
        socraticPromptEng: "Type the date number you circled.",
        hint1Eng: "Look at the date you found at the end of August.",
        hint2Eng: "Type the number that was in the instructions.",
        hint3Eng: "Answer: 31.",
        explainEng: "You circled 31 August!",
        analogyEng: "Celebration day on the 31st!",
        acceptableAnswers: ["31", "31 August", "student selects 31", "thirty-one"]
      }
    ]
  },

  "math_p16_b1": {
    statementEng: "1 week = ____ days",
    hintsEng: [
      "Count the days of the week: Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday.",
      "There are 7 days in every full week.",
      "1 week = 7 days! "
    ],
    explainEng: {
      messageEng: "Every single week on the calendar has exactly 7 days: 5 school days and 2 weekend days!",
      questionEng: "Can you name all 7 days of the week?"
    },
    steps: [
      {
        questionEng: "How many weekday column headings are there in a full week?",
        socraticPromptEng: "Count the column headers: Sun, Mon, Tue, Wed, Thu, Fri, Sat.",
        hint1Eng: "Count across the top row of the calendar.",
        hint2Eng: "Count each day of the week on your fingers.",
        hint3Eng: "Number of days: 7.",
        explainEng: "There are 7 days across the week header.",
        analogyEng: "7 notes in a musical scale: do, re, mi, fa, sol, la, ti!",
        acceptableAnswers: ["7", "seven"]
      },
      {
        questionEng: "So fill in the blank: 1 week = ? days.",
        socraticPromptEng: "How many days make 1 week?",
        hint1Eng: "Think of how many days are in a week.",
        hint2Eng: "Write the number you just counted.",
        hint3Eng: "Answer: 7.",
        explainEng: "1 week = 7 days.",
        analogyEng: "7 sleep-and-wake cycles make one week.",
        acceptableAnswers: ["7", "seven", "7 days"]
      }
    ]
  },

  "math_p16_b2": {
    statementEng: "1 fortnight = ____ weeks",
    hintsEng: [
      "A fortnight is an old word for 'fourteen nights' (14 days).",
      "Since 1 week is 7 days, 14 days is 2 weeks!",
      "1 fortnight = 2 weeks! "
    ],
    explainEng: {
      messageEng: "A fortnight means two full weeks: 7 days + 7 days = 14 days = 2 weeks.",
      questionEng: "If one week has 7 days, how many weeks make 14 days?"
    },
    steps: [
      {
        questionEng: "A fortnight means 14 days. Since 1 week is 7 days, how many 7-day weeks is 14 days?",
        socraticPromptEng: "Think: 7 + 7 = 14. How many weeks is that?",
        hint1Eng: "7 days is 1 week. 14 days is double that.",
        hint2Eng: "Think how many groups of 7 fit into 14.",
        hint3Eng: "7 + 7 = 14, so it is 2 weeks.",
        explainEng: "14 days equals 2 weeks.",
        analogyEng: "Two full weekends and two school weeks together!",
        acceptableAnswers: ["2", "two", "2 weeks", "a fortnight is 2 weeks"]
      },
      {
        questionEng: "Fill in the blank: 1 fortnight = ? weeks.",
        socraticPromptEng: "What number of weeks goes in the blank?",
        hint1Eng: "Think of the number of weeks we just discovered.",
        hint2Eng: "Think back to how many 7-day weeks fit into 14 days.",
        hint3Eng: "Answer: 2.",
        explainEng: "1 fortnight = 2 weeks.",
        analogyEng: "Two calendar rows make a fortnight!",
        acceptableAnswers: ["2", "two", "2 weeks"]
      }
    ]
  },

  "math_p16_b3": {
    statementEng: "1 year = ____ months",
    hintsEng: [
      "Count the months: January, February, March, April, May, June, July, August, September, October, November, December.",
      "There are 12 months in one full year.",
      "1 year = 12 months! "
    ],
    explainEng: {
      messageEng: "From January to December, there are 12 months in every single year!",
      questionEng: "What is the first month and what is the last month of the year?"
    },
    steps: [
      {
        questionEng: "How many month names are there from January to December?",
        socraticPromptEng: "Count them: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec.",
        hint1Eng: "Count all the months in the year.",
        hint2Eng: "Think of a clock: it has this same number of hours!",
        hint3Eng: "There are 12 months in a year.",
        explainEng: "There are 12 months in a year.",
        analogyEng: "12 eggs in a dozen, 12 months in a year!",
        acceptableAnswers: ["12", "twelve"]
      },
      {
        questionEng: "So fill in the blank: 1 year = ? months.",
        socraticPromptEng: "What number of months equals 1 year?",
        hint1Eng: "Think of the total number of months you just counted.",
        hint2Eng: "Think back to the number of months in a year.",
        hint3Eng: "Answer: 12.",
        explainEng: "1 year = 12 months.",
        analogyEng: "12 monthly calendar pages hanging on the wall!",
        acceptableAnswers: ["12", "twelve", "12 months"]
      }
    ]
  },

  "math_p16_b4": {
    statementEng: "A common year = ____ days",
    hintsEng: [
      "A normal, regular year is called a common year.",
      "It has 365 days.",
      "A common year = 365 days! "
    ],
    explainEng: {
      messageEng: "In a normal year, Earth takes about 365 days to circle the Sun once!",
      questionEng: "Does a common year have more or fewer days than a leap year?"
    },
    steps: [
      {
        questionEng: "What kind of year has 365 days: a common year or a leap year?",
        socraticPromptEng: "A regular, normal year with 365 days is called a what?",
        hint1Eng: "It is the standard year, not the leap year.",
        hint2Eng: "It starts with 'c' and means ordinary or regular.",
        hint3Eng: "Answer: common year.",
        explainEng: "A regular year is called a common year.",
        analogyEng: "Common means regular or ordinary!",
        acceptableAnswers: ["common year", "a common year", "common", "365", "365 days"],
        options: ["Common year", "Leap year"]
      },
      {
        questionEng: "How many days are in a common year?",
        socraticPromptEng: "What 3-digit number goes in the blank?",
        hint1Eng: "It has three hundreds and sixty-something days.",
        hint2Eng: "Think of three hundred sixty-five.",
        hint3Eng: "Answer: 365.",
        explainEng: "A common year has 365 days.",
        analogyEng: "365 daily pages on a tear-off calendar!",
        acceptableAnswers: ["365", "365 days", "three hundred sixty-five", "three hundred sixty five"]
      }
    ]
  },

  "math_p16_b5": {
    statementEng: "A leap year = ____ days",
    hintsEng: [
      "Every 4 years, we add 1 extra day to February.",
      "365 + 1 = 366 days.",
      "A leap year = 366 days! "
    ],
    explainEng: {
      messageEng: "Because the Earth takes 365 and 1/4 days to travel around the Sun, every 4 years we add 1 full leap day: 366 days!",
      questionEng: "How many more days does a leap year have compared to a common year?"
    },
    steps: [
      {
        questionEng: "Every 4 years we add 1 extra day to a common year (365 + 1). How many days is that?",
        socraticPromptEng: "What is 365 + 1?",
        hint1Eng: "Add 1 to 365.",
        hint2Eng: "What number comes right after 365?",
        hint3Eng: "365 + 1 = 366 days.",
        explainEng: "A leap year has 366 days.",
        analogyEng: "One extra bonus day to play!",
        acceptableAnswers: ["366", "366 days", "three hundred sixty-six", "three hundred sixty six"]
      },
      {
        questionEng: "Which month gets the extra bonus day during a leap year?",
        socraticPromptEng: "Which short month gets a 29th day in a leap year?",
        hint1Eng: "It is the second month of the year.",
        hint2Eng: "It starts with 'F' and is the shortest month.",
        hint3Eng: "Answer: February.",
        explainEng: "February gets the extra 29th day during a leap year.",
        analogyEng: "February grows from 28 to 29 days!",
        acceptableAnswers: ["February", "february", "feb", "because february has an extra day"],
        options: ["February", "January", "December", "August"]
      }
    ]
  },

  "math_p16_b6": {
    statementEng: "February usually has ____ days",
    hintsEng: [
      "February is the shortest month of the year.",
      "In a normal year, February has 28 days.",
      "In a leap year, it has 29 days! "
    ],
    explainEng: {
      messageEng: "February usually has 28 days, except during a leap year when it gets 29 days!",
      questionEng: "How many days does February usually have before the leap year bonus?"
    },
    steps: [
      {
        questionEng: "Which month is known as the shortest month of the year?",
        socraticPromptEng: "It comes between January and March.",
        hint1Eng: "It is month number 2.",
        hint2Eng: "It starts with 'Feb-'.",
        hint3Eng: "Answer: February.",
        explainEng: "February is the shortest month.",
        analogyEng: "The baby month of the calendar!",
        acceptableAnswers: ["February", "february", "feb"],
        options: ["February", "January", "April"]
      },
      {
        questionEng: "How many days does February usually have in a normal year?",
        socraticPromptEng: "What number of days is printed for February in standard years?",
        hint1Eng: "It is between 25 and 30 days.",
        hint2Eng: "Think of exactly 4 full weeks (4 × 7).",
        hint3Eng: "Answer: 28 days.",
        explainEng: "February usually has 28 days.",
        analogyEng: "Exactly 4 full weeks of 7 days: 4 × 7 = 28!",
        acceptableAnswers: ["28", "28 days", "twenty-eight", "twenty eight"]
      },
      {
        questionEng: "During a leap year, how many days does February have?",
        socraticPromptEng: "Add 1 extra day to 28.",
        hint1Eng: "Add 1 bonus day to 28.",
        hint2Eng: "What number comes right after 28?",
        hint3Eng: "Answer: 29 days.",
        explainEng: "In a leap year, February has 29 days.",
        analogyEng: "February leaps forward with 29 days!",
        acceptableAnswers: ["29", "29 days", "twenty-nine", "because of leap years", "leap year"]
      }
    ]
  },

  // =========================================================================
  // SCIENCE PAGE 8: Identifying Animal Features (Classification Table)
  // =========================================================================

  "science_p8_flamingo": {
    statementEng: "Put a tick or cross to describe the features of the flamingo.",
    hintsEng: [
      "A flamingo is a tall pink wading bird.",
      "Birds are vertebrates with feathers and wings.",
      "Flamingos do NOT have camel humps or lobster pincers! "
    ],
    explainEng: {
      messageEng: "Flamingos are birds! They have backbones, feathers, and wings for flying, but no humps or claws.",
      questionEng: "What special features make a flamingo a bird?"
    },
    steps: [
      {
        questionEng: "Does a flamingo have a backbone (is it a vertebrate)?",
        socraticPromptEng: "Do birds have bones inside their bodies, including a spine?",
        hint1Eng: "All birds have an internal skeleton with a backbone.",
        hint2Eng: "Think: do large flying birds have bones inside?",
        hint3Eng: "Tick 'Yes (✓)'!",
        explainEng: "Flamingos have backbones, making them vertebrates.",
        analogyEng: "Feel your own backbone with your hand: birds have one too!",
        acceptableAnswers: ["Yes", "yes", "true", "y", "tick", "✓"],
        options: ["✓ Yes", "✗ No"]
      },
      {
        questionEng: "What covers a flamingo's body: feathers, fur, or scales?",
        socraticPromptEng: "What soft, colorful coat do birds wear?",
        hint1Eng: "Birds are the only animals that have these.",
        hint2Eng: "They are pink and help the flamingo fly and stay dry.",
        hint3Eng: "Choose 'Feathers'.",
        explainEng: "Flamingos are covered in pink feathers.",
        analogyEng: "Light, waterproof feathers that keep the bird warm and dry.",
        acceptableAnswers: ["Feathers", "feathers", "feather", "yes"],
        options: ["Feathers", "Fur", "Scales"]
      },
      {
        questionEng: "Look at its back. Does a flamingo have a camel-like hump?",
        socraticPromptEng: "Does a flamingo store water in a big raised hump on its back?",
        hint1Eng: "Look closely at the picture: its back is smooth.",
        hint2Eng: "Think: which desert animal is the only one with a hump?",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Only camels have back humps.",
        analogyEng: "A flamingo's back is gracefully curved, not humped.",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a flamingo have lobster-like pincers?",
        socraticPromptEng: "Does a flamingo have sharp claw pincers on its limbs?",
        hint1Eng: "Flamingos have webbed feet and wings, not pinching claws.",
        hint2Eng: "Crabs and lobsters have pincers, not wading birds.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Flamingos do not have pincers.",
        analogyEng: "A flamingo has gentle wings, not snapping pincers!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Can you identify the large body parts birds use for flying?",
        socraticPromptEng: "What does a flamingo spread out to fly through the air?",
        hint1Eng: "Birds flap these to fly in the sky.",
        hint2Eng: "They spread out wide on both sides of its body.",
        hint3Eng: "Choose 'Wings'.",
        explainEng: "Flamingos have wings to fly high across lakes.",
        analogyEng: "Spread your arms wide like wings to glide!",
        acceptableAnswers: ["Wings", "wings", "wing", "yes"],
        options: ["Wings", "Pincers", "Fins"]
      }
    ]
  },

  "science_p8_lobster": {
    statementEng: "Put a tick or cross to describe the features of the lobster.",
    hintsEng: [
      "A lobster lives on the ocean floor.",
      "It has a hard external shell instead of an internal backbone.",
      "It has large front pincers to grab food! "
    ],
    explainEng: {
      messageEng: "Lobsters are invertebrates! They do not have backbones, feathers, or wings, but they have powerful pincers.",
      questionEng: "How is a lobster different from a bird?"
    },
    steps: [
      {
        questionEng: "Does a lobster have an internal backbone like humans do?",
        socraticPromptEng: "Does a lobster have bones inside, or a hard shell outside?",
        hint1Eng: "Lobsters have a hard armor outside (exoskeleton), but no spine inside.",
        hint2Eng: "Invertebrates do not have internal bones.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Lobsters do not have backbones.",
        analogyEng: "A knight wearing a suit of armor with no bones inside!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a lobster have feathers?",
        socraticPromptEng: "Are lobsters covered in bird feathers?",
        hint1Eng: "Feathers belong only to birds.",
        hint2Eng: "Lobsters live underwater with hard crusty shells.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Lobsters have hard shells, not feathers.",
        analogyEng: "A shiny, hard sea shell!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a lobster have a camel-like hump on its back?",
        socraticPromptEng: "Is there a big fat hump on a lobster's back?",
        hint1Eng: "Look at the lobster's segmented tail and body.",
        hint2Eng: "Only desert camels have back humps.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Lobsters do not have humps.",
        analogyEng: "Its back has smooth armor plates.",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Look at the front of the lobster. What special body parts can you see?",
        socraticPromptEng: "What are those two big snapping claws called?",
        hint1Eng: "They are big claws used for grabbing and holding food.",
        hint2Eng: "They start with 'P' and pinch!",
        hint3Eng: "Choose 'Pincers'.",
        explainEng: "Lobsters have strong front pincers.",
        analogyEng: "Pincers act like kitchen tongs to grab tasty snacks!",
        acceptableAnswers: ["Pincers", "pincers", "pincer", "claws", "claw", "yes"],
        options: ["Pincers", "Wings", "Feathers"]
      },
      {
        questionEng: "Does a lobster have wings for flying?",
        socraticPromptEng: "Can a lobster flap wings and fly in the sky?",
        hint1Eng: "Lobsters crawl and swim on the sea bottom.",
        hint2Eng: "Sea creatures on the ocean floor do not fly.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Lobsters do not have wings.",
        analogyEng: "Lobsters walk underwater; they never fly!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      }
    ]
  },

  "science_p8_camel": {
    statementEng: "Put a tick or cross to describe the features of the camel.",
    hintsEng: [
      "A camel is a large desert mammal.",
      "It has a backbone (vertebrate) and a famous mound on its back.",
      "It has NO feathers, pincers, or wings! "
    ],
    explainEng: {
      messageEng: "Camels are vertebrates with fur and back humps that store fat for desert journeys!",
      questionEng: "What is the famous raised bump on a camel's back called?"
    },
    steps: [
      {
        questionEng: "Does a camel have a backbone (vertebrate)?",
        socraticPromptEng: "Is a camel a mammal with a skeleton and spine inside?",
        hint1Eng: "Camels are large mammals with bones inside.",
        hint2Eng: "Think: do large four-legged animals have backbones?",
        hint3Eng: "Tick 'Yes (✓)'!",
        explainEng: "Camels have strong backbones.",
        analogyEng: "Just like horses and cows, camels are vertebrates!",
        acceptableAnswers: ["Yes", "yes", "true", "y", "tick", "✓"],
        options: ["✓ Yes", "✗ No"]
      },
      {
        questionEng: "Does a camel's body have feathers?",
        socraticPromptEng: "Is a camel covered in feathers or thick fur?",
        hint1Eng: "Feathers belong only to birds.",
        hint2Eng: "Mammals have hair or fur, not bird feathers.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Camels have fur, not feathers.",
        analogyEng: "Thick cozy fur coats for chilly desert nights.",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "What special shape can you see on the camel's back?",
        socraticPromptEng: "What is that big raised mound on its back called?",
        hint1Eng: "It stores fat for long desert trips.",
        hint2Eng: "It starts with 'H' and rhymes with bump!",
        hint3Eng: "Choose 'Hump'.",
        explainEng: "Camels have humps on their backs.",
        analogyEng: "A built-in backpack full of stored energy!",
        acceptableAnswers: ["Hump", "hump", "hump on back", "yes"],
        options: ["Hump", "Wings", "Pincers"]
      },
      {
        questionEng: "Does a camel have lobster-like pincers?",
        socraticPromptEng: "Does a camel have pinching claws instead of hooves?",
        hint1Eng: "Camels have wide padded feet for walking on sand.",
        hint2Eng: "Pincers belong to crustaceans, not four-legged mammals.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Camels do not have pincers.",
        analogyEng: "Padded hooves make great sand-shoes!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a camel have wings?",
        socraticPromptEng: "Can a camel fly through the air?",
        hint1Eng: "Camels walk on four legs across the desert.",
        hint2Eng: "Heavy desert mammals cannot fly.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Camels do not have wings.",
        analogyEng: "Camels are the ships of the desert, walking on sand!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      }
    ]
  },

  "science_p8_giraffe": {
    statementEng: "Put a tick or cross to describe the features of the giraffe.",
    hintsEng: [
      "A giraffe is the tallest mammal on land.",
      "It has a long vertebrate neck and spotted fur coat.",
      "It does NOT have feathers, humps, pincers, or wings! "
    ],
    explainEng: {
      messageEng: "Giraffes have backbones, but they have no feathers, wings, humps, or claws!",
      questionEng: "What is the only feature from the worksheet table that a giraffe has?"
    },
    steps: [
      {
        questionEng: "Does a giraffe have a backbone (vertebrate)?",
        socraticPromptEng: "Does a giraffe have bones and a spine inside its super long neck?",
        hint1Eng: "A giraffe's long neck contains 7 big vertebrae bones, just like humans!",
        hint2Eng: "All mammals have backbones.",
        hint3Eng: "Tick 'Yes (✓)'!",
        explainEng: "Giraffes have strong backbones.",
        analogyEng: "A long tower of backbone vertebrae!",
        acceptableAnswers: ["Yes", "yes", "true", "y", "tick", "✓"],
        options: ["✓ Yes", "✗ No"]
      },
      {
        questionEng: "Is its body covered with feathers?",
        socraticPromptEng: "Does a giraffe have bird feathers or spotted hair?",
        hint1Eng: "Only birds have feathers.",
        hint2Eng: "Mammals have hair or fur, not feathers.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Giraffes have fur, not feathers.",
        analogyEng: "A beautiful coat of brown patchwork spots!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a giraffe have a camel-like hump on its back?",
        socraticPromptEng: "Look at the giraffe's back: does it have a hump?",
        hint1Eng: "Only camels have back humps.",
        hint2Eng: "A giraffe's back is straight and sloped, without any hump.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Giraffes do not have humps.",
        analogyEng: "Its back slopes smoothly down towards its tail.",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a giraffe have pincers?",
        socraticPromptEng: "Does a giraffe have claws or hooves?",
        hint1Eng: "Pincers belong to animals like crabs and lobsters.",
        hint2Eng: "Giraffes have long legs with hooves at the bottom.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Giraffes do not have pincers.",
        analogyEng: "Large hooves for walking on the savanna.",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a giraffe have wings for flying?",
        socraticPromptEng: "Can a giraffe fly in the sky?",
        hint1Eng: "Giraffes walk on the ground; they cannot fly.",
        hint2Eng: "Large mammals do not have wings.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Giraffes do not have wings.",
        analogyEng: "They reach high tree leaves using their tall necks, not wings!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      }
    ]
  },

  "science_p8_slug": {
    statementEng: "Put a tick or cross to describe the features of the slug.",
    hintsEng: [
      "A slug is a soft-bodied creature.",
      "It has NO bones inside: it is an invertebrate.",
      "A slug has NO feathers, humps, pincers, or wings (all crosses)! "
    ],
    explainEng: {
      messageEng: "Slugs are soft invertebrates. None of the special features in the table belong to a slug!",
      questionEng: "Can you spot any bones, wings, or claws on a slug?"
    },
    steps: [
      {
        questionEng: "Does a slug have a backbone like a giraffe or camel?",
        socraticPromptEng: "Does a slug have any hard bones inside its squishy body?",
        hint1Eng: "Slugs are completely soft-bodied with zero bones.",
        hint2Eng: "Animals with soft squishy bodies have no backbone.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Slugs do not have backbones.",
        analogyEng: "Squishy like modeling clay or jelly!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a slug have feathers?",
        socraticPromptEng: "Is a slug covered in feathers?",
        hint1Eng: "Feathers belong only to birds.",
        hint2Eng: "A slug has smooth, slimy skin, not feathers.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Slugs do not have feathers.",
        analogyEng: "Smooth and slippery skin.",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a slug have a camel-like hump on its back?",
        socraticPromptEng: "Look at the slug: does it have a hump?",
        hint1Eng: "Slugs have a low, flat, elongated body.",
        hint2Eng: "Look at its long flat body: no hump exists.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Slugs do not have humps.",
        analogyEng: "Flat and streamlined to crawl through garden soil.",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a slug have lobster-like pincers?",
        socraticPromptEng: "Does a slug have snapping claws?",
        hint1Eng: "Pincers belong to crustaceans, not slugs.",
        hint2Eng: "Slugs have no arms, legs, or claws.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Slugs do not have pincers.",
        analogyEng: "Slugs glide gently on a single muscular foot.",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a slug have wings?",
        socraticPromptEng: "Can a slug fly through the air?",
        hint1Eng: "Slugs glide slowly on the ground.",
        hint2Eng: "Slugs crawl on their belly and never fly.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Slugs do not have wings.",
        analogyEng: "Slugs leave a shiny trail on the garden path!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      }
    ]
  },

  "science_p8_moth": {
    statementEng: "Put a tick or cross to describe the features of the moth.",
    hintsEng: [
      "A moth is a flying insect.",
      "Insects do NOT have backbones (they are invertebrates).",
      "Moths have large wings, but NO feathers, humps, or pincers! "
    ],
    explainEng: {
      messageEng: "Moths have wings for flying, but they are insects without bones, feathers, humps, or claws!",
      questionEng: "What special feature helps a moth fly around night lights?"
    },
    steps: [
      {
        questionEng: "Does a moth have an internal backbone?",
        socraticPromptEng: "Is a moth an insect (invertebrate) or an animal with bones?",
        hint1Eng: "Insects have an exoskeleton, but no internal spine.",
        hint2Eng: "Insects belong to the group without backbones.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Moths do not have backbones.",
        analogyEng: "Lightweight insects have no heavy bones inside!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a moth have feathers like a bird?",
        socraticPromptEng: "Are moth wings made of bird feathers or tiny insect scales?",
        hint1Eng: "Only birds have real feathers.",
        hint2Eng: "Insect wings are thin membranes with tiny dust-like scales, not feathers.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Moths do not have feathers.",
        analogyEng: "Silky powdery wings, but no feathers!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a moth have a hump on its back?",
        socraticPromptEng: "Look at the moth: is there a camel hump?",
        hint1Eng: "Only camels have back humps.",
        hint2Eng: "Moths have a small insect thorax, no hump.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Moths do not have humps.",
        analogyEng: "Small slender insect body.",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "Does a moth have pincers like a lobster?",
        socraticPromptEng: "Does a moth have grabbing claws?",
        hint1Eng: "Lobsters have pincers; moths do not.",
        hint2Eng: "Moths have six tiny delicate walking legs, not claws.",
        hint3Eng: "Cross 'No (✗)'!",
        explainEng: "Moths do not have pincers.",
        analogyEng: "Delicate little feet, no sharp claws!",
        acceptableAnswers: ["No", "no", "false", "n", "cross", "✗"],
        options: ["✗ No", "✓ Yes"]
      },
      {
        questionEng: "What large body structures help a moth fly in the air?",
        socraticPromptEng: "What does a moth flutter to fly around?",
        hint1Eng: "They are wide and flap up and down.",
        hint2Eng: "They spread out wide on both sides so it can fly.",
        hint3Eng: "Choose 'Wings'.",
        explainEng: "Moths have two pairs of wings for flying.",
        analogyEng: "Fluttering wings that carry them softly through the night!",
        acceptableAnswers: ["Wings", "wings", "wing", "yes"],
        options: ["Wings", "Pincers", "Hump"]
      }
    ]
  },

  // =========================================================================
  // SCIENCE PAGE 6: Grouping Animals
  // =========================================================================

  "science_p6_bird": {
    statementEng: "Write one feature of the bird animal group.",
    hintsEng: [
      "Think about what covers an eagle or flamingo's body.",
      "Birds are the ONLY animal group with feathers.",
      "Feathers help them stay warm and fly! "
    ],
    explainEng: {
      messageEng: "All birds have feathers, beaks, and wings. Feathers are unique to birds!",
      questionEng: "What body covering is found only on birds?"
    },
    steps: [
      {
        questionEng: "Think of an eagle or flamingo. What covers most of its body?",
        socraticPromptEng: "What lightweight, colorful coat do birds wear?",
        hint1Eng: "It is not fur and not scales.",
        hint2Eng: "Think of the soft, light plumes that help birds fly.",
        hint3Eng: "Choose 'Feathers'.",
        explainEng: "Birds have feathers covering their bodies.",
        analogyEng: "Feathers act like a warm jacket and a glider wing in one!",
        acceptableAnswers: ["Feathers", "feathers", "feather"],
        options: ["Feathers", "Fur", "Scales"]
      },
      {
        questionEng: "Is having feathers a feature shared by all birds?",
        socraticPromptEng: "Do all birds have feathers?",
        hint1Eng: "Every bird, even penguins and ostriches, has feathers.",
        hint2Eng: "Think: is feathers the defining feature of every bird species?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "All birds have feathers.",
        analogyEng: "If it has true feathers, it's definitely a bird!",
        acceptableAnswers: ["Yes", "yes", "true", "y"],
        options: ["Yes", "No"]
      }
    ]
  },

  "science_p6_mammal": {
    statementEng: "Write one feature of the mammal animal group.",
    hintsEng: [
      "Think of animals like elephants, dogs, cats, and humans.",
      "Mammals have hair or fur, and mothers give milk to their babies.",
      "Feature: Hair or fur! "
    ],
    explainEng: {
      messageEng: "Mammals have hair or fur covering their bodies and nurse their young with milk!",
      questionEng: "What covers the body of a kitten, dog, or horse?"
    },
    steps: [
      {
        questionEng: "What animal group does an elephant, dog, or human belong to?",
        socraticPromptEng: "Which group of animals has warm blood, hair, and feeds milk to babies?",
        hint1Eng: "It begins with 'M'.",
        hint2Eng: "Think of warm-blooded animals that nurse their babies.",
        hint3Eng: "Choose 'Mammal'.",
        explainEng: "Elephants and humans are mammals.",
        analogyEng: "Mammals love giving warm hugs to their babies!",
        acceptableAnswers: ["Mammal", "mammal", "mammals"],
        options: ["Mammal", "Bird", "Reptile", "Invertebrate"]
      },
      {
        questionEng: "Can you name a body covering commonly associated with all mammals?",
        socraticPromptEng: "What grows on mammal skin: feathers, scales, or hair/fur?",
        hint1Eng: "Dogs have fur, humans have hair.",
        hint2Eng: "It is the soft, warm covering on animal coats.",
        hint3Eng: "Choose 'Hair or fur'.",
        explainEng: "All mammals grow hair or fur at some stage of life.",
        analogyEng: "Pet a soft puppy to feel mammal fur!",
        acceptableAnswers: ["Hair or fur", "hair or fur", "hair", "fur"],
        options: ["Hair or fur", "Feathers", "Scales"]
      }
    ]
  },

  "science_p6_amphibian": {
    statementEng: "Write one feature of the amphibian animal group.",
    hintsEng: [
      "Think of a frog or salamander.",
      "They can live both in water and on land.",
      "They have smooth, moist skin with NO scales or feathers! "
    ],
    explainEng: {
      messageEng: "Amphibians like frogs have smooth, moist skin that helps them breathe both in water and on land!",
      questionEng: "How does a frog's skin feel compared to a snake's scales?"
    },
    steps: [
      {
        questionEng: "What animal is shown as an example for the amphibian group?",
        socraticPromptEng: "Which green hopping creature starts life as a tadpole?",
        hint1Eng: "It croaks and hops near ponds.",
        hint2Eng: "It rhymes with 'log' and catches flies with its tongue.",
        hint3Eng: "Choose 'Frog'.",
        explainEng: "A frog is a classic amphibian.",
        analogyEng: "Ribbit! The frog hops from water onto a lily pad.",
        acceptableAnswers: ["Frog", "frog"],
        options: ["Frog", "Snake", "Fish", "Bird"]
      },
      {
        questionEng: "Does a frog have feathers, dry scales, or moist skin?",
        socraticPromptEng: "How does a frog's skin feel when it hops out of the pond?",
        hint1Eng: "Frogs need to keep their skin damp.",
        hint2Eng: "It feels slippery, smooth, and damp.",
        hint3Eng: "Choose 'Moist skin'.",
        explainEng: "Frogs have moist, smooth skin.",
        analogyEng: "Moist like a damp clean sponge!",
        acceptableAnswers: ["Moist skin", "moist skin", "smooth skin"],
        options: ["Moist skin", "Dry scales", "Feathers"]
      },
      {
        questionEng: "Can amphibians live both on land and in water during their lives?",
        socraticPromptEng: "Tadpoles swim in water, then grow legs to hop on land: true or false?",
        hint1Eng: "'Amphi' means 'both' (both water and land).",
        hint2Eng: "Think: can a grown frog swim in water AND hop on land?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Amphibians live both in water and on land.",
        analogyEng: "They have two homes: water and land!",
        acceptableAnswers: ["Yes", "yes", "true", "moist skin"],
        options: ["Yes", "No"]
      }
    ]
  },

  "science_p6_reptile": {
    statementEng: "Write one feature of the reptile animal group.",
    hintsEng: [
      "Think of snakes, lizards, crocodiles, and turtles.",
      "Reptiles have dry skin covered in tough waterproof scales.",
      "Feature: Scales! "
    ],
    explainEng: {
      messageEng: "Reptiles have dry skin covered with protective scales that prevent them from drying out!",
      questionEng: "What protects a snake or crocodile's skin?"
    },
    steps: [
      {
        questionEng: "What animal is shown as an example for the reptile group?",
        socraticPromptEng: "Which legless reptile slithers silently on the ground?",
        hint1Eng: "It makes a 'hisss' sound.",
        hint2Eng: "It has a long body and no legs.",
        hint3Eng: "Choose 'Snake'.",
        explainEng: "A snake is a reptile.",
        analogyEng: "A snake slithering smoothly through the grass.",
        acceptableAnswers: ["Snake", "snake"],
        options: ["Snake", "Frog", "Bird", "Elephant"]
      },
      {
        questionEng: "Look closely at the snake's body. What covering does it have?",
        socraticPromptEng: "What tough, dry plates cover a reptile's skin?",
        hint1Eng: "It is not fur and not feathers.",
        hint2Eng: "Think of the small, tough, waterproof plates on a reptile.",
        hint3Eng: "Choose 'Scales'.",
        explainEng: "Reptiles are covered in dry scales.",
        analogyEng: "Tiny overlapping armor plates that keep water inside!",
        acceptableAnswers: ["Scales", "scales", "scale"],
        options: ["Scales", "Feathers", "Hair"]
      }
    ]
  },

  "science_p6_fish": {
    statementEng: "Write one feature of the fish animal group.",
    hintsEng: [
      "Fish live in water all their lives.",
      "They have fins to swim and gills to breathe underwater.",
      "Feature: Gills (or live in water)! "
    ],
    explainEng: {
      messageEng: "Fish live underwater and use gills to absorb oxygen directly from the water!",
      questionEng: "What organ helps fish breathe underwater without lungs?"
    },
    steps: [
      {
        questionEng: "Where do fish live for their entire lives?",
        socraticPromptEng: "Do fish live in trees, on land, or in water?",
        hint1Eng: "They swim in oceans, rivers, and ponds.",
        hint2Eng: "Think of rivers and oceans.",
        hint3Eng: "Choose 'In water'.",
        explainEng: "Fish live in water habitats.",
        analogyEng: "Water is a fish's home, swimming free with fins!",
        acceptableAnswers: ["In water", "in water", "water"],
        options: ["In water", "On land", "In trees"]
      },
      {
        questionEng: "What special body part helps fish take oxygen from the water?",
        socraticPromptEng: "Humans use lungs; what do fish have on the sides of their head?",
        hint1Eng: "They look like slits on the sides of the fish's head.",
        hint2Eng: "It starts with 'G' and rhymes with pills.",
        hint3Eng: "Choose 'Gills'.",
        explainEng: "Fish breathe through gills.",
        analogyEng: "Gills work like magic underwater filters for oxygen!",
        acceptableAnswers: ["Gills", "gills", "gill"],
        options: ["Gills", "Lungs", "Nose"]
      }
    ]
  },

  "science_p6_invertebrate": {
    statementEng: "What name do we give to animals without a backbone?",
    hintsEng: [
      "Animals with a backbone are called vertebrates.",
      "Put 'in-' at the beginning for animals without a backbone.",
      "Answer: Invertebrates! "
    ],
    explainEng: {
      messageEng: "Animals without backbones are called invertebrates. Most animals on Earth (like insects, spiders, and worms) are invertebrates!",
      questionEng: "What prefix means 'not' when added to vertebrate?"
    },
    steps: [
      {
        questionEng: "What do we call animals that HAVE a backbone?",
        socraticPromptEng: "Animals with a spine (like humans, dogs, and birds) are called what?",
        hint1Eng: "It starts with 'V'.",
        hint2Eng: "Think of vertebrae (backbone bones).",
        hint3Eng: "Choose 'Vertebrates'.",
        explainEng: "Animals with backbones are vertebrates.",
        analogyEng: "Vertebrae are the spine bones in your back!",
        acceptableAnswers: ["Vertebrates", "vertebrates", "vertebrate"],
        options: ["Vertebrates", "Invertebrates", "Plants"]
      },
      {
        questionEng: "If an animal does NOT have a backbone, does it belong to the vertebrate group?",
        socraticPromptEng: "Can an animal with no backbone be a vertebrate?",
        hint1Eng: "Vertebrates must have a backbone.",
        hint2Eng: "Think: does an animal without spine bones fit in the backbone group?",
        hint3Eng: "Choose 'No'.",
        explainEng: "Animals without backbones belong to a different group.",
        analogyEng: "Like entering a different club with no bones required!",
        acceptableAnswers: ["No", "no", "false", "n"],
        options: ["No", "Yes"]
      },
      {
        questionEng: "What scientific name do we give to animals WITHOUT a backbone?",
        socraticPromptEng: "Add 'in-' to vertebrate to mean 'without backbone'.",
        hint1Eng: "It begins with 'In-'.",
        hint2Eng: "Add the prefix 'in-' to the word vertebrate.",
        hint3Eng: "Choose 'Invertebrates'.",
        explainEng: "Animals without backbones are invertebrates.",
        analogyEng: "Insects, octopuses, and snails are all proud invertebrates!",
        acceptableAnswers: ["Invertebrates", "invertebrates", "invertebrate"],
        options: ["Invertebrates", "Vertebrates", "Mammals"]
      }
    ]
  },

  // =========================================================================
  // SCIENCE PAGE 44: Producers and Consumers
  // =========================================================================

  "science_p44_a_plant_part": {
    statementEng: "Label the part of this plant that makes its food.",
    hintsEng: [
      "Look at the green, flat parts of the plant catching sunlight.",
      "Plants use their leaves for photosynthesis.",
      "Answer: Leaf (or Leaves)! "
    ],
    explainEng: {
      messageEng: "Leaves contain green chlorophyll that absorbs sunlight to make food for the plant!",
      questionEng: "Which part of the plant catches the most sunlight?"
    },
    steps: [
      {
        questionEng: "Which green part of the plant catches sunlight?",
        socraticPromptEng: "What flat green parts grow from plant stems?",
        hint1Eng: "They are green and spread out to catch rays of sun.",
        hint2Eng: "It starts with 'L' and falls from trees in autumn.",
        hint3Eng: "Choose 'Leaf'.",
        explainEng: "Leaves catch sunlight.",
        analogyEng: "Leaves act like tiny solar panels on a house!",
        acceptableAnswers: ["Leaf", "leaf", "leaves"],
        options: ["Leaf", "Roots", "Stem", "Flower"]
      },
      {
        questionEng: "Inside the leaf, what does the plant make using sunlight and water?",
        socraticPromptEng: "Does the plant make food or rocks?",
        hint1Eng: "Plants create energy to grow.",
        hint2Eng: "It is the nourishment that all living things need to live.",
        hint3Eng: "Choose 'Food'.",
        explainEng: "Plants produce their own food inside their leaves.",
        analogyEng: "The leaf is the plant's natural kitchen!",
        acceptableAnswers: ["Food", "food", "its food", "sugar"],
        options: ["Food", "Rocks", "Soil"]
      },
      {
        questionEng: "So which plant part should we label as the food-making part?",
        socraticPromptEng: "What is the name of this food-making part?",
        hint1Eng: "The green part on the stem.",
        hint2Eng: "The flat green solar panel of the plant.",
        hint3Eng: "Answer: Leaf.",
        explainEng: "The leaf makes the plant's food.",
        analogyEng: "A green leaf kitchen making sweet plant food!",
        acceptableAnswers: ["Leaf", "leaf", "leaves"],
        options: ["Leaf", "Roots", "Bark"]
      }
    ]
  },

  "science_p44_b_plant_eater": {
    statementEng: "Circle the living thing that is most likely to eat this plant.",
    hintsEng: [
      "Look at the choices: Owl (A), Cabbage (B), Rabbit (C), Eagle (D).",
      "Owls and eagles eat small animals. Rabbits eat plants!",
      "Answer: Rabbit (C)! "
    ],
    explainEng: {
      messageEng: "Rabbits are herbivores that love eating green plants like cabbage and carrots!",
      questionEng: "Which animal in the picture eats vegetables?"
    },
    steps: [
      {
        questionEng: "Which choices in the worksheet are animals?",
        socraticPromptEng: "Which ones can move around and are not plants?",
        hint1Eng: "Look at the four pictures: which ones are creatures that can move?",
        hint2Eng: "There are two flying birds and one furry hopper.",
        hint3Eng: "Choose 'Owl, rabbit, eagle'.",
        explainEng: "The owl, rabbit, and eagle are the animals.",
        analogyEng: "Animals can run or fly, plants are rooted in place.",
        acceptableAnswers: ["Owl, rabbit, eagle", "owl, rabbit, eagle"],
        options: ["Owl, rabbit, eagle", "Only cabbage", "Only rabbit"]
      },
      {
        questionEng: "Which animal is famous for eating green leaves and vegetables?",
        socraticPromptEng: "Does an owl eat cabbage, or does a rabbit?",
        hint1Eng: "It has long ears and hops.",
        hint2Eng: "Think of the furry garden visitor with long ears and a twitchy nose.",
        hint3Eng: "Choose 'Rabbit'.",
        explainEng: "Rabbits eat plants and vegetables.",
        analogyEng: "A hungry bunny munching on fresh green cabbage leaves!",
        acceptableAnswers: ["Rabbit", "rabbit"],
        options: ["Rabbit", "Owl", "Eagle"]
      },
      {
        questionEng: "Which letter on the worksheet represents the rabbit?",
        socraticPromptEng: "Check the letter label next to the rabbit.",
        hint1Eng: "A is Owl, B is Cabbage, C is Rabbit, D is Eagle.",
        hint2Eng: "Look at the third letter of the alphabet.",
        hint3Eng: "Choose 'C'.",
        explainEng: "Letter C marks the rabbit.",
        analogyEng: "C is for Cottontail rabbit!",
        acceptableAnswers: ["C", "c", "Rabbit", "C (Rabbit)"],
        options: ["C (Rabbit)", "A (Owl)", "B (Cabbage)", "D (Eagle)"]
      }
    ]
  },

  "science_p44_c_i_producer": {
    statementEng: "Which living thing makes its own food?",
    hintsEng: [
      "Living things that make their own food are green plants.",
      "Cabbage (B) is a plant that uses sunlight to make food.",
      "Answer: B (Cabbage)! "
    ],
    explainEng: {
      messageEng: "Plants are producers because they produce their own food from sunlight, water, and air!",
      questionEng: "Which of the four pictures is a plant?"
    },
    steps: [
      {
        questionEng: "Which option on the worksheet is a green plant?",
        socraticPromptEng: "Find the vegetable in the picture.",
        hint1Eng: "It is green and grows in the garden.",
        hint2Eng: "It is a leafy round vegetable.",
        hint3Eng: "Choose 'Cabbage'.",
        explainEng: "Cabbage is a green plant.",
        analogyEng: "Cabbage leaves growing in rich soil.",
        acceptableAnswers: ["Cabbage", "cabbage", "B", "b"],
        options: ["Cabbage", "Rabbit", "Owl", "Eagle"]
      },
      {
        questionEng: "Do green plants make their own food using sunlight?",
        socraticPromptEng: "Can cabbage make food through photosynthesis?",
        hint1Eng: "Plants use sunlight to make food.",
        hint2Eng: "Think: can green leaves capture solar energy to produce food?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Plants make their own food.",
        analogyEng: "Cooking up sugars using sunshine!",
        acceptableAnswers: ["Yes", "yes", "true"],
        options: ["Yes", "No"]
      },
      {
        questionEng: "Which letter represents the cabbage producer?",
        socraticPromptEng: "What letter is next to the cabbage?",
        hint1Eng: "Check the letter beside the cabbage picture.",
        hint2Eng: "It is the second letter of the alphabet.",
        hint3Eng: "Answer: B.",
        explainEng: "Option B is the cabbage producer.",
        analogyEng: "B is our green producer!",
        acceptableAnswers: ["B", "b", "Cabbage", "B (Cabbage)"],
        options: ["B (Cabbage)", "A (Owl)", "C (Rabbit)", "D (Eagle)"]
      }
    ]
  },

  "science_p44_c_ii_eat_animals": {
    statementEng: "Which living things eat other animals?",
    hintsEng: [
      "Predators hunt other animals for food.",
      "The owl (A) and eagle (D) are hunters that eat mice and rabbits.",
      "Answer: A and D (Owl and Eagle)! "
    ],
    explainEng: {
      messageEng: "Owls and eagles are carnivores/predators that hunt and eat other animals like rabbits and rodents!",
      questionEng: "Which birds in the picture are hunters?"
    },
    steps: [
      {
        questionEng: "Which animals in the picture are birds of prey that hunt other animals?",
        socraticPromptEng: "Do owls and eagles hunt small animals for food?",
        hint1Eng: "Both have sharp beaks and talons for hunting.",
        hint2Eng: "Think of the two flying birds with keen eyes and sharp claws.",
        hint3Eng: "Choose 'Owl and eagle'.",
        explainEng: "Owls and eagles hunt other animals.",
        analogyEng: "Soaring high in the sky to spot mice and rabbits!",
        acceptableAnswers: ["Owl and eagle", "owl and eagle", "owl & eagle", "a and d"],
        options: ["Owl and eagle", "Rabbit and cabbage", "Only cabbage"]
      },
      {
        questionEng: "Does cabbage eat other animals?",
        socraticPromptEng: "Does a cabbage vegetable hunt animals?",
        hint1Eng: "Cabbage is a plant, not a predator!",
        hint2Eng: "Think: do vegetables eat animals?",
        hint3Eng: "Choose 'No'.",
        explainEng: "Cabbage never eats animals.",
        analogyEng: "A quiet garden vegetable minding its own business!",
        acceptableAnswers: ["No", "no", "false"],
        options: ["No", "Yes"]
      },
      {
        questionEng: "Which letters represent the owl and eagle?",
        socraticPromptEng: "Look at the labels for the owl and eagle.",
        hint1Eng: "Owl is A, Eagle is D.",
        hint2Eng: "Find the two letters corresponding to the birds.",
        hint3Eng: "Choose 'A and D'.",
        explainEng: "A and D represent the animal eaters.",
        analogyEng: "A and D are our feathered hunters!",
        acceptableAnswers: ["A and D", "a and d", "A, D", "a, d", "A & D"],
        options: ["A and D (Owl and eagle)", "B and C", "A and B", "C and D"]
      }
    ]
  },

  "science_p44_c_iii_consumers": {
    statementEng: "Which living things are consumers?",
    hintsEng: [
      "Consumers cannot make their own food; they must eat other living things.",
      "All the animals (Owl A, Rabbit C, Eagle D) are consumers!",
      "Answer: A, C and D! "
    ],
    explainEng: {
      messageEng: "Living things that eat other organisms are called consumers. Animals are consumers; plants are producers!",
      questionEng: "Are animals producers or consumers?"
    },
    steps: [
      {
        questionEng: "Which option is the PRODUCER that makes its own food?",
        socraticPromptEng: "Which one is the green plant?",
        hint1Eng: "It is the cabbage.",
        hint2Eng: "Find the only plant on the page.",
        hint3Eng: "Choose 'Cabbage (B)'.",
        explainEng: "Cabbage is the producer.",
        analogyEng: "The producer produces food!",
        acceptableAnswers: ["Cabbage", "cabbage", "B", "b"],
        options: ["B (Cabbage)", "A (Owl)", "C (Rabbit)", "D (Eagle)"]
      },
      {
        questionEng: "Do consumers need to eat other living things to get energy?",
        socraticPromptEng: "Can animals make food from sunlight, or must they eat?",
        hint1Eng: "Animals cannot do photosynthesis.",
        hint2Eng: "Think: must animals consume food to survive?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Consumers consume (eat) other living things.",
        analogyEng: "Eating breakfast gives animals their energy!",
        acceptableAnswers: ["Yes", "yes", "true", "eats others"],
        options: ["Yes (they eat others)", "No (they make food)"]
      },
      {
        questionEng: "Which animals in the picture must eat other living things to survive?",
        socraticPromptEng: "Name all the animals: owl, rabbit, eagle.",
        hint1Eng: "The rabbit eats cabbage, and the owl and eagle eat small animals.",
        hint2Eng: "All three animals must eat food.",
        hint3Eng: "Choose 'Owl, rabbit, eagle'.",
        explainEng: "All three animals are consumers.",
        analogyEng: "A food chain of hungry consumers!",
        acceptableAnswers: ["Owl, rabbit, eagle", "owl, rabbit, eagle"],
        options: ["Owl, rabbit, eagle", "Only cabbage", "Only eagle"]
      },
      {
        questionEng: "Which letters represent all three consumers?",
        socraticPromptEng: "Combine the letters for owl, rabbit, and eagle.",
        hint1Eng: "Owl = A, Rabbit = C, Eagle = D.",
        hint2Eng: "Name all the letters except the plant B.",
        hint3Eng: "Choose 'A, C and D'.",
        explainEng: "A, C and D are all consumers.",
        analogyEng: "Every letter except the plant B!",
        acceptableAnswers: ["A, C and D", "a, c and d", "A, C, D", "a, c, d", "A C D"],
        options: ["A, C and D", "A and B", "Only B", "All of them"]
      }
    ]
  },

  "science_p44_d_producer_word": {
    statementEng: "Write one scientific word for living things that make their own food.",
    hintsEng: [
      "Think about the word 'produce' which means to make.",
      "Living things that produce their own food are called producers.",
      "Scientific word: Producers! "
    ],
    explainEng: {
      messageEng: "In science, green plants that produce food using solar energy are called 'producers'!",
      questionEng: "What word comes from 'produce'?"
    },
    steps: [
      {
        questionEng: "What type of living thing can make its own food using sunlight?",
        socraticPromptEng: "Are they animals, plants, or rocks?",
        hint1Eng: "They have green leaves and roots.",
        hint2Eng: "They grow in soil and have green leaves.",
        hint3Eng: "Choose 'A plant'.",
        explainEng: "Plants make their own food.",
        analogyEng: "Green plants soaking up sunshine!",
        acceptableAnswers: ["A plant", "plant", "plants", "a plant"],
        options: ["A plant", "An animal", "A rock"]
      },
      {
        questionEng: "What scientific word describes an organism that produces its own food?",
        socraticPromptEng: "If they 'produce' food, what are they called?",
        hint1Eng: "The word starts with 'Produce-'.",
        hint2Eng: "Add '-er' to the word produce.",
        hint3Eng: "Choose 'Producer'.",
        explainEng: "An organism that makes food is a producer.",
        analogyEng: "A solar chef producing delicious meals!",
        acceptableAnswers: ["Producer", "producer"],
        options: ["Producer", "Consumer", "Predator"]
      },
      {
        questionEng: "What is the plural scientific word for living things that make their own food?",
        socraticPromptEng: "Add an 's' to producer.",
        hint1Eng: "More than one producer.",
        hint2Eng: "Add an 's' to the end of producer.",
        hint3Eng: "Write 'Producers'.",
        explainEng: "Plural: producers.",
        analogyEng: "All green plants together are the producers of the Earth!",
        acceptableAnswers: ["Producers", "producers", "producer"],
        options: ["Producers", "Consumers", "Herbivores"]
      }
    ]
  },

  // =========================================================================
  // SCIENCE GRADE 1-2: Senses & Living Things
  // =========================================================================

  "science_g1_eyes": {
    statementEng: "Which sense organ do we use to see colors, lights, and shapes?",
    hintsEng: [
      "You have two of them on your face.",
      "You close them when you sleep and blink with them.",
      "Sense organ: Eyes (sense of sight)! "
    ],
    explainEng: {
      messageEng: "Our eyes let us see colors, rainbows, and words in books. Our sense is called sight!",
      questionEng: "What happens when you close your eyes?"
    },
    steps: [
      {
        questionEng: "Which part of your face do you use to look at picture books and colors?",
        socraticPromptEng: "What body parts on your face open up so you can see?",
        hint1Eng: "You blink with them.",
        hint2Eng: "They sit above your nose and below your forehead.",
        hint3Eng: "Choose 'Eyes'.",
        explainEng: "We use our eyes to see.",
        analogyEng: "Two wonderful windows to the world!",
        acceptableAnswers: ["Eyes", "eyes", "eye"],
        options: ["Eyes", "Ears", "Nose"]
      },
      {
        questionEng: "What sense do our eyes give us?",
        socraticPromptEng: "Is it sight, hearing, or smell?",
        hint1Eng: "The ability to see is called sight.",
        hint2Eng: "It rhymes with light and lets you see!",
        hint3Eng: "Choose 'Sight'.",
        explainEng: "Our eyes give us the sense of sight.",
        analogyEng: "Looking at a brilliant rainbow in the sky!",
        acceptableAnswers: ["Sight", "sight", "see", "vision"],
        options: ["Sight", "Hearing", "Smell"]
      }
    ]
  },

  "science_g1_ears": {
    statementEng: "Which body part helps us hear music and bird songs?",
    hintsEng: [
      "You have one on each side of your head.",
      "They catch sound waves so you can hear.",
      "Body part: Ears (sense of hearing)! "
    ],
    explainEng: {
      messageEng: "Our ears catch sound vibrations and send them to our brain so we can hear songs, speech, and laughter!",
      questionEng: "Which body parts are you covering when you put on headphones?"
    },
    steps: [
      {
        questionEng: "What body parts on the sides of your head listen to sounds?",
        socraticPromptEng: "What do you listen to your teacher or music with?",
        hint1Eng: "You have two of them on the sides of your head.",
        hint2Eng: "They begin with 'E' and catch sounds.",
        hint3Eng: "Choose 'Ears'.",
        explainEng: "We listen with our ears.",
        analogyEng: "Two satellite dishes catching sound waves!",
        acceptableAnswers: ["Ears", "ears", "ear"],
        options: ["Ears", "Eyes", "Mouth"]
      },
      {
        questionEng: "Can our ears hear both loud sounds and quiet whispers?",
        socraticPromptEng: "Can you hear a drum beat and also a tiny secret whisper?",
        hint1Eng: "Ears are very sensitive to all volume levels.",
        hint2Eng: "Think: can healthy ears pick up loud and soft noises?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Our ears detect loud thunder and soft whispers alike.",
        analogyEng: "From a loud lion roar to a quiet mouse squeak!",
        acceptableAnswers: ["Yes", "yes", "true"],
        options: ["Yes", "No"]
      }
    ]
  },

  "science_g1_nose": {
    statementEng: "Which body part do we use to smell flowers and delicious food?",
    hintsEng: [
      "It sits right in the middle of your face.",
      "It has two nostrils to breathe and smell.",
      "Body part: Nose (sense of smell)! "
    ],
    explainEng: {
      messageEng: "Our nose detects pleasant scents like flowers and warns us of bad smells like smoke!",
      questionEng: "What do you sniff with when cookies are baking?"
    },
    steps: [
      {
        questionEng: "Which facial feature do you use to smell freshly baked cookies or flowers?",
        socraticPromptEng: "What do you sniff with in the center of your face?",
        hint1Eng: "It has two nostrils.",
        hint2Eng: "It is between your eyes and above your mouth.",
        hint3Eng: "Choose 'Nose'.",
        explainEng: "We smell through our nose.",
        analogyEng: "Sniffing a sweet red rose in the garden!",
        acceptableAnswers: ["Nose", "nose"],
        options: ["Nose", "Tongue", "Ears"]
      },
      {
        questionEng: "Does your nose also help you breathe fresh air into your lungs?",
        socraticPromptEng: "Take a deep breath in through your nostrils: does air enter?",
        hint1Eng: "You breathe through your nose every few seconds.",
        hint2Eng: "Inhale right now: did air pass through your nostrils?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Our nose is for smelling and breathing.",
        analogyEng: "A built-in air filter for your body!",
        acceptableAnswers: ["Yes", "yes", "true"],
        options: ["Yes", "No"]
      }
    ]
  },

  "science_g1_tongue": {
    statementEng: "Which organ inside our mouth helps us taste sweet, sour, or salty food?",
    hintsEng: [
      "It is pink, soft, and inside your mouth.",
      "It is covered in tiny taste buds.",
      "Organ: Tongue (sense of taste)! "
    ],
    explainEng: {
      messageEng: "Our tongue is covered in thousands of tiny taste buds that detect sweet, sour, salty, and bitter flavors!",
      questionEng: "Which part of your mouth touches ice cream when you lick it?"
    },
    steps: [
      {
        questionEng: "Which organ inside your mouth tastes the sweetness of ripe mangoes?",
        socraticPromptEng: "What soft muscle inside your mouth licks an ice cream cone?",
        hint1Eng: "It is covered in tiny taste buds.",
        hint2Eng: "It is pink, flexible, and rests behind your teeth.",
        hint3Eng: "Choose 'Tongue'.",
        explainEng: "We taste flavors using our tongue.",
        analogyEng: "Your tongue tells your brain: 'Yum, this is sweet!'",
        acceptableAnswers: ["Tongue", "tongue"],
        options: ["Tongue", "Teeth", "Lips"]
      },
      {
        questionEng: "Is taste one of our five wonderful human senses?",
        socraticPromptEng: "Sight, hearing, smell, taste, touch: is taste one of them?",
        hint1Eng: "We have 5 senses.",
        hint2Eng: "Think: does taste belong to the 5 senses list?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Taste is one of the five human senses.",
        analogyEng: "One of the 5 sensory super-tools!",
        acceptableAnswers: ["Yes", "yes", "true"],
        options: ["Yes", "No"]
      }
    ]
  },

  "science_g1_hands": {
    statementEng: "Which sense organ covers our whole body to feel hot, cold, soft, and rough?",
    hintsEng: [
      "It covers you from head to toe.",
      "Your fingertips use it to feel textures.",
      "Sense organ: Skin (sense of touch)! "
    ],
    explainEng: {
      messageEng: "Our skin is the largest organ in our body. It gives us our sense of touch to feel temperatures and textures!",
      questionEng: "What layer of your body feels a soft blanket?"
    },
    steps: [
      {
        questionEng: "What outer covering on our hands and body lets us feel if something is hot, cold, or soft?",
        socraticPromptEng: "What covers all your muscles and bones?",
        hint1Eng: "It covers your whole body.",
        hint2Eng: "It starts with 'S' and covers your fingers and arms.",
        hint3Eng: "Choose 'Skin'.",
        explainEng: "Our skin provides our sense of touch.",
        analogyEng: "A soft, protective jacket that feels everything you touch!",
        acceptableAnswers: ["Skin", "skin"],
        options: ["Skin", "Hair", "Nails"]
      },
      {
        questionEng: "Can you feel if a puppy's fur is soft using your sense of touch?",
        socraticPromptEng: "When you pet a dog or cat, do your fingers feel the soft fur?",
        hint1Eng: "Your fingertips have sensitive touch sensors.",
        hint2Eng: "Think: can your fingertips detect soft textures?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Touch tells us if something is fluffy, soft, or prickly.",
        analogyEng: "Petting a warm fluffy kitten!",
        acceptableAnswers: ["Yes", "yes", "true"],
        options: ["Yes", "No"]
      }
    ]
  },

  "science_g1_living": {
    statementEng: "Which of these is a living thing that needs food and water to grow?",
    hintsEng: [
      "Living things breathe, eat, drink, and grow bigger.",
      "A kitten grows into a cat; a stone stays the same forever.",
      "Answer: Kitten! "
    ],
    explainEng: {
      messageEng: "Living things (like plants and animals) need food and water to grow. Non-living things (like stones and toys) do not grow!",
      questionEng: "Does a toy or a rock ever need a drink of water to stay alive?"
    },
    steps: [
      {
        questionEng: "Does a little kitten need milk, water, and food to grow into a big cat?",
        socraticPromptEng: "Do baby animals need to eat and drink to grow?",
        hint1Eng: "All baby animals need food to get bigger.",
        hint2Eng: "Think: do baby pets need food and water to live and grow?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Living animals need nutrition to grow.",
        analogyEng: "A kitten drinks milk and plays every day!",
        acceptableAnswers: ["Yes", "yes", "true"],
        options: ["Yes", "No"]
      },
      {
        questionEng: "Does a stone or rock in your garden need food to grow bigger?",
        socraticPromptEng: "Does a rock eat food or stay the exact same size?",
        hint1Eng: "Rocks are non-living objects.",
        hint2Eng: "Think: does a rock have a mouth, stomach, or life?",
        hint3Eng: "Choose 'No'.",
        explainEng: "Stones are non-living and do not eat.",
        analogyEng: "A stone sits still for hundreds of years without eating!",
        acceptableAnswers: ["No", "no", "false"],
        options: ["No", "Yes"]
      },
      {
        questionEng: "So which one is the LIVING thing: the kitten or the stone?",
        socraticPromptEng: "Which one breathes, moves, and grows?",
        hint1Eng: "The furry animal.",
        hint2Eng: "The purring pet that plays with yarn.",
        hint3Eng: "Choose 'Kitten'.",
        explainEng: "The kitten is a living thing.",
        analogyEng: "Living creatures are full of life, energy, and growth!",
        acceptableAnswers: ["Kitten", "kitten", "cat"],
        options: ["Kitten", "Stone"]
      }
    ]
  },

  // =========================================================================
  // SCIENCE GRADE 2-3: Plants, Habitats & States of Matter
  // =========================================================================

  "science_g2_plant_needs": {
    statementEng: "What essential things from nature do green plants need to grow healthy?",
    hintsEng: [
      "Plants need sunlight, water, air, and soil.",
      "Without water and sun, plants wilt and cannot make food.",
      "Answer: Water and sunlight! "
    ],
    explainEng: {
      messageEng: "Plants need water from the soil and sunlight from the sky to grow strong and make food through photosynthesis!",
      questionEng: "What happens to a houseplant if you never water it?"
    },
    steps: [
      {
        questionEng: "Do green plants need sunlight shining from the sky to grow?",
        socraticPromptEng: "Can a plant grow healthy if it is locked in a dark closet?",
        hint1Eng: "Leaves use sunlight as energy.",
        hint2Eng: "Think: can leaves make food in pitch darkness?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Sunlight powers plant growth.",
        analogyEng: "Sunlight is like battery power for green leaves!",
        acceptableAnswers: ["Yes", "yes", "true"],
        options: ["Yes", "No"]
      },
      {
        questionEng: "What liquid must we give plants so they do not dry up and wilt?",
        socraticPromptEng: "What do you pour into the plant pot: water, oil, or juice?",
        hint1Eng: "It falls from rain clouds.",
        hint2Eng: "It is the clear natural liquid that falls as rain.",
        hint3Eng: "Choose 'Water'.",
        explainEng: "Water keeps plant stems crisp and carries soil nutrients.",
        analogyEng: "Roots drink fresh water like drinking through straws!",
        acceptableAnswers: ["Water", "water", "water and sunlight"],
        options: ["Water", "Oil", "Juice"]
      }
    ]
  },

  "science_g2_plant_parts": {
    statementEng: "Which part of the plant grows underground to absorb water?",
    hintsEng: [
      "Roots spread out in the dark soil underneath the plant.",
      "They drink water and anchor the plant in place.",
      "Answer: Roots! "
    ],
    explainEng: {
      messageEng: "Roots grow underground to anchor the plant securely in the dirt and absorb water and nutrients!",
      questionEng: "Which underground plant parts act like drinking straws?"
    },
    steps: [
      {
        questionEng: "Which plant part stays hidden underground in the soil to drink water?",
        socraticPromptEng: "What spreads out under the dirt beneath the stem?",
        hint1Eng: "They anchor the plant and drink moisture.",
        hint2Eng: "They grow downward beneath the soil.",
        hint3Eng: "Choose 'Roots'.",
        explainEng: "Roots absorb water from the ground.",
        analogyEng: "Like an underground network of tiny drinking straws!",
        acceptableAnswers: ["Roots", "roots", "root"],
        options: ["Roots", "Leaves", "Flower"]
      },
      {
        questionEng: "What strong part stands above ground to hold up the leaves and flowers?",
        socraticPromptEng: "What is the green stalk in the middle called?",
        hint1Eng: "Water travels up through this stalk.",
        hint2Eng: "It is the central stalk of the plant.",
        hint3Eng: "Choose 'Stem'.",
        explainEng: "The stem holds the plant upright towards the sunlight.",
        analogyEng: "The sturdy trunk or backbone of the plant!",
        acceptableAnswers: ["Stem", "stem", "stems"],
        options: ["Stem", "Roots", "Fruit"]
      }
    ]
  },

  "science_g2_habitats": {
    statementEng: "Where is the natural habitat of a fish?",
    hintsEng: [
      "Fish have fins and gills made for swimming.",
      "They live in ponds, lakes, rivers, and oceans.",
      "Natural habitat: In water! "
    ],
    explainEng: {
      messageEng: "A habitat is a living thing's natural home. Fish have gills and fins that require a water habitat!",
      questionEng: "Can a goldfish survive in a tree or on dry grass?"
    },
    steps: [
      {
        questionEng: "Can a fish breathe air and survive on dry land?",
        socraticPromptEng: "Do fish have lungs like humans to walk on land?",
        hint1Eng: "Fish need water to breathe through their gills.",
        hint2Eng: "Think: can a fish breathe without water?",
        hint3Eng: "Choose 'No'.",
        explainEng: "Fish gills collapse on dry land.",
        analogyEng: "Fish are built specifically for aquatic life!",
        acceptableAnswers: ["No", "no", "false"],
        options: ["No", "Yes"]
      },
      {
        questionEng: "What is the natural habitat of fish: in water, in trees, or in the desert?",
        socraticPromptEng: "Where do fish swim happily?",
        hint1Eng: "In rivers, lakes, and oceans.",
        hint2Eng: "Think of where rivers, lakes, and oceans are.",
        hint3Eng: "Choose 'In water'.",
        explainEng: "A fish's natural home is in water.",
        analogyEng: "Gliding through the cool blue water of a coral reef!",
        acceptableAnswers: ["In water", "in water", "water"],
        options: ["In water", "In trees", "In desert"]
      }
    ]
  },

  "science_g3_matter_ice": {
    statementEng: "What happens when solid ice gets warm in the sun?",
    hintsEng: [
      "An ice cube is a solid that keeps its shape.",
      "When warmed by heat or sunlight, it turns into liquid water.",
      "Process name: Melting! "
    ],
    explainEng: {
      messageEng: "Heat causes solid ice to melt into liquid water. This change of state is called melting!",
      questionEng: "What happens to an ice popsicle on a sunny hot day?"
    },
    steps: [
      {
        questionEng: "Is a frozen ice cube a solid, liquid, or gas?",
        socraticPromptEng: "Can you hold an ice cube in your hand? Does it keep its own shape?",
        hint1Eng: "It is hard and keeps its shape until it warms up.",
        hint2Eng: "Things that hold their own fixed shape are in this state.",
        hint3Eng: "Choose 'Solid'.",
        explainEng: "Ice is water in its solid state.",
        analogyEng: "Hard and chilly like a cold brick of crystal!",
        acceptableAnswers: ["Solid", "solid", "solids"],
        options: ["Solid", "Liquid", "Gas"]
      },
      {
        questionEng: "When the ice cube warms up in the sun, does it turn into liquid water?",
        socraticPromptEng: "Does warm sunshine turn ice cubes into water puddles?",
        hint1Eng: "Warmth makes ice turn to water.",
        hint2Eng: "Think: what happens to ice left on the kitchen counter?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Warming ice changes it into liquid water.",
        analogyEng: "Dripping droplets forming a cool puddle!",
        acceptableAnswers: ["Yes", "yes", "true"],
        options: ["Yes", "No"]
      },
      {
        questionEng: "What scientific word describes the change from solid to liquid?",
        socraticPromptEng: "When ice turns into water, we say the ice is ___?",
        hint1Eng: "It starts with 'M'.",
        hint2Eng: "Think of what happens to chocolate or ice cream on a hot day.",
        hint3Eng: "Choose 'Melting'.",
        explainEng: "The change from solid to liquid is called melting.",
        analogyEng: "Melting cheese on a hot pizza, melting ice in the sun!",
        acceptableAnswers: ["Melting", "melting", "melt", "melts"],
        options: ["Melting", "Freezing", "Evaporation"]
      }
    ]
  },

  "science_g3_matter_states": {
    statementEng: "What state of matter is the water we drink?",
    hintsEng: [
      "The three main states of matter are solid, liquid, and gas.",
      "Drinking water flows and takes the shape of its glass.",
      "State of matter: Liquid! "
    ],
    explainEng: {
      messageEng: "Liquids can pour, splash, and flow. Water from the tap is a liquid!",
      questionEng: "Does water take the shape of the cup you pour it into?"
    },
    steps: [
      {
        questionEng: "Can liquid water flow and take the shape of whatever cup or bottle you pour it in?",
        socraticPromptEng: "If you pour water into a round bowl, does it become round?",
        hint1Eng: "Liquids have no fixed shape of their own.",
        hint2Eng: "Think: does pouring water let it match the cup's shape?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Liquids flow and adapt to their container.",
        analogyEng: "Pouring water from a tall pitcher into a wide mug!",
        acceptableAnswers: ["Yes", "yes", "true"],
        options: ["Yes", "No"]
      },
      {
        questionEng: "So what state of matter is drinking water: solid, liquid, or gas?",
        socraticPromptEng: "Is drinking water hard like ice (solid), flowing like juice (liquid), or floating like steam (gas)?",
        hint1Eng: "It pours and flows smoothly.",
        hint2Eng: "Think of the state that flows and splashes.",
        hint3Eng: "Choose 'Liquid'.",
        explainEng: "Water we drink is in the liquid state of matter.",
        analogyEng: "A refreshing glass of cold liquid water!",
        acceptableAnswers: ["Liquid", "liquid", "liquids"],
        options: ["Liquid", "Solid", "Gas"]
      }
    ]
  },

  "science_g3_animal_diet": {
    statementEng: "What kind of food does a cow, rabbit, or horse eat?",
    hintsEng: [
      "Cows graze on pasture grass; rabbits eat carrots and leaves.",
      "Animals that eat ONLY plants are called herbivores.",
      "Answer: Herbivores! "
    ],
    explainEng: {
      messageEng: "Animals that eat only grass, plants, and fruits are herbivores. 'Herb' means plant!",
      questionEng: "Does a cow ever hunt or eat meat?"
    },
    steps: [
      {
        questionEng: "Does a cow, horse, or rabbit eat plants and grass rather than meat?",
        socraticPromptEng: "Do cows eat fresh green grass in the field?",
        hint1Eng: "Cows chew grass and hay all day.",
        hint2Eng: "Think: do farm cows eat green grass and grain?",
        hint3Eng: "Choose 'Yes'.",
        explainEng: "Cows and rabbits eat plants, not meat.",
        analogyEng: "A peaceful pasture of cows grazing on green grass!",
        acceptableAnswers: ["Yes", "yes", "true"],
        options: ["Yes", "No"]
      },
      {
        questionEng: "What scientific name do we give to animals that eat ONLY plants?",
        socraticPromptEng: "Are plant-eaters called herbivores or carnivores?",
        hint1Eng: "'Herb' means plant (like garden herbs).",
        hint2Eng: "It starts with 'Herb-' because they eat herbs and vegetation.",
        hint3Eng: "Choose 'Herbivores'.",
        explainEng: "Plant-eating animals are called herbivores.",
        analogyEng: "Rabbits, elephants, and deer are all gentle herbivores!",
        acceptableAnswers: ["Herbivores", "herbivores", "herbivore"],
        options: ["Herbivores", "Carnivores", "Producers"]
      }
    ]
  }
};

/**
 * Retrieve English pedagogical data for any hardcoded case ID.
 */
export function getEnglishCaseData(caseId: string): CaseEnglishData | undefined {
  return HARDCODED_ENGLISH_PEDAGOGY[caseId];
}
