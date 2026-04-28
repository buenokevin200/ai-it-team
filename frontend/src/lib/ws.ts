import { io, Socket } from "socket.io-client";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "http://localhost:8000";

let socket: Socket | null = null;

export function getWebSocket(): Socket {
  if (!socket) {
    socket = io(WS_URL, {
      path: "/ws/logs",
      transports: ["websocket"],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });
  }
  return socket;
}

export function subscribeToLogs(callback: (log: string) => void): () => void {
  const ws = getWebSocket();
  ws.on("log", callback);
  return () => {
    ws.off("log", callback);
  };
}
