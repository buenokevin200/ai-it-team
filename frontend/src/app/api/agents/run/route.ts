import { NextRequest, NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_SERVICE_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const command = body.command;

    if (!command) {
      return NextResponse.json(
        { error: "command is required" },
        { status: 400 }
      );
    }

    const res = await fetch(`${AGENT_URL}/api/agents/run?command=${encodeURIComponent(command)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(300000),
    });

    const contentType = res.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      const data = await res.json();
      return NextResponse.json(data);
    }

    const text = await res.text();
    return NextResponse.json(
      {
        error: `Backend returned status ${res.status}`,
        details: text.substring(0, 1000),
      },
      { status: 502 }
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : "Agent service unavailable";
    return NextResponse.json(
      { error: message },
      { status: 500 }
    );
  }
}
