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

# 4. Number of Questions Per Quiz

The preferred quiz size is:

```text
15 questions per quiz set
```

Example for 75 questions:

```text
Quiz Set 1 → Q1–15
Quiz Set 2 → Q16–30
Quiz Set 3 → Q31–45
Quiz Set 4 → Q46–60
Quiz Set 5 → Q61–75
```

If the total is not divisible by 15:

- keep sets of 15 where possible
- place the remaining questions in the final set

Example:

```text
67 questions

Set 1 → Q1–15
Set 2 → Q16–30
Set 3 → Q31–45
Set 4 → Q46–60
Set 5 → Q61–67
```

Never drop questions just to make all sets equal.

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

The learner should proceed sequentially within each 15-question quiz set.

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
8. Split questions into sets of maximum 15
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
15-question Interactive Quiz
    ↓
Immediate Learning Feedback
    ↓
Final Wrong-Answer Review
    ↓
Word / PDF Revision Report
```

Every new source study-day document should be transformed into this structure, committed, and pushed while preserving all previously completed days.
