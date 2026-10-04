# NEET-SS Paediatrics Interactive Quiz — Repository Update Instructions

## Purpose

This repository hosts an interactive NEET-SS + ICP Paediatrics quiz application.

New study-day source files will be provided regularly. Each source file contains MCQ questions, answer keys, and detailed explanations similar to the existing Day 4 source material.

Whenever a new daily source file is provided, update the repository by adding that day as a separate quiz module without modifying or breaking previously completed days.

The expected workflow is:

**Source file → extract questions/answers/explanations → create day folder → divide into quiz sets → update day selector → test → commit → push**

---

# 1. Repository Structure

Keep each study day in a completely separate folder.

Expected structure:

```text
/
├── index.html
├── README.md
├── Day4/
│   ├── index.html
│   ├── quiz1.html
│   ├── quiz2.html
│   ├── quiz3.html
│   ├── quiz4.html
│   └── quiz5.html
├── Day5/
│   ├── index.html
│   ├── quiz1.html
│   ├── quiz2.html
│   ├── quiz3.html
│   ├── quiz4.html
│   └── quiz5.html
├── Day6/
│   └── ...
└── ...
```

Do not mix files from multiple days inside the same folder.

The root `index.html` is only the **Day Selection** page.

Each `DayN/index.html` is only the **Quiz Set Selection** page for that day.

Each `quizN.html` contains one independent interactive quiz.

---

# 2. Source File Handling

A new file will normally be provided for a specific study day.

Examples:

```text
Day_5_xxxxx.docx
Day_6_xxxxx.docx
Day_7_xxxxx.docx
```

The source file may contain:

- Study notes
- Definitions
- Clinical cases
- Exam pearls
- Exam traps
- MCQs
- Answer key
- Detailed explanations

For quiz generation, use the questions, answer key, and explanations from the supplied source file.

Do not silently replace source questions with newly generated questions.

Do not change the intended correct answer unless the source itself is internally inconsistent.

If the source contains an obvious inconsistency between a question, answer key, and explanation:

1. Do not guess silently.
2. Record the conflict.
3. Prefer the detailed explanation only when it clearly resolves the conflict.
4. Add the conflict to the update summary.

---

# 3. Question Extraction

Identify the MCQ section in the source document.

For every question extract:

```json
{
  "num": 1,
  "level": "Basic",
  "question": "Question text",
  "options": [
    "Option A",
    "Option B",
    "Option C",
    "Option D"
  ],
  "answer": 0,
  "explanation": "Detailed explanation",
  "pearl": "Exam pearl if available"
}
```

Answer index convention:

```text
A = 0
B = 1
C = 2
D = 3
```

Preserve:

- Clinical values
- Gestational ages
- Drug doses
- Units
- Symbols
- Percentages
- Correct medical terminology
- Question difficulty labels

Clean only formatting artifacts such as:

- broken line wrapping
- duplicated headers/footers
- page numbers
- malformed spacing
- stray document conversion characters

Do not simplify medical wording merely for convenience.

---

# 4. Number of Questions Per Quiz Set

Applies to every learning-mode test: daily study portals and cumulative mocks.
(Grand Mocks use the official exam sections instead — see §34–36.)

## 4.1 Rule

```text
Default            : 5 sets × 15 questions (75 questions)
More questions     : keep 5 sets and grow each set, up to 20 questions per set (100 questions)
Even more questions: add more sets so that no set exceeds 20 questions
Fewer questions    : sets of at most 15 questions
Balance            : all sets as equal as possible — sizes may differ by at most 1
Order              : contiguous source order (Set 1 = first questions); larger sets come first
```

Number of sets for N questions:

| Total questions (N) | Number of sets | Questions per set |
|---|---|---|
| 1 – 75 | ⌈N ÷ 15⌉ | ≤ 15 |
| 76 – 100 | 5 | 16 – 20 |
| 101 and above | ⌈N ÷ 20⌉ | ≤ 20 |

Then divide N as evenly as possible across the sets (each set gets ⌊N ÷ sets⌋ or ⌊N ÷ sets⌋ + 1).

## 4.2 Examples

| Questions | Sets | Sizes |
|---|---|---|
| 50 | 4 | 13, 13, 12, 12 |
| 60 | 4 | 15, 15, 15, 15 |
| 75 | 5 | 15, 15, 15, 15, 15 |
| 80 | 5 | 16, 16, 16, 16, 16 |
| 90 | 5 | 18, 18, 18, 18, 18 |
| 100 | 5 | 20, 20, 20, 20, 20 |
| 101 | 6 | 17, 17, 17, 17, 17, 16 |
| 120 | 6 | 20 × 6 |
| 150 | 8 | 19, 19, 19, 19, 19, 19, 18, 18 |
| 200 | 10 | 20 × 10 |

Example ranges for 90 questions:

```text
Quiz Set 1 → Q1–18
Quiz Set 2 → Q19–36
Quiz Set 3 → Q37–54
Quiz Set 4 → Q55–72
Quiz Set 5 → Q73–90
```

## 4.3 Requirements

- Never drop or duplicate questions to make sets equal.
- Sets must be contiguous: each set starts immediately after the previous one ends.
- The build applies this automatically: `tools/docx_parse.py → set_sizes()` / `split_sets()`, used by `tools/build_day.py`.
- Show each set's real question range and count on the quiz-set page (e.g. "Questions 19–36 · 18 MCQs").

---

# 5. Root Day Selection Page

The repository root:

```text
/index.html
```

must display the available study days.

Example:

```text
Day 4
Prematurity + ELBW/VLBW + Thermoregulation + Apnea of Prematurity
[Open Day 4]

Day 5
Topic name from source document
[Open Day 5]
```

Day cards should be shown in ascending numerical order.

The link format must be:

