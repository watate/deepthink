const API_BASE = "http://localhost:8000/api";

export interface AnswerBlock {
  id: string;
  content: string;
  score: number | null;
  feedback: string | null;
  children_questions: QuestionBlock[];
}

export interface QuestionBlock {
  id: string;
  content: string;
  answer: AnswerBlock | null;
}

export interface TitleBlock {
  id: string;
  content: string;
  questions: QuestionBlock[];
}

export interface BlockTree {
  id: string;
  title: string;
  original_text: string;
  blocks: TitleBlock[];
  num_questions: number;
}

export interface TreeListItem {
  id: string;
  title: string;
  num_blocks: number;
  num_questions: number;
}

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function createTree(
  title: string,
  text: string,
  numQuestions: number = 2
): Promise<BlockTree> {
  return request("/trees", {
    method: "POST",
    body: JSON.stringify({ title, text, num_questions: numQuestions }),
  });
}

export async function listTrees(): Promise<TreeListItem[]> {
  return request("/trees");
}

export async function searchTrees(query: string): Promise<TreeListItem[]> {
  return request(`/trees/search?q=${encodeURIComponent(query)}`);
}

export async function getTree(treeId: string): Promise<BlockTree> {
  return request(`/trees/${treeId}`);
}

export async function deleteTree(treeId: string): Promise<void> {
  await request(`/trees/${treeId}`, { method: "DELETE" });
}

export async function generateQuestions(
  treeId: string,
  blockId: string,
  numQuestions: number = 1
): Promise<BlockTree> {
  return request(`/trees/${treeId}/blocks/${blockId}/questions`, {
    method: "POST",
    body: JSON.stringify({ num_questions: numQuestions }),
  });
}

export async function submitAnswer(
  treeId: string,
  questionId: string,
  content: string
): Promise<BlockTree> {
  return request(`/trees/${treeId}/questions/${questionId}/answer`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function evaluateAnswer(
  treeId: string,
  answerId: string
): Promise<BlockTree> {
  return request(`/trees/${treeId}/answers/${answerId}/evaluate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function exportTree(
  treeId: string
): Promise<{ ok: boolean; path: string }> {
  return request(`/trees/${treeId}/export`, { method: "POST" });
}
