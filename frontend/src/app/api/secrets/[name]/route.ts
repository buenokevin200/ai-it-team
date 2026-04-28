import { NextRequest, NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_SERVICE_URL || "http://localhost:8000";

export async function DELETE(
  _request: NextRequest,
  { params }: { params: { name: string } }
) {
  try {
    const res = await fetch(
      `${AGENT_URL}/api/secrets/${encodeURIComponent(params.name)}`,
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
