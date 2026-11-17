# Hand-drawn diagrams (06, 10, 11)

`sketch06.mjs` draws `images/06_sequence_exam_round.jpg` in the style of Excalidraw: sketchy strokes from roughjs
(the library Excalidraw uses) and Virgil, Excalidraw's handwriting font. The content is the same as the Mermaid
diagram 06 in `03_Sequence_Diagrams.md`; change both together.

To draw it again (Node 18 or newer):

```bash
npm install roughjs@4.6.6 puppeteer
# Virgil.woff2 (SIL Open Font License) ships in the @excalidraw/excalidraw package: dist/excalidraw-assets/Virgil.woff2
VIRGIL_FONT=/path/to/Virgil.woff2 node sketch06.mjs out.png
```

Then convert `out.png` to JPG (any image tool) and replace `images/06_sequence_exam_round.jpg`.

## RAG diagrams (10 and 11)

`rag_architecture.mjs` and `rag_sequence.mjs` draw the answer-key assistant (RAG) with the shared helpers in
`sketch_lib.mjs` (boxes, arrows, numbered steps, frames, notes in the same colour key):

```bash
VIRGIL_FONT=/path/to/Virgil.woff2 node rag_architecture.mjs 10.png
VIRGIL_FONT=/path/to/Virgil.woff2 node rag_sequence.mjs 11.png
```

