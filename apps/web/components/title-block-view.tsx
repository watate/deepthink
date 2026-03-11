"use client";

import { useState } from "react";
import { ChevronRight, Loader2, Plus } from "lucide-react";
import { Button } from "@workspace/ui/components/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@workspace/ui/components/collapsible";
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
  const [open, setOpen] = useState(true);

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
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer select-none">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <ChevronRight
                className={`h-4 w-4 shrink-0 transition-transform ${open ? "rotate-90" : ""}`}
              />
              Block {index + 1}
              <span className="text-muted-foreground font-normal">
                ({block.questions.length} question{block.questions.length !== 1 ? "s" : ""})
              </span>
            </CardTitle>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
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
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
