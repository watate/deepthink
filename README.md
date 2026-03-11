# DeepThink

DeepThink is a tool that helps you think deeply about written text. This can be an essay, a blog post, a paper, or anything. It uses a tree structure to help you structure your thinking, and automatically generates questions for you to think about.

How it works:
1. You paste a piece of writing (markdown format)
2. DeepThink turns the writing into blocks
3. DeepThink automatically generates "n" questions per block. By default n=2, and this is configurable. These new questions form sub-blocks
4. You write answers to the questions. These answers form sub-blocks
5. DeepThink evaluates your answer and gives it a score + feedback on the answer
6. You can click a button to generate more sub-questions to the answer you wrote

Additional details:
- You can always add more questions to each block. Meaning: if n=2, 2 questions will be generated automatically, but you can click a button to generate a 3rd question
- All answers and questions are in markdown format
- All answers are stored in JSON. JSON is always saved automatically to S3 after generating questions or submitting answers
- There is a dashboard to see a list of writings. The dashboard has a search feature
- There is an export feature that exports the data as a Markdown file. This is exported to a local directory, since DeepThink is only for local use (no deployment plans currently)

Objects:
- BlockTree
- TitleBlock
- QuestionBlock
- AnswerBlock

# Run
```
uv run fastapi dev apps/backend/main.py
```