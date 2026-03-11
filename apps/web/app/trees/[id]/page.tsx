"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download, Loader2 } from "lucide-react";
import { Button } from "@workspace/ui/components/button";
import { getTree, exportTree, type BlockTree } from "@/lib/api";
import { TitleBlockView } from "@/components/title-block-view";

export default function TreePage() {
  const { id } = useParams<{ id: string }>();
  const [tree, setTree] = useState<BlockTree | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportPath, setExportPath] = useState("");

  useEffect(() => {
    getTree(id)
      .then(setTree)
      .finally(() => setLoading(false));
  }, [id]);

  async function handleExport() {
    setExporting(true);
    try {
      const result = await exportTree(id);
      setExportPath(result.path);
    } finally {
      setExporting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <Loader2 className="text-muted-foreground h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (!tree) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <p className="text-muted-foreground">Tree not found.</p>
        <Link href="/" className="text-sm underline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <Link
          href="/"
          className="text-muted-foreground inline-flex items-center gap-1 text-sm hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          Dashboard
        </Link>
        <Button
          variant="outline"
          size="sm"
          onClick={handleExport}
          disabled={exporting}
        >
          {exporting ? (
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          ) : (
            <Download className="mr-1 h-3 w-3" />
          )}
          Export
        </Button>
      </div>

      <h1 className="mb-1 text-2xl font-bold">{tree.title}</h1>
      <p className="text-muted-foreground mb-6 text-xs">
        {tree.blocks.length} blocks &middot; {tree.num_questions} questions per
        block
      </p>

      {exportPath && (
        <div className="bg-muted mb-4 rounded-md p-2 text-xs">
          Exported to: <code>{exportPath}</code>
        </div>
      )}

      <div className="flex flex-col gap-6">
        {tree.blocks.map((block, i) => (
          <TitleBlockView
            key={block.id}
            block={block}
            treeId={tree.id}
            index={i}
            onTreeUpdate={setTree}
          />
        ))}
      </div>
    </div>
  );
}