```text
Day4/index.html
Day5/index.html
Day6/index.html
```

Do not place quiz-set links directly on the root page.

Navigation must always follow:

```text
Day Selection
      ↓
Quiz Set Selection
      ↓
Interactive Quiz
```

---

# 6. Day Quiz Selection Page

Each day must have:

```text
DayN/index.html
```

It should show:

- Day number
- Main topic/title
- Number of questions
- Number of quiz sets
- Each quiz set
- Question range for each set

Example:

```text
Day 5 — Quiz Sets

Quiz Set 1
Questions 1–15
[Start Quiz Set 1]

Quiz Set 2
Questions 16–30
[Start Quiz Set 2]
```

Include:

```text
← Back to Day List
```

which links to:

```text
../index.html
```

---

# 7. Quiz Behaviour

Each quiz must show one question at a time.

Required interaction:

1. Display question.
2. Display four options.
3. User selects one option.
4. User clicks **Submit Answer**.
5. Immediately evaluate the answer.

If correct:

- selected answer turns green
- show `Correct (+4)`
- show explanation
- show exam pearl if available

If incorrect:

- selected answer turns red
- correct answer turns green
- show `Incorrect (-1)`
- explicitly display the correct answer
- show explanation
- show exam pearl if available

Then show:

```text
Next Question
```

Do not automatically advance before the learner can read the explanation.

---

# 8. NEET-SS Marking

Use:

```text
Correct answer = +4
Wrong answer   = -1
Unanswered     = 0
```

Live display should include:

```text
Question X / 15
Score
Correct count
Wrong count
Progress bar
```

Do not use percentage-based scoring during the quiz.

---

# 9. Finish Quiz Early

Every quiz must contain:

```text
Finish Quiz
```

The user can end the current quiz set at any time.

Before ending, show a confirmation such as:

```text
You have attempted 8 questions.
Finish the quiz now?
```

The final report must calculate results using only attempted questions.

Do not mark unseen questions as wrong.

---

# 10. No Jump-to-Question Feature

Do not include:

- Start from Question N
- Jump to Question
- Question dropdown
- direct question navigation

The learner should proceed sequentially within each quiz set (set sizes per §4).

---

# 11. No Login or Email

Do not request:

- Email
- Username
- Password
- Candidate login

No backend is required.

The quiz should work as a lightweight static website.

It should preferably function when opened locally from disk and when hosted through:

- GitHub Pages
- Netlify
- Cloudflare Pages
- Vercel
- any standard static web server

Avoid unnecessary external JavaScript dependencies.

---

# 12. Final Result Page

At completion, display:

```text
Quiz Set
Attempted questions
Correct
Wrong
Score
Maximum possible score for attempted questions
Percentage
Time taken
```

Example:

```text
Quiz Set 2 Result

Attempted: 15
Correct: 11
Wrong: 4
Score: 40 / 60
Percentage: 66.67%
Time: 12m 41s
```

Calculation:

```text
score = correct × 4 - wrong
maximum = attempted × 4
percentage = score / maximum × 100
```

If attempted count is zero:

```text
percentage = 0
```

---

# 13. Wrong-Answer Review

At the end, show only incorrectly answered questions.

For every wrong question display:

```text
Question number
Question
User answer
Correct answer
Explanation
Exam pearl
```

Example:

```text
Q24. Previously stable preterm infant develops new apnea...

Your answer:
B. Increase caffeine

Correct answer:
A. Evaluate for NEC/sepsis

Explanation:
...

Exam pearl:
New or changing apnea in a preterm infant should trigger evaluation for secondary causes.
```

If there are no wrong answers:

```text
No wrong answers.
```

---

# 14. Downloadable Wrong-Answer Report

Provide:

```text
Download Word
Print / Save PDF
```

The Word report should contain only:

- quiz information
- final score
- wrong-answer questions
- user's answer
- correct answer
- explanation
- exam pearl

Use the browser print dialog for PDF generation where possible.

Avoid heavy client-side PDF libraries unless absolutely required.

---

# 15. Report File Naming

Downloaded reports must use:

```text
Day{N}_QuizSet{S}_Q{START}-{END}_{YYYYMMDD_HHMMSS}_Wrong_Answers
```

Examples:

```text
Day4_QuizSet1_Q1-15_20261002_194530_Wrong_Answers.doc
Day5_QuizSet3_Q31-45_20261004_083512_Wrong_Answers.doc
```

For printable PDF reports, set the document title to the same generated base name so the browser can suggest it when saving.

Timestamp must be generated at download/report time.

---

# 16. UI Requirements

Keep the UI simple, fast, and mobile-friendly.

Use a consistent visual style across every day.

Recommended visual behaviour:

### Correct
Green background/border.

### Wrong
Red background/border.

### Explanation
Neutral light background.

### Exam Pearl
Highlighted box.

### Navigation
Clear buttons:

```text
Quiz Sets
Finish Quiz
Submit Answer
Next Question
Back to Day List
```

Do not overload the interface.

---

# 17. Preserve Existing Days

When adding a new day:

DO NOT modify previously working quiz content unless explicitly requested.

For example, when adding Day 8:

Do not regenerate:

```text
Day4/
Day5/
Day6/
Day7/
```

Only:

1. create `Day8/`
2. update the root day selector
3. update documentation if needed

Changes to shared styling/navigation should be made carefully and tested against existing days.

---

# 18. Validation Before Commit

Before committing, verify all of the following.

## Question integrity

Check:

```text
Total source MCQ count == total generated MCQ count
```

Verify:

- no duplicated questions
- no missing questions
- options A–D preserved
- correct answer mapping preserved
- explanation mapped to the correct question
- question numbering preserved

## Quiz-set integrity

Verify:

```text
Set 1 ends immediately before Set 2 starts
```

There must be no gaps or overlaps.

