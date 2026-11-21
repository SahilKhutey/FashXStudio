# ARC-08: 14 — Visual Editor Architecture

## 1. Visual Drag-and-Drop Canvas
The Visual Editor enables direct manipulation of the menu structure:
- **Component Tree**: Hierarchical view of active slots and component instances.
- **Interactive Canvas**: Live WYSIWYG preview rendering components inside an isolated iframe.
- **Property Inspector**: Context-sensitive panel displaying schema-defined properties for the selected component.
- **Drag & Drop**: Reordering components within authorized slots.
- **Shared Draft Model**: Operates on the identical canonical configuration document as the Settings Editor.
