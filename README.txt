NEET-SS + ICP PAEDIATRICS — STUDY PORTALS AND QUIZZES

Open the root index.html first.

Folder structure:

index.html                 Home: Daily Study Portals
notebook.html              Combined K/C/R/G/S error notebook (all days and mocks)
assets/
  portal.css, portal.js    Shared study-portal UI (every day uses these two files)
  countdown.js             Exam countdown (home banner + chip on portal/quiz pages); exam date/time set at the top of the file
  notebook.js              Automatic error notebook: records wrong answers when any quiz/mock finishes,
                           K/C/R/G/S tagging panel on result screens, "Error notes" ntfy message, notebook pages
tools/
  build_day.py             Builds a day's portal + quiz sets from its source docx
  docx_parse.py            Docx reader (headings, tables, callout boxes, MCQs)
  templates/quiz.html      Shared quiz-set template (set sizes: rules §4)
Day7/, Day8/
  source/<day docx>        Original document (kept for audit/regeneration)
  index.html               Study portal (overview, notes, cases, pearls, revision, quizzes)
  content.js               Portal content generated from the docx — do not edit by hand
  quiz1.html ... quiz5.html
  calc.html                Calculation Drill (numeric answers), when the document has one
  img/                     Pictures from the document + generated unlabelled schematics (tools/gen_xray.py)
  source/extras.json       Optional: generated images for image MCQs/visual stations, reworded drill questions, day title

Adding or updating a day (needs Python 3, no extra packages):

  python tools/build_day.py 7 "path/to/Day_7_....docx"

The script copies the docx into Day7/source/, checks the MCQs (question count, answer key,
explanations, option text) and stops with a list of problems if anything disagrees. It also checks
that every block of the document appears in the portal. Then add a Day 7 card to the root index.html.
