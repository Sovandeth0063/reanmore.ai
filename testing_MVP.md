# 🧪 ReanMore AI Tutor — MVP Testing Guide & Question Catalog (`testing_MVP.md`)

This guide provides the complete catalog of hardcoded **Math** and **Science** homework exercises, featured demo problems, and account credentials for testing the ReanMore AI Tutor MVP.

---

## 🔑 1. Demo User Accounts & PINs

| Role | Username | Display Name | PIN Code | Access Level |
| :--- | :--- | :--- | :--- | :--- |
| **Student (សិស្ស)** | `sochea` | សុជា (Sochea) | **`1234`** | Grade 4 Student, Homework Exercises, Chat, Profile |
| **Parent (អាណាព្យាបាល)** | `parent` | អ្នកម្តាយ សុជា (Parent) | **`9999`** | Weekly Learning Report, Accuracy Stats, PIN Protected |

> **Quick Login Tip:** On the Login modal, you can simply click the **"ចូលភ្លាមៗ (Login)"** button next to each account card to bypass typing the PIN, or click the preset chips in custom login mode.

---

## 🧮 2. Math Exercises Catalog (31 Exercises Across 3 Homeworks)

### 📘 Math Homework 1 (Page 1 — Multi-Addend Addition & Making 100)

| Case ID | Problem Statement / Trigger | Expected Final Answer | Step-by-Step Question & Answers |
| :--- | :--- | :--- | :--- |
| `math_p1_a1` | `4 + 5 + 6 = ___` | **`15`** | **Step 1:** $4 + 5 = \mathbf{9}$<br>**Step 2:** Add $\mathbf{6}$<br>**Step 3:** $9 + 6 = \mathbf{15}$ |
| `math_p1_a2` | `7 + 3 + 2 + 5 = ___` | **`17`** | **Step 1:** $7 + 3 = \mathbf{10}$<br>**Step 2:** $10 + 2 = \mathbf{12}$<br>**Step 3:** $12 + 5 = \mathbf{17}$ |
| `math_p1_a3` | `8 + 1 + 4 = ___` | **`13`** | **Step 1:** $8 + 1 = \mathbf{9}$<br>**Step 2:** $9 + 4 = \mathbf{13}$ |
| `math_p1_a4` | `9 + 2 + 3 + 1 = ___` | **`15`** | **Step 1:** $9 + 1 = \mathbf{10}$<br>**Step 2:** $2 + 3 = \mathbf{5}$<br>**Step 3:** $10 + 5 = \mathbf{15}$ |
| `math_p1_a5` | `6 + 6 + 4 = ___` | **`16`** | **Step 1:** $6 + 4 = \mathbf{10}$<br>**Step 2:** $10 + 6 = \mathbf{16}$ |
| `math_p1_b1` | `30 + [ ] = 100` | **`70`** | **Step 1:** How many tens in 30? $\mathbf{3}$<br>**Step 2:** Tens to 100: $\mathbf{7}$ tens<br>**Step 3:** $100 - 30 = \mathbf{70}$ |
| `math_p1_b2` | `20 + [ ] = 100` | **`80`** | **Step 1:** How many tens in 20? $\mathbf{2}$<br>**Step 2:** Tens to 100: $\mathbf{8}$ tens<br>**Step 3:** $100 - 20 = \mathbf{80}$ |
| `math_p1_b3` | `35 + [ ] = 100` | **`65`** | **Step 1:** Make next ten (40): $+\mathbf{5}$<br>**Step 2:** 40 to 100: $+\mathbf{60}$<br>**Step 3:** $60 + 5 = \mathbf{65}$ |
| `math_p1_b4` | `48 + [ ] = 100` | **`52`** | **Step 1:** Make next ten (50): $+\mathbf{2}$<br>**Step 2:** 50 to 100: $+\mathbf{50}$<br>**Step 3:** $50 + 2 = \mathbf{52}$ |
| `math_p1_b5` | `67 + [ ] = 100` | **`33`** | **Step 1:** Make next ten (70): $+\mathbf{3}$<br>**Step 2:** 70 to 100: $+\mathbf{30}$<br>**Step 3:** $30 + 3 = \mathbf{33}$ |
| `math_p1_b6` | `54 + [ ] = 100` | **`46`** | **Step 1:** Make next ten (60): $+\mathbf{6}$<br>**Step 2:** 60 to 100: $+\mathbf{40}$<br>**Step 3:** $40 + 6 = \mathbf{46}$ |

---

