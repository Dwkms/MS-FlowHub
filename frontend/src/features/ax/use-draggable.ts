"use client";

import { type PointerEvent as ReactPointerEvent, type RefObject, useEffect, useRef } from "react";

export interface Position {
  left: number;
  top: number;
}

// 이 거리 안에서 손을 떼면 드래그가 아니라 클릭으로 본다(플로팅 버튼용).
const DRAG_THRESHOLD_PX = 4;

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function clampToViewport(position: Position, width: number, height: number): Position {
  return {
    left: clamp(position.left, 0, Math.max(0, window.innerWidth - width)),
    top: clamp(position.top, 0, Math.max(0, window.innerHeight - height)),
  };
}

function applyPosition(element: HTMLElement, position: Position) {
  element.style.left = `${position.left}px`;
  element.style.top = `${position.top}px`;
  element.style.right = "auto";
  element.style.bottom = "auto";
}

function clearPosition(element: HTMLElement) {
  element.style.left = "";
  element.style.top = "";
  element.style.right = "";
  element.style.bottom = "";
}

/**
 * 요소를 끌어 옮긴다. 화면 밖으로 나가지 않도록 항상 가둔다.
 *
 * 위치를 React state가 아니라 DOM에 직접 쓴다. 포인터가 움직일 때마다 리렌더하지
 * 않아 부드럽고, 서버 렌더 결과와 첫 클라이언트 렌더가 같아 하이드레이션 경고도 없다.
 */
export function useDraggable({
  elementRef,
  getPosition,
  onCommit,
  disabled = false,
}: {
  elementRef: RefObject<HTMLElement | null>;
  getPosition: () => Position | null;
  onCommit: (position: Position) => void;
  disabled?: boolean;
}) {
  const dragRef = useRef<{ pointerId: number; grabX: number; grabY: number } | null>(null);
  const draggedRef = useRef(false);

  // 저장된 위치를 붙인다. 메뉴를 옮겨 다시 마운트돼도 같은 자리에 나타난다.
  // 좁은 화면에서는 전체화면 시트이므로 인라인 위치를 걷어낸다.
  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;
    if (disabled) {
      clearPosition(element);
      return;
    }
    const saved = getPosition();
    if (saved) {
      applyPosition(element, clampToViewport(saved, element.offsetWidth, element.offsetHeight));
    }
  }, [disabled, elementRef, getPosition]);

  // 창을 줄이면 화면 밖으로 나갈 수 있으므로 다시 안으로 넣는다.
  useEffect(() => {
    if (disabled) return;
    function keepInView() {
      const element = elementRef.current;
      if (!element) return;
      const saved = getPosition();
      if (!saved) return;
      const next = clampToViewport(saved, element.offsetWidth, element.offsetHeight);
      applyPosition(element, next);
      onCommit(next);
    }
    window.addEventListener("resize", keepInView);
    return () => window.removeEventListener("resize", keepInView);
  }, [disabled, elementRef, getPosition, onCommit]);

  function onPointerDown(event: ReactPointerEvent<HTMLElement>) {
    if (disabled) return;
    const element = elementRef.current;
    if (!element) return;
    const rect = element.getBoundingClientRect();
    dragRef.current = {
      pointerId: event.pointerId,
      grabX: event.clientX - rect.left,
      grabY: event.clientY - rect.top,
    };
    draggedRef.current = false;
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event: ReactPointerEvent<HTMLElement>) {
    const drag = dragRef.current;
    const element = elementRef.current;
    if (!drag || drag.pointerId !== event.pointerId || !element) return;
    const rect = element.getBoundingClientRect();
    const wanted = { left: event.clientX - drag.grabX, top: event.clientY - drag.grabY };
    if (
      Math.abs(wanted.left - rect.left) > DRAG_THRESHOLD_PX ||
      Math.abs(wanted.top - rect.top) > DRAG_THRESHOLD_PX
    ) {
      draggedRef.current = true;
    }
    applyPosition(element, clampToViewport(wanted, rect.width, rect.height));
  }

  function onPointerUp(event: ReactPointerEvent<HTMLElement>) {
    if (dragRef.current?.pointerId !== event.pointerId) return;
    dragRef.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);
    const element = elementRef.current;
    if (!element || !draggedRef.current) return;
    const rect = element.getBoundingClientRect();
    onCommit({ left: rect.left, top: rect.top });
  }

  /** 방금 끌었는지 확인하고 플래그를 지운다. 드래그 직후 이어지는 click을 무시할 때 쓴다. */
  function consumeDragged() {
    const dragged = draggedRef.current;
    draggedRef.current = false;
    return dragged;
  }

  return {
    consumeDragged,
    handlers: {
      onPointerDown,
      onPointerMove,
      onPointerUp,
      onPointerCancel: onPointerUp,
    },
  };
}