Example:

```text
Q1–15
Q16–30
Q31–45
```

Correct.

Incorrect:

```text
Q1–15
Q15–30
```

because Q15 is duplicated.

## Functional validation

Test at minimum:

- first question of every quiz set
- last question of every quiz set
- one correct answer
- one wrong answer
- score calculation
- finish-early action
- final wrong-answer review
- Word report download
- Print / Save PDF
- Back to Quiz Sets
- Back to Day List

---

# 19. Lightweight Requirement

The quiz pages must load reliably.

Prefer:

```text
HTML
CSS
Vanilla JavaScript
```

Avoid adding frameworks unless there is a clear requirement.

Do not require:

```text
React
Angular
Vue
Node runtime
database
server backend
login service
email service
```

for the current application.

If the repository already uses a framework, follow the existing architecture rather than introducing a second architecture.

---

# 20. Git Workflow

Before making changes:

```bash
git status
git branch --show-current
git pull --rebase
```

Inspect the existing repository structure before creating files.

Do not overwrite unrelated local changes.

If the working tree contains user changes:

- preserve them
- do not reset them
- do not run destructive Git commands

Never use destructive commands such as:

```bash
git reset --hard
git clean -fd
```

unless explicitly instructed.

---

# 21. Branch Behaviour

If repository policy allows direct commits to the current branch, use the current branch.

If the repository normally uses feature branches, create:

```text
quiz/day-N
```

Example:

```bash
git checkout -b quiz/day-5
```

Follow existing repository contribution rules if they differ.

---

# 22. Commit Message

Use a clear commit message.

Examples:

```text
feat(quiz): add Day 5 interactive MCQ sets
```

```text
feat(quiz): add Day 6 NEET-SS paediatrics quizzes
```

If updating an existing day:

```text
fix(quiz): correct Day 5 answer explanations
```

---

# 23. Push Changes

After validation:

```bash
git status
git diff --check
git diff
```

Then:

```bash
git add <only relevant files>
git commit -m "feat(quiz): add Day N interactive MCQ sets"
git push
```

If working on a newly created branch:

```bash
git push -u origin quiz/day-N
```

Do not stage unrelated files.

---

# 24. Post-Push Verification

After pushing:

1. Confirm the remote push succeeded.
2. If GitHub Pages or another static deployment is configured, verify deployment status where possible.
3. Verify the root Day Selection page includes the newly added day.
4. Verify the new day page opens.
5. Verify all quiz-set links work.

---

# 25. Update Summary

After completing the repository update, return a concise summary in this format:

```text
Day added:
Day 5

Topic:
[topic]

Questions imported:
75

Quiz sets:
5

Ranges:
Set 1: Q1–15
Set 2: Q16–30
Set 3: Q31–45
Set 4: Q46–60
Set 5: Q61–75

Files added:
Day5/index.html
Day5/quiz1.html
Day5/quiz2.html
Day5/quiz3.html
Day5/quiz4.html
Day5/quiz5.html

Root navigation:
Updated

Validation:
Passed

Commit:
<commit hash>

Pushed:
Yes

Remote branch:
<branch>
```

If something fails, state exactly what failed.

Do not claim a successful push unless the Git command actually succeeded.

---

# 26. Handling Future Daily Updates

When a new source document is supplied, determine the day number and topic from the document itself.

Then perform:

```text
1. Read source document
2. Identify MCQ section
3. Identify answer key
4. Identify detailed explanations
5. Cross-check question-to-answer mapping
6. Extract all questions
7. Create DayN folder
8. Split questions into quiz sets per §4 (default 5 × 15, up to 20 per set, sizes within ±1)
9. Generate DayN/index.html
10. Generate quiz pages
11. Update root index.html
12. Validate question counts
13. Test quiz functionality
14. Review git diff
15. Commit
16. Push
17. Report results
```

Do not ask the user to manually repeat information already available in the supplied source file or repository.

---

# 27. Important Medical Content Rule

The source material is exam-preparation content.

Do not casually alter:

- medication dosages
- gestational-age thresholds
- diagnostic criteria
- temperature ranges
- laboratory values
- clinical sequencing
- guideline statements

If there appears to be a medical-content error, report it separately instead of silently rewriting it.

The primary task during repository update is faithful transformation of the supplied study material into the interactive quiz format.

---

# 28. Existing Application Behaviour Is the Reference

Before implementing a new day, inspect the most recently completed working day in the repository.

Use it as the UI/behaviour template.

For example:

```text
Day4/
```

should be treated as the initial reference implementation.

Future days must maintain the same:

- navigation
- scoring
- colors
- feedback behaviour
- report structure
- naming format
- mobile responsiveness

unless the user explicitly requests a UI or functional change.

---

# 29. Do Not Introduce These Features Unless Requested

Do not add:

- email collection
- automatic email reports
- Google Sheets submission
- authentication
- leaderboard
- central score storage
- start-from-question field
- question jumping
- backend server
- cloud database

The current design intentionally remains a lightweight static quiz application.

---

# 30. Final Objective

The repository should evolve into:

```text
NEET-SS + ICP Paediatrics
    ↓
Day Selection
    ↓
Day Quiz Set Selection
    ↓
Interactive Quiz Set (15–20 questions, §4)
    ↓
Immediate Learning Feedback
    ↓
Final Wrong-Answer Review
    ↓
Word / PDF Revision Report
```

Every new source study-day document should be transformed into this structure, committed, and pushed while preserving all previously completed days.


---

# Mock Tests — Repository Rules

## 31. Separate Mock Section

Add a separate **Mock Tests** area alongside the normal study-day navigation.

Preferred structure:

```text
/
├── index.html
├── Day4/
├── Day5/
├── Day6/
├── Mock/
│   ├── index.html
│   ├── Day1-5/
│   ├── Day1-11/
│   ├── GrandMockTest1/
│   └── GrandMockTest2/
└── ...
```