### 📙 Math Homework 8 (Page 8 — 3-Digit Place Value & Mental Arithmetic)

| Case ID | Problem Statement / Trigger | Expected Final Answer | Step-by-Step Question & Answers |
| :--- | :--- | :--- | :--- |
| `math_p8_a1` | `Hundreds, tens, ones for 146` | **H: 1, T: 4, O: 6**<br>+10: **156**, -10: **136** | **Step 1:** Hundreds = $\mathbf{1}$<br>**Step 2:** Tens = $\mathbf{4}$<br>**Step 3:** Ones = $\mathbf{6}$<br>**Step 4:** $+10 = \mathbf{156}$, $-10 = \mathbf{136}$ |
| `math_p8_a2` | `Hundreds, tens, ones for 308` | **H: 3, T: 0, O: 8**<br>+10: **318**, -10: **298** | **Step 1:** Hundreds = $\mathbf{3}$<br>**Step 2:** Tens = $\mathbf{0}$<br>**Step 3:** Ones = $\mathbf{8}$<br>**Step 4:** $+10 = \mathbf{318}$, $-10 = \mathbf{298}$ |
| `math_p8_a3` | `Hundreds, tens, ones for 235` | **H: 2, T: 3, O: 5**<br>+10: **245**, -10: **225** | **Step 1:** Hundreds = $\mathbf{2}$<br>**Step 2:** Tens = $\mathbf{3}$<br>**Step 3:** Ones = $\mathbf{5}$<br>**Step 4:** $+10 = \mathbf{245}$, $-10 = \mathbf{225}$ |
| `math_p8_a4` | `Hundreds, tens, ones for 472` | **H: 4, T: 7, O: 2**<br>+10: **482**, -10: **462** | **Step 1:** Hundreds = $\mathbf{4}$<br>**Step 2:** Tens = $\mathbf{7}$<br>**Step 3:** Ones = $\mathbf{2}$<br>**Step 4:** $+10 = \mathbf{482}$, $-10 = \mathbf{462}$ |
| `math_p8_b2` | `35 + 9 = ___` | **`44`** | **Step 1:** Add 10: $35 + 10 = \mathbf{45}$<br>**Step 2:** Adjust $-1$: $45 - 1 = \mathbf{44}$ |
| `math_p8_b6` | `74 - 9 = ___` | **`65`** | **Step 1:** Subtract 10: $74 - 10 = \mathbf{64}$<br>**Step 2:** Adjust $+1$: $64 + 1 = \mathbf{65}$ |
| `math_p8_b3` | `58 + 11 = ___` | **`69`** | **Step 1:** Add 10: $58 + 10 = \mathbf{68}$<br>**Step 2:** Adjust $+1$: $68 + 1 = \mathbf{69}$ |
| `math_p8_b7` | `52 - 11 = ___` | **`41`** | **Step 1:** Subtract 10: $52 - 10 = \mathbf{42}$<br>**Step 2:** Adjust $-1$: $42 - 1 = \mathbf{41}$ |
| `math_p8_b4` | `27 + 30 = ___` | **`57`** | **Step 1:** Add 3 tens: $20 + 30 = \mathbf{50}$<br>**Step 2:** Add 7 ones: $50 + 7 = \mathbf{57}$ |
| `math_p8_b8` | `91 - 20 = ___` | **`71`** | **Step 1:** Subtract 2 tens: $90 - 20 = \mathbf{70}$<br>**Step 2:** Add 1 one: $70 + 1 = \mathbf{71}$ |

---

### 📅 Math Homework 16 (Page 16 — Calendar & Time Units)

| Case ID | Problem Statement / Trigger | Expected Final Answer | Step-by-Step Question & Answers |
| :--- | :--- | :--- | :--- |
| `math_p16_a1` | `How many days are in this month?` | **`31`** | **Step 1:** Check last number on calendar: $\mathbf{31}$ |
| `math_p16_a2` | `What day is 14 August?` | **`Friday`** | **Step 1:** Look at column for 14: $\mathbf{Friday}$ |
| `math_p16_a3` | `What date is one week after 8 August?` | **`15 August`** | **Step 1:** Add 7 days: $8 + 7 = \mathbf{15\text{ August}}$ |
| `math_p16_a4` | `Circle 31 August.` | **`31`** | **Step 1:** Locate last day of August: $\mathbf{31}$ |
| `math_p16_b1` | `1 week = ____ days` | **`7`** | **Step 1:** Days in 1 week = $\mathbf{7}$ |
| `math_p16_b2` | `1 fortnight = ____ weeks` | **`2`** | **Step 1:** Weeks in 1 fortnight = $\mathbf{2}$ (14 days) |
| `math_p16_b3` | `1 year = ____ months` | **`12`** | **Step 1:** Months in 1 year = $\mathbf{12}$ |
| `math_p16_b4` | `A common year = ____ days` | **`365`** | **Step 1:** Days in common year = $\mathbf{365}$ |
| `math_p16_b5` | `A leap year = ____ days` | **`366`** | **Step 1:** Days in leap year = $\mathbf{366}$ |
| `math_p16_b6` | `February usually has ____ days` | **`28`** | **Step 1:** Standard February days = $\mathbf{28}$ (29 in leap year) |

