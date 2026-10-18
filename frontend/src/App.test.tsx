import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("App", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true })));
  it("renders the operations shell and reports a healthy platform", async () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "SwarVox AI" })).toBeInTheDocument();
    expect(await screen.findByText("Platform online")).toBeInTheDocument();
    expect(screen.getByText("Calls today")).toBeInTheDocument();
  });
});
