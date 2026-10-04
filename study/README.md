# Study material

Everything you need to revise after (or alongside) the hands-on lessons.

| File | What it is | Use it when |
|---|---|---|
| [study-guide.pdf](study-guide.pdf) | the 15 concept lessons, the service contract, the troubleshooting method, the capstone, the glossary and the interview questions as one printable PDF (answers expanded, with a table of contents; built by `study/tools/build_pdf.py`) | you want to read offline, print, or annotate |
| [glossary.md](glossary.md) | every term used in the course, A–Z, in one or two plain sentences, with a link to where it is explained | a word in a lesson is unclear |
| [interview-questions.md](interview-questions.md) | 25 questions with model answers, from Dockerfiles to troubleshooting | before an interview, or to test yourself |
| [../tutorial/](../tutorial/README.md) | the guided training course through the repository | you want to be taught, step by step |

## How to revise

1. Work through the [tutorial](../tutorial/README.md); it sends you to the lessons, labs and docs in the right order.
2. After each chapter, look up every glossary term you could not explain to a colleague.
3. At the end, answer the interview questions **out loud**, then compare with the model answers. Explaining is a
   different skill from knowing; it needs practice.
4. Finish with the [capstone](../capstone/README.md) and the [knowledge check](../tutorial/13-knowledge-check.md).

## Rebuild the PDF

```text
pip install markdown
python study/tools/build_pdf.py        (uses a headless Chrome or Edge to print the PDF)
```