---

## 🔬 3. Science Exercises Catalog (18 Exercises Across 3 Pages)

### 🦩 Science Page 8 (Identifying Animals & Morphological Features)

| Case ID | Animal | Features Checked | Step-by-Step Questions & Answers |
| :--- | :--- | :--- | :--- |
| `science_p8_flamingo` | **Flamingo (🦩)** | Backbone, feathers, hump, pincers, wings | 1. Backbone? **`Yes`**<br>2. Body cover? **`Feathers`**<br>3. Hump? **`No`**<br>4. Pincers? **`No`**<br>5. Flying parts? **`Wings`** |
| `science_p8_lobster` | **Lobster (🦞)** | Invertebrate, pincers, shell | 1. Backbone? **`No`**<br>2. Feathers? **`No`**<br>3. Hump? **`No`**<br>4. Claw parts? **`Pincers`**<br>5. Wings? **`No`** |
| `science_p8_camel` | **Camel (🐪)** | Mammal, fur, dorsal hump | 1. Backbone? **`Yes`**<br>2. Feathers? **`No`**<br>3. Back feature? **`Hump`**<br>4. Pincers? **`No`**<br>5. Wings? **`No`** |
| `science_p8_giraffe` | **Giraffe (🦒)** | Mammal, long neck, fur | 1. Backbone? **`Yes`**<br>2. Feathers? **`No`**<br>3. Hump? **`No`**<br>4. Pincers? **`No`**<br>5. Wings? **`No`** |
| `science_p8_slug` | **Slug (🐌)** | Invertebrate, soft body, shell-less | 1. Backbone? **`No`**<br>2. Feathers? **`No`**<br>3. Hump? **`No`**<br>4. Pincers? **`No`**<br>5. Wings? **`No`** |
| `science_p8_moth` | **Moth (🦋)** | Invertebrate, insect, wings | 1. Backbone? **`No`**<br>2. Feathers? **`No`**<br>3. Hump? **`No`**<br>4. Pincers? **`No`**<br>5. Flying parts? **`Wings`** |

---

### 🦎 Science Page 6 (Grouping Animals & Taxonomic Classification)

| Case ID | Class / Group | Key Focus | Step-by-Step Questions & Answers |
| :--- | :--- | :--- | :--- |
| `science_p6_bird` | **Birds** | Feathers & endothermy | 1. Body cover? **`Feathers`**<br>2. Has backbone? **`Yes`** |
| `science_p6_mammal` | **Mammals** | Hair/fur & live birth | 1. Group name? **`Mammal`**<br>2. Body cover? **`Hair or fur`** |
| `science_p6_amphibian` | **Amphibians** | Metamorphosis & moist skin | 1. Animal example? **`Frog`**<br>2. Skin type? **`Moist skin`**<br>3. Distinguishing trait? **`Moist skin`** |
| `science_p6_reptile` | **Reptiles** | Dry scaly skin & ectothermy | 1. Animal example? **`Snake`**<br>2. Skin covering? **`Scales`** |
| `science_p6_fish` | **Fish** | Gills & aquatic habitat | 1. Where do they live? **`In water`**<br>2. Breathing organ? **`Gills`** |
| `science_p6_invertebrate` | **Invertebrates** | Absence of vertebral column | 1. Animals with backbone? **`Vertebrates`**<br>2. Does it have backbone? **`No`**<br>3. Group name? **`Invertebrates`** |

---

### 🌿 Science Page 44 (Producers, Consumers & Ecosystem Energy)

