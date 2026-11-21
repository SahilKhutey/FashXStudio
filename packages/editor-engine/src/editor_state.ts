import type { MenuCustomization } from '../../contracts/generated/customization';
import { HistoryManager } from './history';
import type { EditorCommand } from './commands';

export type EditorMode = 'settings' | 'visual';
export type ViewportSize = '320px' | '375px' | '768px' | '1024px' | '1440px';

export class EditorSession {
  public mode: EditorMode = 'settings';
  public viewport: ViewportSize = '1024px';
  public selectedComponentId: string | null = null;
  public hasUnsavedChanges: boolean = false;
  private history: HistoryManager;

  constructor(
    public draft: MenuCustomization,
    public serverRevision: number = 1
  ) {
    this.history = new HistoryManager(50);
  }

  setMode(newMode: EditorMode): void {
    this.mode = newMode;
  }

  setViewport(vp: ViewportSize): void {
    this.viewport = vp;
  }

  selectComponent(id: string | null): void {
    this.selectedComponentId = id;
  }

  executeCommand(command: EditorCommand): void {
    this.history.push(this.draft);
    this.draft = command.execute(this.draft);
    this.hasUnsavedChanges = true;
  }

  undo(): boolean {
    if (!this.history.canUndo()) return false;
    const restored = this.history.undo(this.draft);
    if (restored) {
      this.draft = restored;
      this.hasUnsavedChanges = true;
      return true;
    }
    return false;
  }

  redo(): boolean {
    if (!this.history.canRedo()) return false;
    const restored = this.history.redo(this.draft);
    if (restored) {
      this.draft = restored;
      this.hasUnsavedChanges = true;
      return true;
    }
    return false;
  }

  markSaved(newRevision: number): void {
    this.serverRevision = newRevision;
    this.hasUnsavedChanges = false;
  }
}
