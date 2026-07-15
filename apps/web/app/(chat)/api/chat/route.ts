import { geolocation } from "@vercel/functions";
import {
  createUIMessageStream,
  createUIMessageStreamResponse,
  generateId,
} from "ai";
import { after } from "next/server";
import { createResumableStreamContext } from "resumable-stream";
import { auth, type UserType } from "@/app/(auth)/auth";
import { entitlementsByUserType } from "@/lib/ai/entitlements";
import { isProductionEnvironment } from "@/lib/constants";
import {
  createStreamId,
  deleteChatById,
  getChatById,
  getMessageCountByUserId,
  getMessagesByChatId,
  saveChat,
  saveMessages,
  updateChatTitleById,
  updateMessage,
} from "@/lib/db/queries";
import type { DBMessage } from "@/lib/db/schema";
import { ChatSDKError } from "@/lib/errors";
import type { ChatMessage } from "@/lib/types";
import { convertToUIMessages, generateUUID } from "@/lib/utils";
//import { generateTitleFromUserMessage } from "../../actions";
import { type PostRequestBody, postRequestBodySchema } from "./schema";

export const maxDuration = 60;

function getStreamContext() {
  try {
    return createResumableStreamContext({ waitUntil: after });
  } catch (_) {
    return null;
  }
}

export { getStreamContext };

