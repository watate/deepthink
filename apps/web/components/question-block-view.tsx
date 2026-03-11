"use client";

import { useState } from "react";
import {
  CheckCircle,
  MessageSquare,
  Plus,
  Star,
  Loader2,
} from "lucide-react";
import { Button } from "@workspace/ui/components/button";
import { Badge } from "@workspace/ui/components/badge";
import { Separator } from "@workspace/ui/components/separator";
import type { QuestionBlock, BlockTree } from "@/lib/api";
import {
  submitAnswer,
  evaluateAnswer,
  generateQuestions,
} from "@/lib/api";
import { AnswerForm } from "./answer-form";

interface QuestionBlockViewProps {
  question: QuestionBlock;
  treeId: string;
  onTreeUpdate: (tree: BlockTree) => void;
  depth?: number;
}

export function QuestionBlockView({
  question,
  treeId,
  onTreeUpdate,
  depth = 0,
}: QuestionBlockViewProps) {
  const [evaluating, setEvaluating] = useState(false);
  const [generating, setGenerating] = useState(false);

  async function handleSubmitAnswer(content: string) {
    const updated = await submitAnswer(treeId, question.id, content);
    onTreeUpdate(updated);
  }

  async function handleEvaluate() {
    if (!question.answer) return;
    setEvaluating(true);
    try {
      const updated = await evaluateAnswer(treeId, question.answer.id);
      onTreeUpdate(updated);
    } finally {
      setEvaluating(false);
    }
  }

  async function handleGenerateMore() {
    if (!question.answer) return;
    setGenerating(true);
    try {
      const updated = await generateQuestions(treeId, question.answer.id, 1);
      onTreeUpdate(updated);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div
      className={`border-l-2 pl-4 ${depth > 0 ? "border-muted ml-2" : "border-primary/30"}`}
    >
      <div className="flex items-start gap-2 py-2">
        <MessageSquare className="text-primary mt-0.5 h-4 w-4 shrink-0" />
        <p className="text-sm font-medium">{question.content}</p>
      </div>

      {question.answer ? (
        <div className="ml-6">
          <div className="bg-muted/50 rounded-md p-3">
            <p className="text-sm whitespace-pre-wrap">
              {question.answer.content}
            </p>

            {question.answer.score !== null && (
              <div className="mt-2 flex items-center gap-2">
                <Badge
                  variant={
                    question.answer.score >= 70 ? "default" : "secondary"
                  }
                  className="text-xs"
                >
                  <Star className="mr-1 h-3 w-3" />
                  {question.answer.score}/100
                </Badge>
              </div>
            )}

            {question.answer.feedback && (
              <p className="text-muted-foreground mt-2 text-xs italic">
                {question.answer.feedback}
              </p>
            )}
          </div>

          <div className="mt-2 flex gap-2">
            {question.answer.score === null && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleEvaluate}
                disabled={evaluating}
              >
                {evaluating ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : (
                  <CheckCircle className="mr-1 h-3 w-3" />
                )}
                Evaluate
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerateMore}
              disabled={generating}
            >
              {generating ? (
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              ) : (
                <Plus className="mr-1 h-3 w-3" />
              )}
              More Questions
            </Button>
          </div>

          {question.answer.children_questions.length > 0 && (
            <div className="mt-3">
              <Separator className="mb-3" />
              {question.answer.children_questions.map((childQ) => (
                <QuestionBlockView
                  key={childQ.id}
                  question={childQ}
                  treeId={treeId}
                  onTreeUpdate={onTreeUpdate}
                  depth={depth + 1}
                />
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="ml-6">
          <AnswerForm onSubmit={handleSubmitAnswer} />
        </div>
      )}
    </div>
  );
}
