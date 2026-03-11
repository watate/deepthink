"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@workspace/ui/components/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@workspace/ui/components/card";
import { Input } from "@workspace/ui/components/input";
import { Textarea } from "@workspace/ui/components/textarea";
import { createTree } from "@/lib/api";

export default function NewTreePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [numQuestions, setNumQuestions] = useState(2);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !text.trim()) return;

    setLoading(true);
    setError("");
    try {
      const tree = await createTree(title, text, numQuestions);
      router.push(`/trees/${tree.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create tree");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <Link href="/" className="text-muted-foreground mb-6 inline-flex items-center gap-1 text-sm hover:underline">
        <ArrowLeft className="h-4 w-4" />
        Back to dashboard
      </Link>

      <Card>
        <CardHeader>
          <CardTitle>New Writing</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="mb-1 block text-sm font-medium">Title</label>
              <Input
                placeholder="e.g. My essay on consciousness"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">
                Text (markdown)
              </label>
              <Textarea
                placeholder="Paste your writing here..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={12}
                required
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">
                Questions per block
              </label>
              <Input
                type="number"
                min={1}
                max={10}
                value={numQuestions}
                onChange={(e) => setNumQuestions(Number(e.target.value))}
                className="w-24"
              />
            </div>

            {error && (
              <p className="text-sm text-red-500">{error}</p>
            )}

            <Button type="submit" disabled={loading} className="self-start">
              {loading ? "Creating..." : "Create & Generate Questions"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
