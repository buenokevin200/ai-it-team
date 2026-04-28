import { NextRequest, NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_SERVICE_URL || "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${AGENT_URL}/api/secrets`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ secrets: [] });
  }
}

export async function POST(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const name = url.searchParams.get("name") || "";
    const category = url.searchParams.get("category") || "";
    const value = url.searchParams.get("value") || "";

    const res = await fetch(
      `${AGENT_URL}/api/secrets?name=${encodeURIComponent(name)}&category=${encodeURIComponent(category)}&value=${encodeURIComponent(value)}`,
      { method: "POST" }
    );
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed to store secret" },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const name = url.pathname.split("/").pop() || "";

    const res = await fetch(
      `${AGENT_URL}/api/secrets/${encodeURIComponent(name)}`,
      { method: "DELETE" }
    );
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed to delete secret" },
      { status: 500 }
    );
  }
}
