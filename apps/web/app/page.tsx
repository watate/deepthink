"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Search, Trash2, FileText, HelpCircle } from "lucide-react";
import { Button } from "@workspace/ui/components/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@workspace/ui/components/card";
import { Input } from "@workspace/ui/components/input";
import { listTrees, searchTrees, deleteTree, type TreeListItem } from "@/lib/api";

export default function DashboardPage() {
  const [trees, setTrees] = useState<TreeListItem[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const data = query.trim()
        ? await searchTrees(query)
        : await listTrees();
      setTrees(data);
    } catch {
      /* backend may not be running */
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    await load();
  }

  async function handleDelete(id: string) {
    await deleteTree(id);
    setTrees((prev) => prev.filter((t) => t.id !== id));
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold">DeepThink</h1>
        <Link href="/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New
          </Button>
        </Link>
      </div>

      <form onSubmit={handleSearch} className="mb-6 flex gap-2">
        <div className="relative flex-1">
          <Search className="text-muted-foreground absolute top-2.5 left-3 h-4 w-4" />
          <Input
            placeholder="Search writings..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button type="submit" variant="outline">
          Search
        </Button>
      </form>

      {loading ? (
        <p className="text-muted-foreground text-sm">Loading...</p>
      ) : trees.length === 0 ? (
        <div className="text-muted-foreground py-16 text-center text-sm">
          No writings yet. Click &quot;New&quot; to get started.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {trees.map((tree) => (
            <Card key={tree.id}>
              <CardHeader className="flex-row items-center justify-between pb-2">
                <Link href={`/trees/${tree.id}`} className="flex-1">
                  <CardTitle className="text-base hover:underline">
                    {tree.title}
                  </CardTitle>
                </Link>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => handleDelete(tree.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent>
                <CardDescription className="flex items-center gap-4 text-xs">
                  <span className="flex items-center gap-1">
                    <FileText className="h-3 w-3" />
                    {tree.num_blocks} blocks
                  </span>
                  <span className="flex items-center gap-1">
                    <HelpCircle className="h-3 w-3" />
                    {tree.num_questions} questions
                  </span>
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
