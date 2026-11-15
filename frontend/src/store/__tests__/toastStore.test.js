// toastStore.test.js — pop-up messages after actions (submitted, saved, errors).
import { describe, it, expect, vi } from "vitest";
import useToastStore from "../toastStore";

describe("toastStore", () => {
  // Why: messages must appear, be removable, and disappear by themselves after 4 s
  it("adds, removes and auto-dismisses toasts", () => {
    vi.useFakeTimers();
    const { addToast } = useToastStore.getState();
    addToast("Saved", "success");
    addToast("Oops", "error");
    expect(useToastStore.getState().toasts.map((t) => t.message)).toEqual(["Saved", "Oops"]);
    useToastStore.getState().removeToast(useToastStore.getState().toasts[0].id);
    expect(useToastStore.getState().toasts).toHaveLength(1);
    vi.advanceTimersByTime(4000);
    expect(useToastStore.getState().toasts).toHaveLength(0);
    vi.useRealTimers();
  });
});
