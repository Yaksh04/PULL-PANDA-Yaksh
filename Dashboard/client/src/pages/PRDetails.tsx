// SWE_project_website/client/src/pages/PRDetails.tsx

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useLocation, useRoute } from "wouter"; // ✅ Added useRoute

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress"; // Optional: for score

import {
  ExternalLink,
  ArrowLeft,
  MessageSquare,
  Bot,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";

import { apiFetch } from "@/lib/apiClient";
import { AIReviewResult } from "@/lib/api"; // Ensure this interface exists in api.ts

interface PRComment {
  id: number;
  body: string;
  user: {
    login: string;
    avatar_url: string;
  };
  created_at: string;
}

export default function PRDetails() {
  const [, setLocation] = useLocation();

  // ✅ FIX: Use useRoute to get parameters from /pr-details/:owner/:repo/:number
  const [match, params] = useRoute("/pr-details/:owner/:repo/:number");

  const owner = match ? params?.owner : null;
  const repo = match ? params?.repo : null;
  const number = match ? params?.number : null;

  const [latestAIComment, setLatestAIComment] = useState<PRComment | null>(
    null
  );
  const [humanComments, setHumanComments] = useState<PRComment[]>([]);

  // 1. Fetch GitHub Comments (The conversation)
  const { data: githubData, isLoading: loadingGithub } = useQuery({
    queryKey: ["pr-reviews", owner, repo, number],
    queryFn: () =>
      owner
        ? apiFetch(`/api/pull-requests/${owner}/${repo}/${number}/reviews`)
        : null,
    enabled: !!owner && !!repo && !!number,
  });

  // 2. Fetch Rich AI Stats from DB (The Score & Semgrep Data)
  const { data: aiStats, isLoading: loadingStats } = useQuery<AIReviewResult>({
    queryKey: ["ai-analysis", owner, repo, number],
    queryFn: () =>
      owner ? apiFetch(`/api/ai-analysis/${owner}/${repo}/${number}`) : null,
    enabled: !!owner && !!repo && !!number,
  });

  // Process GitHub comments
  useEffect(() => {
    if (!githubData) return;

    const all = githubData.allComments || [];

    // Find the comment posted by the Bot
    const ai = all
      .filter(
        (c: PRComment) =>
          c.body?.toLowerCase().includes("ai-powered review") ||
          c.user.login.includes("bot") // Adjust based on your bot's name
      )
      .sort(
        (a: PRComment, b: PRComment) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );

    setLatestAIComment(ai[0] || null);

    // Human comments
    const humans = all.filter(
      (c: PRComment) =>
        !c.body?.toLowerCase().includes("ai-powered review") &&
        !c.user.login.includes("bot")
    );

    setHumanComments(humans);
  }, [githubData]);

  if (!match) return <div>Invalid PR Link</div>;

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {/* Back Button */}
      <Button variant="outline" onClick={() => setLocation("/pull-requests")}>
        <ArrowLeft className="h-4 w-4 mr-2" /> Back to List
      </Button>

      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            PR #{number}: {repo}
          </h1>
          <p className="text-muted-foreground">Owner: {owner}</p>
        </div>
        <Button variant="outline" asChild>
          <a
            href={`https://github.com/${owner}/${repo}/pull/${number}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Open in GitHub
          </a>
        </Button>
      </div>

      {/* LOADING */}
      {(loadingGithub || loadingStats) && (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      )}

      {/* DASHBOARD CONTENT */}
      {githubData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* LEFT COL: AI INSIGHTS */}
          <div className="md:col-span-2 space-y-6">
            {/* 1. SCORE CARD (Only if DB data exists) */}
            {aiStats && (
              <Card className="p-6 border-l-4 border-l-primary">
                <h2 className="text-lg font-semibold mb-4">AI Quality Score</h2>
                <div className="flex items-center gap-4">
                  <div className="text-4xl font-bold text-primary">
                    {aiStats.score}/100
                  </div>
                  <Progress value={aiStats.score} className="w-1/2 h-4" />
                </div>
                {aiStats.staticAnalysis && (
                  <div className="mt-4 p-4 bg-muted/50 rounded-md text-sm font-mono whitespace-pre-wrap max-h-60 overflow-y-auto">
                    <strong>Static Analysis Logs:</strong>
                    <br />
                    {aiStats.staticAnalysis}
                  </div>
                )}
              </Card>
            )}

            {/* 2. THE REVIEW TEXT */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold flex items-center gap-2 mb-4">
                <Bot className="h-5 w-5 text-blue-500" />
                AI Review Summary
              </h2>

              {latestAIComment ? (
                <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap">
                  {/* Ideally use ReactMarkdown here, but text works for now */}
                  {latestAIComment.body}
                </div>
              ) : (
                <div className="text-muted-foreground italic">
                  No AI review comment found on GitHub yet.
                </div>
              )}
            </Card>
          </div>

          {/* RIGHT COL: HUMAN CONVERSATION */}
          <div className="space-y-6">
            <Card className="p-5 h-full">
              <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
                <MessageSquare className="h-5 w-5" />
                Discussion
              </h2>
              <div className="space-y-4">
                {humanComments.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No other comments.
                  </p>
                ) : (
                  humanComments.map((c) => (
                    <div
                      key={c.id}
                      className="p-3 bg-secondary/50 rounded-lg text-sm"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <img
                          src={c.user.avatar_url}
                          alt={c.user.login}
                          className="w-5 h-5 rounded-full"
                        />
                        <span className="font-semibold">{c.user.login}</span>
                        <span className="text-xs text-muted-foreground ml-auto">
                          {new Date(c.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p>{c.body}</p>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
