import type { MenuCustomization } from '../../contracts/generated/customization';

export class HistoryManager {
  private undoStack: MenuCustomization[] = [];
  private redoStack: MenuCustomization[] = [];
  private maxDepth: number;

  constructor(maxDepth: number = 50) {
    this.maxDepth = maxDepth;
  }

  push(state: MenuCustomization): void {
    const cloned = JSON.parse(JSON.stringify(state));
    this.undoStack.push(cloned);
    if (this.undoStack.length > this.maxDepth) {
      this.undoStack.shift();
    }
    this.redoStack = [];
  }

  undo(currentState: MenuCustomization): MenuCustomization | null {
    if (this.undoStack.length === 0) return null;
    const prev = this.undoStack.pop()!;
    this.redoStack.push(JSON.parse(JSON.stringify(currentState)));
    return prev;
  }

  redo(currentState: MenuCustomization): MenuCustomization | null {
    if (this.redoStack.length === 0) return null;
    const next = this.redoStack.pop()!;
    this.undoStack.push(JSON.parse(JSON.stringify(currentState)));
    return next;
  }

  canUndo(): boolean {
    return this.undoStack.length > 0;
  }

  canRedo(): boolean {
    return this.redoStack.length > 0;
  }

  clear(): void {
    this.undoStack = [];
    this.redoStack = [];
  }
}
