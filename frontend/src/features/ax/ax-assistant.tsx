"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

import { askAssistant } from "@/features/ax/api";
import { useAxAssistant } from "@/features/ax/ax-assistant-provider";
import { type Position, useDraggable } from "@/features/ax/use-draggable";
import type { AxChatResponse } from "@/types/ax";

// 기획서 5장에서 정한 초기 추천 질문. F1을 첫 칩으로 두는 이유는 처음 쓰는 직원이
// 가장 먼저 누를 질문이기 때문이다.
const SUGGESTED_QUESTIONS = [
  "MS FlowHub에서 어떤 기능을 사용할 수 있나요?",
  "전자결재 문서는 어떻게 작성하나요?",
  "연차·반차는 어떻게 신청하나요?",
  "다른 직원을 어떻게 찾나요?",
  "채용 요청은 어떻게 작성하나요?",
];

const ROUTE_LABELS: Record<string, string> = {
  "/approvals": "전자결재",
  "/employees": "직원 · 부서",
  "/recruitment-requests": "ATS Lite",
  "/": "업무 홈",
};

const COMPACT_QUERY = "(max-width: 640px)";

export function AxAssistant() {
  const { open, setOpen, turns, addTurn, clearTurns, getPosition, savePosition } = useAxAssistant();
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [compact, setCompact] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLElement>(null);

  // 좁은 화면에서는 전체화면 시트라 옮길 필요도, 옮겨서도 안 된다.
  useEffect(() => {
    const media = window.matchMedia(COMPACT_QUERY);
    const sync = () => setCompact(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [turns, pending]);

  const panelDrag = useDraggable({
    elementRef: panelRef,
    getPosition: useCallback(() => getPosition("panel"), [getPosition]),
    onCommit: useCallback((position: Position) => savePosition("panel", position), [savePosition]),
    disabled: compact,
  });

  async function ask(question: string) {
    const trimmed = question.trim();
    if (!trimmed || pending) return;
    setInput("");
    setPending(true);
    try {
      const answer = await askAssistant(trimmed);
      addTurn({ question: trimmed, answer, error: null });
    } catch (reason: unknown) {
      const message = reason instanceof Error ? reason.message : "도우미를 사용할 수 없습니다.";
      addTurn({ question: trimmed, answer: null, error: message });
    } finally {
      setPending(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void ask(input);
  }

  return (
    <>
      <button
        aria-expanded={open}
        aria-label={open ? "도움말 닫기" : "도움말 열기"}
        className="ax-launcher"
        onClick={() => setOpen(!open)}
        type="button"
      >
        {open ? "×" : "?"}
      </button>

      {open && (
        <section
          aria-label="MS FlowHub 도우미"
          className="ax-panel"
          ref={panelRef}
        >
          <header className="ax-panel-header" {...panelDrag.handlers}>
            <div>
              <strong>MS FlowHub 도우미</strong>
              <small>{compact ? "등록된 매뉴얼과 FAQ에서 찾아드립니다" : "제목을 끌어 옮길 수 있습니다"}</small>
            </div>
            <button
              aria-label="닫기"
              className="modal-close"
              onClick={() => setOpen(false)}
              onPointerDown={(event) => event.stopPropagation()}
              type="button"
            >
              ×
            </button>
          </header>

          <div className="ax-log" ref={logRef}>
            {turns.length === 0 && (
              <div className="ax-intro">
                <p>무엇을 도와드릴까요?</p>
                <div className="ax-suggestions">
                  {SUGGESTED_QUESTIONS.map((question) => (
                    <button key={question} onClick={() => void ask(question)} type="button">{question}</button>
                  ))}
                </div>
              </div>
            )}

            {turns.map((turn, index) => (
              <div className="ax-turn" key={`${turn.question}-${index}`}>
                <p className="ax-question">{turn.question}</p>
                {turn.error ? (
                  <div className="ax-card ax-card-error">
                    <p>{turn.error}</p>
                    <div className="ax-card-actions">
                      <Link href="/faq" onClick={() => setOpen(false)}>FAQ 보기</Link>
                      <Link href="/manuals" onClick={() => setOpen(false)}>매뉴얼 보기</Link>
                    </div>
                  </div>
                ) : (
                  turn.answer && <AnswerCard answer={turn.answer} onAsk={ask} onNavigate={() => setOpen(false)} />
                )}
              </div>
            ))}

            {pending && <p className="ax-pending">찾는 중입니다…</p>}
          </div>

          <form className="ax-input" onSubmit={submit}>
            <input
              aria-label="질문 입력"
              maxLength={300}
              onChange={(event) => setInput(event.target.value)}
              placeholder="궁금한 점을 입력하세요"
              value={input}
            />
            <button className="primary-button" disabled={pending || !input.trim()} type="submit">전송</button>
          </form>
          {turns.length > 0 && (
            <button className="ax-clear" onClick={clearTurns} type="button">대화 지우기</button>
          )}
        </section>
      )}
    </>
  );
}

function AnswerCard({
  answer,
  onAsk,
  onNavigate,
}: {
  answer: AxChatResponse;
  onAsk: (question: string) => Promise<void>;
  onNavigate: () => void;
}) {
  const manualHref = answer.source?.manual_slug ? `/manuals/${answer.source.manual_slug}` : null;
  const hasAction = Boolean(manualHref || answer.route);

  return (
    <div className="ax-card">
      <p className="ax-answer">{answer.answer}</p>

      {/* 접전이면 확신하지 않고 사용자가 고르게 한다. 후보를 누르면 그 질문으로 다시 묻는다. */}
      {answer.candidates.length > 0 && (
        <div className="ax-candidates">
          {answer.candidates.map((candidate) => (
            <button key={candidate.doc_id} onClick={() => void onAsk(candidate.title)} type="button">
              {candidate.title}
              <small>{candidate.category}</small>
            </button>
          ))}
        </div>
      )}

      {hasAction && (
        <div className="ax-card-actions">
          {/* 매뉴얼은 새 탭으로 연다. 보던 화면을 그대로 두고 매뉴얼을 옆에 놓고 볼 수 있다. */}
          {manualHref && (
            <Link href={manualHref} rel="noreferrer" target="_blank">자세히 보기</Link>
          )}
          {answer.route && (
            <Link href={answer.route} onClick={onNavigate}>
              {ROUTE_LABELS[answer.route] ?? "관련 화면"}으로 이동
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