The main application must clearly separate:

```text
Study Days
Mock Tests
```

The user will provide the mock name together with the source question file.

Examples:

```text
Day1-5
Day1-11
GrandMockTest 1
GrandMockTest 2
```

Use the supplied mock name as the visible label.

Do not invent a different mock name.

---

## 32. Mock List Page

`Mock/index.html` must list mock tests separately from daily study material.

Prefer two groups:

```text
Cumulative Mocks

Day1-5
Day1-11
Day1-20
...

Grand Mocks

GrandMockTest 1
GrandMockTest 2
...
```

Each mock must have its own folder.

Example:

```text
Mock/
├── index.html
├── Day1-5/
│   ├── index.html
│   ├── quiz1.html
│   ├── quiz2.html
│   └── ...
├── Day1-11/
│   └── ...
└── GrandMockTest1/
    └── index.html
```

---

## 33. Regular/Cumulative Mock Behaviour

Mocks such as:

```text
Day1-5
Day1-11
Day1-20
RevisionMock1
```

should use the existing **quiz-set learning model** with set sizes per §4.

Example for 75 questions:

```text
Quiz Set 1 → Q1–15
Quiz Set 2 → Q16–30
Quiz Set 3 → Q31–45
Quiz Set 4 → Q46–60
Quiz Set 5 → Q61–75
```

Regular mocks must retain:

- one question at a time
- +4 correct
- -1 wrong
- 0 unattempted
- immediate answer validation
- correct option shown in green
- wrong selected option shown in red
- explanation immediately after submission
- exam pearl when available
- sequential question flow
- Finish Quiz option
- final score
- wrong-answer review
- Word wrong-answer report
- Print / Save PDF

Do not add:

- email
- login
- backend
- question jumping
- start-from-question controls

Regular mock report filename example:

```text
Mock_Day1-5_QuizSet2_Q16-30_20261003_091522_Wrong_Answers.doc
```

---

## 34. Grand Mock Detection

Treat the source as a Grand Mock when the supplied mock name clearly identifies it as one.

Examples:

```text
GrandMockTest 1
GrandMockTest 2
Grand Mock Test 3
```

Grand Mocks must use **exam simulation mode**, not the normal quiz-set learning-mode behavior.

Before implementing any Grand Mock, verify the latest available official NBEMS NEET-SS examination pattern.

Priority sources:

```text
1. Latest official NBEMS NEET-SS Information Bulletin
2. Latest official NBEMS NEET-SS notice
3. Official NBEMS examination page
```

Do not assume the pattern is unchanged from previous years.

At the time these rules were written, the latest officially verified pattern available was:

```text
Total questions: 150
Total duration: 150 minutes

Section A: 50 questions / 50 minutes
Section B: 50 questions / 50 minutes
Section C: 50 questions / 50 minutes

Correct: +4
Incorrect: -1
Unattempted: 0
```

This is a reference only.

If NBEMS changes the pattern later, use the latest official pattern.

Record the verified pattern and source year in the repository update summary.

---

## 35. Grand Mock Instructions Screen

Before the exam starts, show an exam instructions page.

Display at least:

```text
Grand Mock name
Total number of questions
Total duration
Number of sections
Questions per section
Time per section
Correct = +4
Incorrect = -1
Unattempted = 0
Section locking rule
Answer-editing rule
Final validation rule
```

The timer must NOT start until the candidate clicks:

```text
Start Grand Mock
```

---

## 36. Grand Mock Section Timer

Grand Mock sections must be strictly time-bound.

For the currently verified reference pattern:

```text
Section A
50 Questions
50 Minutes

Section B
50 Questions
50 Minutes

Section C
50 Questions
50 Minutes
```

Display the current section and remaining time prominently.

Example:

```text
GrandMockTest 1
Section A
Question 18 / 50
Time Remaining: 32:14
```

The section timer must count down continuously.

Do not provide a pause button.

---

## 37. Timer Persistence

Do not implement the timer as a simple in-memory decrementing counter.

Persist an absolute section deadline.

Concept:

```text
sectionEndTime = sectionStartTime + sectionDuration
```

On reload:

```text
remainingTime = sectionEndTime - currentTime
```

Store exam state using `localStorage` or an equivalent lightweight browser mechanism.

Persist at minimum:

```text
Grand Mock name
active section
section end timestamp
answers
review flags
locked sections
final-submission state
```

Refreshing the browser must not reset the timer or give extra time.

If the stored deadline has already passed:

- immediately lock the section
- proceed according to exam rules

---

## 38. Answer Editing During Active Section

While a section is active, the candidate must be able to:

- select an answer
- change an answer
- clear an answer
- navigate forward within the active section
- navigate backward within the active section
- revisit any question within the active section
- optionally mark a question for review

The candidate's final selection at section lock is the recorded answer.

Example:

```text
Q12:
First choice = B
Changed later = D
Section locks

Recorded response = D
```

Do not score intermediate selections.

---

## 39. Clear Response

Grand Mock questions must provide:

```text
Clear Response
```

While the section is active, this changes the question to:

```text
Unattempted
```

The candidate may select another answer afterward.

Clear Response must be disabled once the section is locked.

---

## 40. Grand Mock Navigation Palette

Provide a question palette for the currently active section.

Recommended statuses:

```text
Not Visited
Not Answered
Answered
Marked for Review
Answered & Marked for Review
```

The candidate may click question numbers only inside the current active section.

Do not allow access to:

- future sections
- previously locked sections

---

## 41. No Immediate Correctness Feedback in Grand Mock

Grand Mock is exam mode.

During the exam, DO NOT show:

- correct/incorrect status
- green correctness highlight
- red wrong-answer highlight
- correct answer
- explanation
- exam pearl
- running correct count
- running wrong count
- running marks obtained

The candidate should only see response status.

Complete answer validation happens only after final exam submission.

---

## 42. Section Submission and Locking

A section must lock when either:

```text
1. section time reaches 00:00
```

or, if practice-mode early submission is implemented:

```text
2. candidate explicitly submits the section
```

Before voluntary section submission, show a confirmation such as:

```text
Submit Section A?

You still have 18 minutes remaining.

Once submitted, answers in this section cannot be changed.

[Cancel] [Submit Section]
```

After lock:

- answers cannot be edited
- responses cannot be cleared
- the section cannot be reopened
- navigation back into that section is blocked
- its final answers remain stored

This is mandatory.

---

## 43. Section Transition

Follow the latest verified official NBEMS section-transition rules.

Under the currently verified reference pattern:

- each section is time-bound
- candidates cannot review or modify a section after its allotted time ends
- the next section starts after the previous section completes
- previous sections remain locked

Do not allow unrestricted movement across sections.

If official rules change, update this behavior accordingly.

---

## 44. Grand Mock Final Submission

After the final section is completed:

- lock the entire exam
- calculate the final result
- validate all answers
- show answer correctness
- show explanations
- allow post-exam review

No answers may be modified after final submission.

The final exam can complete by:

```text
final section timeout
```

or:

```text
explicit final section submission
```

---

## 45. Grand Mock Final Result

Display:

```text
Grand Mock name
Total questions
Attempted
Unattempted
Correct
Wrong
Score
Maximum score
Percentage
Total elapsed exam time
Section-wise performance
```

With a 150-question +4/-1 scheme:

```text
Maximum = 600
Score = correct × 4 - wrong
```

Unattempted questions score zero.

If the official marking scheme changes, use the verified current scheme instead.

---

## 46. Section-wise Performance

Show a separate result for each exam section.

Example:

```text
Section A
Correct: 34
Wrong: 10
Unattempted: 6
Score: 126 / 200

Section B
Correct: 37
Wrong: 8
Unattempted: 5
Score: 140 / 200

Section C
Correct: 32
Wrong: 12
Unattempted: 6
Score: 116 / 200

Overall
382 / 600
```

Use actual section counts and marks from the verified official pattern.

---

## 47. Grand Mock Final Review

Only after full exam completion should answer explanations become visible.

For every question show:

```text
Question
Candidate response
Correct response
Status: Correct / Wrong / Unattempted
Explanation
Exam pearl
```

Provide review filters:

```text
All
Wrong
Correct
Unattempted
Marked for Review
```

At minimum, the `Wrong` filter is mandatory.

---

## 48. Grand Mock Wrong-Answer Report

Provide:

```text
Download Wrong Answers
Print / Save PDF
```

Report must include:

```text
Grand Mock name
Overall score
Section-wise scores
Wrong questions
Candidate answer
Correct answer
Explanation
Exam pearl
```

Optionally include unattempted questions in a separate section.

Filename example:

```text
GrandMockTest1_20261003_114233_Wrong_Answers.doc
```

Preserve the supplied Grand Mock name in a filesystem-safe form.

---

## 49. Grand Mock UI

Grand Mock pages should look like an exam interface rather than a daily-study card.

Recommended layout:

```text
------------------------------------------------
GrandMockTest 1
Section A                       Time: 42:17
------------------------------------------------

Question 18 of 50

Question text...

A. ...
B. ...
C. ...
D. ...

[Clear Response]
[Mark for Review & Next]
[Save & Next]

Question Palette
01 02 03 04 05 ...
------------------------------------------------
```

Timer must remain visible.

During the exam, status colors should represent navigation state, not correctness.

Correctness colors are allowed only after final submission.

---

## 50. Grand Mock Question Source Integrity

Use the supplied Grand Mock source file as the source of truth.

Extract:

- questions
- four options
- answer key
- detailed explanations
- exam pearls when present
- question category/difficulty metadata when supplied

Do not reveal answer explanations before exam completion.

Validate:

```text
source MCQ count == generated Grand Mock MCQ count
```

If the current verified official pattern requires 150 questions but the supplied source contains fewer than 150 valid questions:

- do not invent the missing questions
- report the mismatch
- do not label an incomplete test as an exact NEET-SS Grand Mock

---

## 51. Mock Naming

Use the exact supplied mock name as the display name.

Examples:

```text
Day1-5
Day1-11
GrandMockTest 1
```

Safe folder names may remove spaces:

```text
GrandMockTest 1 → GrandMockTest1
Day1-5 → Day1-5
```

Do not replace a supplied name with generic names such as:

```text
Mock 1
Mock 2
```

unless explicitly requested.

---

## 52. Mock Repository Update Workflow

When a mock source file is supplied:

```text
1. Read the mock name provided by the user.
2. Read the source file.
3. Determine Regular Mock vs Grand Mock.
4. Extract MCQs, answer key and explanations.
5. Validate question count and mapping.
6. Create Mock/<MockName>/.
7. Generate the appropriate UI.
8. Update Mock/index.html.
9. Update root navigation if required.
10. Test navigation.
11. Test scoring.
12. If Grand Mock, verify the latest official NBEMS pattern.
13. If Grand Mock, test timers.
14. If Grand Mock, test answer editing before lock.
15. If Grand Mock, test section locking.
16. If Grand Mock, test reload/timer persistence.
17. Test final answer validation.
18. Test wrong-answer reports.
19. Review git diff.
20. Commit.
21. Push.
22. Return a concise update summary.
```

---

## 53. Additional Grand Mock Validation Checklist

Before committing a Grand Mock:

