"use client";

import { useState } from "react";
import { Loader2, Plus } from "lucide-react";
import { Button } from "@workspace/ui/components/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@workspace/ui/components/card";
import type { TitleBlock, BlockTree } from "@/lib/api";
import { generateQuestions } from "@/lib/api";
import { QuestionBlockView } from "./question-block-view";

interface TitleBlockViewProps {
  block: TitleBlock;
  treeId: string;
  index: number;
  onTreeUpdate: (tree: BlockTree) => void;
}

export function TitleBlockView({
  block,
  treeId,
  index,
  onTreeUpdate,
}: TitleBlockViewProps) {
  const [generating, setGenerating] = useState(false);

  async function handleGenerateMore() {
    setGenerating(true);
    try {
      const updated = await generateQuestions(treeId, block.id, 1);
      onTreeUpdate(updated);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Block {index + 1}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground mb-4 text-sm whitespace-pre-wrap">
          {block.content}
        </p>

        <div className="flex flex-col gap-3">
          {block.questions.map((q) => (
            <QuestionBlockView
              key={q.id}
              question={q}
              treeId={treeId}
              onTreeUpdate={onTreeUpdate}
            />
          ))}
        </div>

        <Button
          variant="ghost"
          size="sm"
          className="mt-3"
          onClick={handleGenerateMore}
          disabled={generating}
        >
          {generating ? (
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          ) : (
            <Plus className="mr-1 h-3 w-3" />
          )}
          Add Question
        </Button>
      </CardContent>
    </Card>
  );
}