export async function POST(request: Request) {
  let requestBody: PostRequestBody;

  try {
    const json = await request.json();
    requestBody = postRequestBodySchema.parse(json);
  } catch (_) {
    return new ChatSDKError("bad_request:api").toResponse();
  }

  try {
    const { id, message, messages, selectedVisibilityType } = requestBody;
    const session = await auth();

    if (!session?.user) {
      return new ChatSDKError("unauthorized:chat").toResponse();
    }

    const userType: UserType = session.user.type;
    const messageCount = await getMessageCountByUserId({
      id: session.user.id,
      differenceInHours: 24,
    });

    if (messageCount > entitlementsByUserType[userType].maxMessagesPerDay) {
      return new ChatSDKError("rate_limit:chat").toResponse();
    }

    const isToolApprovalFlow = Boolean(messages);
    const chat = await getChatById({ id });
    let messagesFromDb: DBMessage[] = [];
    let titlePromise: Promise<string> | null = null;

    if (chat) {
      if (chat.userId !== session.user.id) {
        return new ChatSDKError("forbidden:chat").toResponse();
      }
      if (!isToolApprovalFlow) {
        messagesFromDb = await getMessagesByChatId({ id });
      }
    } else if (message?.role === "user") {
      await saveChat({
        id,
        userId: session.user.id,
        title: "New chat",
        visibility: selectedVisibilityType,
      });
      
      // 👇 PERBAIKAN TypeScript: Pakai trik 'as any' biar linter gak bawel soal tipe gambar/file 👇
      const textPart = message.parts?.find((part: any) => part.type === "text") as any;
      const textContent = textPart?.text || "Chat Baru";
      titlePromise = Promise.resolve(textContent.substring(0, 30) + "...");
    }

    const uiMessages = isToolApprovalFlow
      ? (messages as ChatMessage[])
      : [...convertToUIMessages(messagesFromDb), message as ChatMessage];

    if (message?.role === "user") {
      await saveMessages({
        messages: [
          {
            chatId: id,
            id: message.id,
            role: "user",
            parts: message.parts,
            attachments: [],
            createdAt: new Date(),
          },
        ],
      });
    }

    // ======================================================================
    // 🧠 OPERASI TRANSPLANTASI: MENGHUBUNGKAN VERCEL KE FASTAPI RENDER
    // ======================================================================
    const stream = createUIMessageStream({
      originalMessages: isToolApprovalFlow ? uiMessages : undefined,
      execute: async ({ writer: dataStream }) => {
        
        // 1. Fungsi Pembantu: Mengekstrak teks dari format UI Vercel
        const extractText = (msg: any) => {
          if (!msg) return "";
          if (typeof msg.content === 'string' && msg.content) return msg.content;
          if (Array.isArray(msg.parts)) return msg.parts.map((p: any) => p.text || "").join("");
          return "";
        };

       // 2. Siapkan Data untuk dikirim ke API Kamu
        const userMessageContent = extractText(message) || extractText(uiMessages[uiMessages.length - 1]);
        // 👇 PERBAIKAN MEMORI: Ubah 'assistant' menjadi 'model' agar dikenali Gemini 👇
        const historyPayload = uiMessages.slice(0, -1).map(m => ({
            role: m.role === "user" ? "user" : "model", 
            content: extractText(m)
        }));

        let sentaAnswer = "";

        // 3. Tembak ke API FastAPI Senta di Render
        try {
            const API_RENDER_URL = "https://ai-sentuhtanahku-api.onrender.com/api/chat";

            const fastApiResponse = await fetch(API_RENDER_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    pesan: userMessageContent,
                    session_id: id,
                    riwayat: historyPayload
                })
            });

            if (fastApiResponse.ok) {
                // Server balas sukses — ambil jawaban Senta
                const data = await fastApiResponse.json();
                sentaAnswer = data.jawaban
                    || "Hmm, Senta lagi bingung nih, coba tanya lagi ya Kak 🙏";
            } else {
                // Server Render HIDUP tapi balas error (mis. 5xx dari FastAPI / LLM bermasalah)
                const errText = await fastApiResponse.text().catch(() => "");
                console.error(`FastAPI Error [${fastApiResponse.status}]:`, errText);
                sentaAnswer = `Duh, mesin AI Senta lagi ada kendala teknis nih Kak (kode ${fastApiResponse.status}). Coba kirim ulang beberapa saat lagi ya 🙏`;
            }
        } catch (error) {
            // Gagal MENJANGKAU server sama sekali (jaringan / timeout / server sleep/mati)
            console.error("Error nembak Render:", error);
            sentaAnswer = "Maaf Kak, Senta lagi nggak bisa nyambung ke server utama nih 😢. Kemungkinan server-nya lagi \"bangun tidur\" (cold start). Coba refresh & kirim ulang pesannya ya!";
        }

        // 4. Kirim balasan FastAPI ke layar UI Vercel
        const textPartId = generateUUID();
        // Buka blok teks
        dataStream.write({ type: 'text-start', id: textPartId });
        // Isi blok teks dengan jawaban Senta
        dataStream.write({ type: 'text-delta', delta: sentaAnswer, id: textPartId });
        // 👇 PERBAIKAN: Tutup blok teks secara resmi agar UI Vercel tidak menunggu lagi 👇
        dataStream.write({ type: 'text-end', id: textPartId });

        // 5. Simpan histori jawaban Senta ke Database Vercel agar tersimpan di Sidebar
        const assistantMessageId = generateUUID();
        await saveMessages({
            messages: [{
                id: assistantMessageId,
                role: "assistant",
                parts: [{ type: "text", text: sentaAnswer }],
                createdAt: new Date(),
                attachments: [],
                chatId: id,
            }]
        });

        // 6. Simpan judul chat (Fitur bawaan template)
        if (titlePromise) {
          const title = await titlePromise;
          dataStream.write({ type: "data-chat-title", data: title });
          updateChatTitleById({ chatId: id, title });
        }
      },
      generateId: generateUUID,
      onFinish: async () => {
         // Sengaja dikosongkan karena penyimpanan DB sudah kita lakukan secara manual di langkah ke-5
      },
      onError: () => "Oops, an error occurred!",
    });

    return createUIMessageStreamResponse({
      stream,
      async consumeSseStream({ stream: sseStream }) {
        if (!process.env.REDIS_URL) {
          return;
        }
        try {
          const streamContext = getStreamContext();
          if (streamContext) {
            const streamId = generateId();
            await createStreamId({ streamId, chatId: id });
            await streamContext.createNewResumableStream(
              streamId,
              () => sseStream
            );
          }
        } catch (_) {
          // ignore redis errors
        }
      },
    });
  } catch (error) {
    const vercelId = request.headers.get("x-vercel-id");

    if (error instanceof ChatSDKError) {
      return error.toResponse();
    }

    console.error("Unhandled error in chat API:", error, { vercelId });
    return new ChatSDKError("offline:chat").toResponse();
  }
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");

  if (!id) {
    return new ChatSDKError("bad_request:api").toResponse();
  }

  const session = await auth();

  if (!session?.user) {
    return new ChatSDKError("unauthorized:chat").toResponse();
  }

  const chat = await getChatById({ id });

  if (chat?.userId !== session.user.id) {
    return new ChatSDKError("forbidden:chat").toResponse();
  }

  const deletedChat = await deleteChatById({ id });

  return Response.json(deletedChat, { status: 200 });
}