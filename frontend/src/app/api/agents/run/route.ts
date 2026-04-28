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
    });

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Agent service unavailable" },
      { status: 500 }
    );
  }
}