| Case ID | Topic | Question / Prompt | Step-by-Step Questions & Answers |
| :--- | :--- | :--- | :--- |
| `science_p44_a_plant_part` | Plant Food Part | `Label the part of this plant that makes its food.` | 1. Primary food part? **`Leaf`**<br>2. Photosynthesis organ? **`Leaf`**<br>3. Label? **`Leaf`** |
| `science_p44_b_plant_eater` | Herbivore | `Circle the living thing that is most likely to eat this plant.` | 1. Choices: **`Owl, rabbit, eagle`**<br>2. Herbivore animal? **`Rabbit`**<br>3. Letter? **`C`** |
| `science_p44_c_i_producer` | Producers | `Which living thing makes its own food?` | 1. Plant example? **`Cabbage`**<br>2. Makes own food? **`Yes`**<br>3. Letter? **`B`** |
| `science_p44_c_ii_eat_animals` | Carnivores | `Which living things eat other animals?` | 1. Predators: **`Owl and eagle`**<br>2. Do they make food? **`No`**<br>3. Letters? **`A and D`** |
| `science_p44_c_iii_consumers` | Consumers | `Which living things are consumers?` | 1. Plant item: **`Cabbage`**<br>2. What plant does: **`Makes its own food`**<br>3. Consumer animals: **`Owl, rabbit, eagle`**<br>4. Letters: **`A, C and D`** |
| `science_p44_d_producer_word` | Scientific Term | `Write one scientific word for living things that make their own food.` | 1. Organism type: **`A plant`**<br>2. Singular term: **`Producer`**<br>3. Plural term: **`Producers`** |

---

## 🌟 4. Featured Interactive Demo Cards (`mockProblems.ts`)

These problems are accessible directly from the **Home (ទំព័រដើម)** dashboard cards:

| Problem ID | Subject & Grade | Problem Statement (Khmer & English) | Step Answers |
| :--- | :--- | :--- | :--- |
| `math-g4-apples` | **Math** (Grade 4) | *មាន ៥ ប្រអប់។ ប្រអប់នីមួយៗមានផ្លែប៉ោម ៨ ផ្លែ។ តើមានផ្លែប៉ោមសរុបប៉ុន្មានផ្លែ?*<br>(5 boxes, 8 apples each. Total?) | **1.** `5`<br>**2.** `8`<br>**3.** `ការបូក ឬ ការគុណ (Addition or Multiplication)`<br>**4.** `40` |
| `math-g3-perimeter` | **Math** (Grade 3) | *ចតុកោណកែងមួយមានបណ្តោយ 6m និងទទឹង 4m។ តើបរិមាត្រស្មើប៉ុន្មាន?*<br>(Rectangle with length 6m and width 4m. Find perimeter.) | **1.** `20`<br>**2.** `2 * (6 + 4)`<br>**3.** `20` |
| `math-g4-fractions` | **Math** (Grade 4) | *ភីហ្សាមួយត្រូវកាត់ជា ៨ ចំណែកស្មើគ្នា។ បើគេញ៉ាំអស់ ៣ ចំណែក តើសល់ប្រភាគប៉ុន្មាន?*<br>(A pizza has 8 slices. 3 slices were eaten. What fraction remains?) | **1.** `5/8`<br>**2.** `5` |
| `science-g4-water` | **Science** (Grade 4) | *វដ្តទឹក (Water Cycle)៖ តើដំណើរការដែលទឹកប្រែក្លាយជាចំហាយទឹកហៅថាអ្វី?*<br>(Water turning into vapor) | **1.** `ការហួត (Evaporation)`<br>**2.** `ពពក (Clouds)` |
| `science-g5-plants` | **Science** (Grade 5) | *រុក្ខជាតិ និងរស្មីសំយោគ៖ តើរុក្ខជាតិត្រូវការអ្វីខ្លះដើម្បីបង្កើតអាហារ?*<br>(What do plants need for photosynthesis?) | **1.** `ពន្លឺព្រះអាទិត្យ ទឹក និងឧស្ម័នកាបូនិច (Sunlight, Water, CO2)`<br>**2.** `ស្លឹក (Leaves)`<br>**3.** `អុកស៊ីសែន (Oxygen)` |

---

## 🛠️ 5. Automated Validation Command

To verify that all 31 math exercises and 99 steps have 0 answer leakage and 100% pedagogical hint compliance:

```bash
cd frontend
npm run test:hints
```

Expected output:
```text
=== Auditing All 31 Math Exercises Across Homework 1, 8, and 16 ===
Audited 31 math exercises (11 HW1, 10 HW8, 10 HW16) across 99 total steps.
✅ PASSED! All 31 math exercises across all homeworks are 100% complete, non-leaking, and strictly pedagogical.
```
