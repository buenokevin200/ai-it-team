import { NextRequest, NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_SERVICE_URL || "http://localhost:8000";

export async function GET(
  _request: NextRequest,
  { params }: { params: { session_id: string } }
) {
  try {
    const res = await fetch(
      `${AGENT_URL}/api/deployments/${encodeURIComponent(params.session_id)}`
    );
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { session_id: params.session_id, status: "unknown", logs: [] },
      { status: 200 }
    );
  }
}