```text
[ ] Exam timer starts only after Start Grand Mock
[ ] Correct official pattern was verified
[ ] Section timer displays correctly
[ ] Active section questions can be revisited
[ ] Answers can be changed before lock
[ ] Clear Response works
[ ] Mark for Review works if implemented
[ ] Future section cannot be opened
[ ] Locked previous section cannot be reopened
[ ] Refresh does not reset time
[ ] Timeout locks section automatically
[ ] No correctness feedback appears during exam
[ ] Section submission permanently locks section
[ ] Final section completion locks the entire exam
[ ] Final scoring is correct
[ ] Section-wise scoring is correct
[ ] Explanations appear only after final submission
[ ] Wrong-answer filter works
[ ] Wrong-answer Word report works
[ ] Print / Save PDF works
```

Do not commit a Grand Mock with known timer, state-persistence, scoring, or section-lock defects.

---

## 54. Updated Application Objective

The application should evolve into:

```text
NEET-SS + ICP Paediatrics
│
├── Study Days
│   ├── Day 4
│   │   └── learning quiz sets (§4 sizes)
│   ├── Day 5
│   │   └── learning quiz sets (§4 sizes)
│   └── ...
│
└── Mock Tests
    │
    ├── Cumulative Mocks
    │   ├── Day1-5
    │   │   └── learning quiz sets (§4 sizes)
    │   ├── Day1-11
    │   │   └── learning quiz sets (§4 sizes)
    │   └── ...
    │
    └── Grand Mocks
        ├── GrandMockTest 1
        │   └── Full NEET-SS exam simulation
        ├── GrandMockTest 2
        │   └── Full NEET-SS exam simulation
        └── ...
```

Daily quizzes and cumulative mocks are **Learning Mode**.

Grand Mock Tests are **Exam Simulation Mode**.

Do not mix their answer-feedback behavior.


---

## 55. Grand Mock — Previous Question and Answer Change

Grand Mock Tests must explicitly support going back to earlier questions within the currently active section.

While the section timer is still running and the section has not been submitted, the candidate must be able to:

```text
Previous Question
Next Question
Click any question number in the active-section palette
```

The candidate may revisit any question in the current section and change the selected answer.

Example:

```text
Q8 → selected B

Candidate moves to Q9, Q10, Q11

Candidate returns to Q8

Candidate changes B → D

Section is still active

Final recorded answer for Q8 = D
```

There is no penalty for changing an answer before section lock.

Only the **last selected option at the moment the section locks** is used for scoring.

---

## 56. Grand Mock — Explicit Navigation Controls

Each question in Grand Mock exam mode should provide clear navigation controls such as:

```text
[Previous]
[Clear Response]
[Mark for Review & Next]
[Save & Next]
```

Rules:

- `Previous` moves to the preceding question in the current active section.
- `Save & Next` stores the current selection and moves forward.
- Selecting an option should also be auto-saved immediately so navigation does not lose the response.
- Returning to a previously answered question must display the candidate's current saved selection.
- The candidate can replace that selection with another option.
- `Clear Response` removes the saved selection and makes the question unattempted.
- The question palette may also be used to revisit any question in the current section.

Do not force the candidate to answer questions sequentially in Grand Mock mode.

---

## 57. Grand Mock — Editing Window

Answer editing remains available until the first of these events occurs:

```text
1. Section timer reaches 00:00
2. Candidate confirms Submit Section
```

Before either event:

```text
Previous questions = editable
Current question = editable
Unanswered questions = accessible
Marked questions = editable
Answered questions = editable
```

After section lock:

```text
Previous questions in that section = read-only / inaccessible during exam
Selections = permanently locked
Clear Response = disabled
Question palette for locked section = disabled
```

A locked section must never become editable again during the same Grand Mock attempt.

---

## 58. Grand Mock — Important Navigation Distinction

There are two different meanings of "go back":

### Allowed

Going back to an earlier question **inside the currently active section**.

Example:

```text
Section B is active.

Q73 → Q72 → change answer → Q80
```

This must be supported.

### Not Allowed After Lock

Going back to a question in an already completed/locked section.

Example:

```text
Section A time has ended.
Section B is active.

Candidate tries to return to Q20 in Section A.
```

This must be blocked if the verified official NEET-SS pattern uses time-bound locked sections.

Always follow the latest verified official NBEMS rules if section navigation policy changes in the future.

---

## 59. Grand Mock — Validation Test for Answer Changes

Before committing any Grand Mock, test this sequence:

```text
1. Open Q1.
2. Select A.
3. Click Save & Next.
4. Navigate forward several questions.
5. Click Previous or palette Q1.
6. Verify A is still selected.
7. Change Q1 to C.
8. Navigate away.
9. Return to Q1.
10. Verify C is selected.
11. Allow section to lock.
12. Confirm C is the final stored response.
13. Confirm Q1 can no longer be edited.
```

This test must pass before the Grand Mock is considered complete.


---

# 60. Canonical Repository Folder Structure — FINAL

Use the following structure as the canonical repository layout from now on.

The original source documents must be preserved inside a dedicated `source/` folder for each Day or Mock.

Generated quiz files must remain outside `source/`.

