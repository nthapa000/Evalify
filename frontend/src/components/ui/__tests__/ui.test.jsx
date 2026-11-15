// ui.test.jsx — shared UI building blocks (Button, Badge, Card, Modal, Toast, Skeleton).
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Button from "../Button";
import Badge from "../Badge";
import Card from "../Card";
import Modal from "../Modal";
import ToastContainer from "../Toast";
import { SkeletonCard, SkeletonRow } from "../Skeleton";
import useToastStore from "../../../store/toastStore";

describe("UI components", () => {
  // Why: buttons are disabled while loading so a form cannot be submitted twice
  it("Button disables itself while loading and passes clicks otherwise", () => {
    const onClick = vi.fn();
    const { rerender } = render(<Button onClick={onClick}>Save</Button>);
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onClick).toHaveBeenCalledTimes(1);
    rerender(<Button onClick={onClick} loading>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  // Why: badges show statuses (Flagged, Re-evaluated…) with a colour per variant
  it("Badge renders its text with the variant colour", () => {
    render(<Badge variant="warning">Flagged</Badge>);
    expect(screen.getByText("Flagged").className).toMatch(/amber/);
  });

  // Why: cards are the layout block of every page
  it("Card renders header, body and footer", () => {
    render(<Card><Card.Header>H</Card.Header><Card.Body>B</Card.Body><Card.Footer>F</Card.Footer></Card>);
    expect(screen.getByText("H")).toBeInTheDocument();
    expect(screen.getByText("F")).toBeInTheDocument();
  });

  // Why: dialogs (e.g. the teacher's hand-marking form) open, and close on ✕ or Escape
  it("Modal shows only when open and closes on ✕ and Escape", () => {
    const onClose = vi.fn();
    const { rerender } = render(<Modal isOpen={false} onClose={onClose} title="T">body</Modal>);
    expect(screen.queryByText("body")).toBeNull();
    rerender(<Modal isOpen onClose={onClose} title="T">body</Modal>);
    fireEvent.click(screen.getByLabelText("Close"));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  // Why: toasts from the store are shown and can be dismissed by the user
  it("ToastContainer renders and dismisses toasts", () => {
    useToastStore.setState({ toasts: [{ id: 1, message: "Marks submitted", type: "success" }] });
    render(<ToastContainer />);
    expect(screen.getByText("Marks submitted")).toBeInTheDocument();
    fireEvent.click(screen.getByText("✕"));
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  // Why: skeletons fill the layout while data loads (no jumping page)
  it("Skeletons render", () => {
    const { container } = render(<><SkeletonCard /><table><tbody><SkeletonRow /></tbody></table></>);
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(3);
  });
});
