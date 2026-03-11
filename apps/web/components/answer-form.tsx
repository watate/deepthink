"use client";

import { useState } from "react";
import { Send } from "lucide-react";
import { Button } from "@workspace/ui/components/button";
import { Textarea } from "@workspace/ui/components/textarea";

interface AnswerFormProps {
  onSubmit: (content: string) => Promise<void>;
}

export function AnswerForm({ onSubmit }: AnswerFormProps) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    setLoading(true);
    try {
      await onSubmit(content);
      setContent("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-2 flex flex-col gap-2">
      <Textarea
        placeholder="Write your answer..."
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={3}
        className="text-sm"
      />
      <Button
        type="submit"
        size="sm"
        disabled={loading || !content.trim()}
        className="self-start"
      >
        <Send className="mr-1 h-3 w-3" />
        {loading ? "Submitting..." : "Submit Answer"}
      </Button>
    </form>
  );
}