```text
/
├── index.html
├── README.md
│
├── Day4/
│   ├── source/
│   │   └── Day_4_Prematurity_ELBW_VLBW_Thermoregulation_Apnea.docx
│   ├── index.html
│   ├── quiz1.html
│   ├── quiz2.html
│   ├── quiz3.html
│   ├── quiz4.html
│   └── quiz5.html
│
├── Day5/
│   ├── source/
│   │   └── Day_5_<Topic>.docx
│   ├── index.html
│   ├── quiz1.html
│   ├── quiz2.html
│   └── ...
│
├── Day6/
│   ├── source/
│   │   └── Day_6_<Topic>.docx
│   └── ...
│
└── Mock/
    ├── index.html
    │
    ├── Day1-5/
    │   ├── source/
    │   │   └── Day1-5.docx
    │   ├── index.html
    │   ├── quiz1.html
    │   ├── quiz2.html
    │   ├── quiz3.html
    │   ├── quiz4.html
    │   └── quiz5.html
    │
    ├── Day1-11/
    │   ├── source/
    │   │   └── Day1-11.docx
    │   ├── index.html
    │   ├── quiz1.html
    │   ├── quiz2.html
    │   └── ...
    │
    ├── GrandMockTest1/
    │   ├── source/
    │   │   └── GrandMockTest1.docx
    │   ├── index.html
    │   ├── exam.html
    │   ├── questions.json
    │   └── README.md
    │
    ├── GrandMockTest2/
    │   ├── source/
    │   │   └── GrandMockTest2.docx
    │   ├── index.html
    │   ├── exam.html
    │   ├── questions.json
    │   └── README.md
    │
    └── ...
```

This structure overrides any earlier examples in this document that placed source files beside generated quiz files.

---

# 61. Source Folder Rules

Every Day and Mock folder must contain:

```text
source/
```

The purpose of this folder is to preserve the exact original material supplied by the user.

Examples:

```text
Day7/source/Day_7_Neonatal_Shock.docx

Mock/Day1-20/source/Day1-20.docx

Mock/GrandMockTest3/source/GrandMockTest3.docx
```

Do not modify the original source document unless explicitly asked.

Do not overwrite an existing source document silently.

If a revised version of the same source is supplied, preserve a clearly identifiable filename when practical.

Example:

```text
source/
├── Day_8_v1.docx
└── Day_8_v2.docx
```

or replace the source only when the user clearly intends the new file to supersede the old one.

---

# 62. Generated Files vs Source Files

Keep these responsibilities separate.

## Source material

```text
source/
```

contains only user-supplied study/test material such as:

- DOCX
- PDF
- Markdown
- other original question documents

## Generated application files

The parent Day/Mock folder contains:

- `index.html`
- `quiz*.html`
- `exam.html`
- `questions.json`
- test metadata
- README files

Example:

```text
Mock/GrandMockTest1/
├── source/
│   └── GrandMockTest1.docx
├── index.html
├── exam.html
├── questions.json
└── README.md
```

Never place generated HTML files inside `source/`.

---

# 63. Daily Update Workflow With Source Preservation

When a new Day source file is supplied:

```text
1. Determine the Day number from the supplied file/content.
2. Create DayN/ if it does not exist.
3. Create DayN/source/.
4. Copy/save the supplied original file into DayN/source/.
5. Read the source file from that location.
6. Extract MCQs, answer keys and explanations.
7. Validate the extracted question count.
8. Generate DayN/index.html.
9. Generate quiz-set HTML files (set sizes per §4).
10. Update the root Day list.
11. Test navigation and scoring.
12. Review git diff.
13. Commit the source file AND generated files.
14. Push.
```

The original source document should normally be committed together with the generated quiz update so the repository contains an auditable source-to-quiz history.

---

# 64. Regular Mock Update Workflow With Source Preservation

For a cumulative/regular mock such as:

```text
Day1-5
Day1-11
Day1-20
```

use:

```text
Mock/<MockName>/
├── source/
├── index.html
├── quiz1.html
├── quiz2.html
└── ...
```

Workflow:

```text
1. Read the exact mock name supplied by the user.
2. Create Mock/<MockName>/.
3. Create Mock/<MockName>/source/.
4. Preserve the supplied source file inside source/.
5. Extract questions/answers/explanations.
6. Split into quiz sets per §4.
7. Generate the mock index page.
8. Generate quiz-set pages.
9. Update Mock/index.html.
10. Validate.
11. Commit.
12. Push.
```

---

# 65. Grand Mock Update Workflow With Source Preservation

For:

```text
GrandMockTest N
```

use:

```text
Mock/GrandMockTestN/
├── source/
│   └── <supplied Grand Mock source>
├── index.html
├── exam.html
├── questions.json
└── README.md
```

`source/` preserves the user-supplied test document.

`questions.json` is the normalized machine-readable representation used by the exam UI.

The transformation is:

```text
source document
      ↓
questions.json
      ↓
exam.html
```

Before writing `questions.json`, validate:

```text
source MCQ count
answer-key count
explanation count
question-to-answer mapping
```

Do not regenerate `questions.json` from memory or from a previous Grand Mock.

Always rebuild it from the current Grand Mock source file.

---

# 66. Grand Mock Metadata README

Each Grand Mock folder should contain:

```text
README.md
```

Record at minimum:

```text
Grand Mock name
Source filename
Source question count
Generated question count
NEET-SS official pattern used
Official pattern year
Total exam duration
Section count
Questions per section
Time per section
Marking scheme
Generation/update date
```

Example:

```text
# GrandMockTest 1

Source:
source/GrandMockTest1.docx

Questions:
150

Exam pattern:
NEET-SS 2025 official pattern

Sections:
3 × 50 questions

Section duration:
50 minutes

Total duration:
150 minutes

Marking:
+4 / -1 / 0
```

This makes future maintenance easier when the official examination pattern changes.

---

# 67. Git Handling of Source Documents

When updating the repository:

```bash
git status
```

Confirm the expected source file appears as a new or modified file.

Stage both source and generated content.

Example:

```bash
git add Day8/source/
git add Day8/index.html
git add Day8/quiz*.html
git add index.html
```

For mocks:

```bash
git add Mock/Day1-11/
git add Mock/index.html
```

For Grand Mock:

```bash
git add Mock/GrandMockTest2/
git add Mock/index.html
```

Do not stage unrelated user documents.

---

# 68. Never Delete the Source After Generation

After the quiz is generated successfully:

DO NOT delete:

