import '@testing-library/jest-dom';
import { expect, vi } from 'vitest';

// Extend expect with jest-dom matchers
// eslint-disable-next-line @typescript-eslint/no-explicit-any
globalThis.expect = expect;

// Mock global objects if needed
globalThis.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));