```text
source/
```

The source file is part of the repository record.

It is useful for:

- checking question fidelity
- fixing answer-key errors
- regenerating a quiz later
- auditing explanations
- comparing revised study material
- rebuilding the UI with a new template

The generated HTML/JSON should always be traceable back to the preserved source file.

---

# 69. Final Navigation and Folder Model

The final application architecture is:

```text
ROOT
│
├── index.html
│
├── Day4/
│   ├── source/
│   ├── index.html
│   └── quiz*.html
│
├── Day5/
│   ├── source/
│   ├── index.html
│   └── quiz*.html
│
└── Mock/
    ├── index.html
    │
    ├── Day1-5/
    │   ├── source/
    │   ├── index.html
    │   └── quiz*.html
    │
    ├── Day1-11/
    │   ├── source/
    │   ├── index.html
    │   └── quiz*.html
    │
    └── GrandMockTest1/
        ├── source/
        ├── index.html
        ├── exam.html
        ├── questions.json
        └── README.md
```

Navigation remains:

```text
Home
│
├── Study Days
│   └── Day
│       └── Quiz Set
│           └── Learning Quiz
│
└── Mock Tests
    │
    ├── Cumulative Mock
    │   └── Quiz Set
    │       └── Learning Quiz
    │
    └── Grand Mock
        └── Full Timed Exam Simulation
```

This folder structure is the final preferred structure for future repository updates.

---

# 70. Daily Study Portal (from Day 5 onward)

Each study day is a **study portal**, not only a quiz list. `DayN/index.html` is the portal; the quiz sets (sizes per §4) remain inside it.

Build every day with the shared tooling — never hand-write portal HTML:

```bash
python tools/build_day.py N "path/to/Day_N_source.docx"
```

The script:

1. copies the docx into `DayN/source/`
2. converts the whole document (headings, tables, callout boxes, WHAT/WHY/HOW grids, lists, bold/italic) into `DayN/content.js`
3. builds `DayN/quiz1..K.html` from `tools/templates/quiz.html` (Sections A–C)
4. stops with an error list if MCQ count, answer key, explanation answer, option text or level disagree
5. stops if any document block is not placed in the portal (block-integrity check)

Standard portal pages (same for every day, driven by the document's Heading 1 titles):

```text
Overview (objectives, study plan with tick boxes, progress)
Study Notes (one page per PART)
Must-Know Numbers · Tables & Algorithms
Clinical Cases (reasoning hidden until revealed) · Data Interpretation (answers hidden)
Pearls & Traps · Quizzes
Rapid Revision · Active Recall (self-rated cards) · Revision Plan
References
```

The UI lives only in `assets/portal.css` and `assets/portal.js`. Change the look there so every day stays identical.

Cache busting: the build appends `?v=<content hash>` to the shared assets (and `content.js`) so phones fetch the new copy after an update. After changing anything in `assets/`, rebuild every day (`tools/build_day.py`) so all pages get the new version tag; pages not built by the script (Day 1–5 mock, grand mock) must have their `notebook.js?v=` tag refreshed as well.

Recognised extra headings: "Rapid Revision" (same as "Last 15-minute revision") → Rapid Revision page; "Cross-Day Connections" → Quick Reference page. Clinical cases may be one paragraph with line breaks — everything from the first "Structured reasoning / Reasoning / Answer / Trap identified / Management / Next step" line onward is hidden until revealed.

Answer options are always shuffled once at build time (fixed seed per day, so rebuilds are identical): correct answers are spread evenly over A–D, never more than 3 identical letters in a row, never a repeating A-B-C-D cycle. "Why not the others" letters are relabelled to the shuffled positions and the build re-verifies every answer against an unshuffled parse of the docx. `srcAnswer` in the quiz data records the document's original letter. Exception: when the source document already carries a deliberately randomised key (e.g. a "…_RandomKey.docx", balanced and with no run >3 or cycle), build with `python tools/build_day.py N <docx> --keep-order` so the site's letters match the document. If a new doc lacks content the current day has (e.g. Active Recall answers) and the user asked only for a quiz update, keep the existing page and report it.

Content rules still apply: show the document text faithfully; do not rewrite medical content. Generic boilerplate "why not" lines are dropped from quiz explanations; pearls labelled "Qn pearl" are matched to question n even if printed under another question. Report such source issues in the update summary.

Error notebook (`assets/notebook.js`, shared by every quiz page, mock and grand mock): wrong answers are recorded automatically when a test finishes (repeat mistakes counted, retest date +48–72 h, later correct answers mark the entry fixed). The result screen shows a K/C/R/G/S tagging panel; "Save error notes & send" posts a second ntfy message:

Every error-note entry uses exactly this format, one mistake per line:

```text
Day → Question → Chosen answer → Correct answer → Error type → optional note
```

Learning-mode quizzes put the error notes inside the single result notification:

```text
Day 6 Quiz 2 — Q16–Q30
Score: 45 / 60 (75%)
Attempted 15/15 · Correct 12 · Wrong 3 · Skipped 0
Time: 11m 40s

Wrong (3): Day → Question → Chosen → Correct → Type → Note
Day 6 → Q16 → C → B → R → DAT is etiology, not a threshold
Day 6 → Q22 → C → B → K
Day 6 → Q29 → B → A → S (2×)
Total: K1 R1 S1 · Retest: 6–7 Oct 2026
```

Untagged entries show `?` as the type (grand mock before tagging); repeated mistakes add `(2×)` after the type.

Each portal has an Error Notebook page; `notebook.html` combines all days and mocks. New pages must include `assets/notebook.js` and pass a `NB_CTX` ({srcId, label, set, href}).

If a new document uses a Heading 1 the build does not recognise, it becomes a Study Notes page and is listed under `warnings` — review it before committing.
