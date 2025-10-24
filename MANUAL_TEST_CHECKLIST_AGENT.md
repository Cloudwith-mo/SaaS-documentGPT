# Frontend Manual Test Checklist (AI Agent)

Use this end-to-end checklist whenever you validate `web/dev.html`. Follow every step in order (A → Z) to ensure every control, button, and feature receives coverage.

## A. Access & Warm-Up
1. Open `https://documentgpt.io/dev.html` in a fresh session (incognito or cleared localStorage).
2. Confirm skeleton shimmer shows while the app bootstraps.
3. Verify chat placeholder message renders once UI loads.

## B. Branding & Navigation
1. Click the DocumentGPT logo and ensure it resets to the current document.
2. Toggle the sidebar visibility using the hamburger button (should slide in/out in ChatPDF mode).
3. Open the Library modal, scroll the list, select a document, and close via the × button.

## C. Authentication Flows
1. Open the login modal, attempt invalid credentials (expect validation error).
2. Trigger “Forgot password”, verify email input prompt appears, then cancel.
3. Close the login modal and ensure the UI state is unchanged.

## D. Document Management
1. Create a new blank document via “New chat”.
2. Create a folder, move the document into it, then switch between folders.
3. Delete the document, confirm the toast shows the undo action, then undo.

## E. Upload Pipeline
1. Click “Upload PDF”, choose `real-test-doc.txt`.
2. Observe progress overlay (Uploading → Extracting → Embedding → Indexing).
3. Confirm summary + suggested questions render via `renderArtifacts`.

## F. Editor Surface
1. Type text into the editor and confirm autosave kicks in (`Saving…` → `Saved`).
2. Use toolbar buttons: Bold, Italic, Underline, Bullet list, Number list.
3. Adjust zoom in/out, then reset by toggling focus mode.

## G. Keyboard Shortcuts
1. Press `⌘K` / `Ctrl+K` to open the command palette.
2. Run “Upload file” from palette (should focus the file picker).
3. Press `?` to open the shortcuts overlay, then close with `Esc`.

## H. Search & Replace
1. Use the inline Find box to search for “Microsoft”.
2. Verify highlight navigation works (prev/next buttons).
3. Clear search term and ensure highlight styling disappears.

## I. AI Agents Dock
1. Open the Agents menu (`+` button) and run each agent (Summary, Email, Sheets, Calendar, Save, Export).
2. Confirm for each agent: spinner shows, toast displays success/failure, resulting content appears in chat or downloads.
3. Close the agent menu and confirm focus returns to chat input.

## J. Chat Streaming (Primary)
1. Ask “Who founded Microsoft?” and ensure streaming tokens appear immediately.
2. While response is streaming, scroll the chat list to confirm it stays pinned.
3. Interrupt by sending another prompt; verify the previous stream aborts cleanly.

## K. Citation UX
1. Click each inline `[n]` marker; the PDF pane should jump to the correct page.
2. Ensure highlight animation shows and the toast announces the page jump.
3. Open the citation list under the answer and verify doc/page/snippet text.

## L. Suggested Questions
1. Click each suggested question generated after upload.
2. Validate they dispatch chat requests (streaming) and append to history.
3. Confirm usage counter increments without exceeding plan limits.

## M. Modes & Metrics
1. Toggle Research ↔ Journal mode (button beside assistant title).
2. Observe DocIQ stats update when text changes.
3. Open the DocIQ tips modal, read tooltips, then close.

## N. Highlights & Insights
1. Select text in the editor, apply each highlight color, and verify legend entries.
2. Export highlights to a file, then clear all.
3. Open Instant Insights, cycle through Prev/Next, collapse panel.

## O. Mind Map & Exports
1. Add nodes to the mind map canvas and drag them.
2. Export the mind map (should download `.txt`).
3. Use the “Export highlights” and “Export journal” buttons to ensure downloads.

## P. Auto Complete & Suggestions
1. Trigger AI Suggestions card by pausing mid-sentence; accept once, dismiss once.
2. Toggle auto-suggest off/on from Co-Editor panel.
3. Confirm accepted suggestion inserts clean HTML into the editor.

## Q. Voice & Mic
1. Click the microphone button (grant browser mic permission).
2. Speak a short sentence and ensure it populates the chat input.
3. Cancel mic capture and verify UI reverts.

## R. Command Palette Actions
1. Execute “New document” from the palette.
2. Execute “Summarize” command (should auto-populate chat input).
3. Execute “Theme toggle” command and verify background adjusts.

## S. Paywall & Upgrade
1. Manually set `state.usage.chats_used = CONFIG.CHAT_LIMIT` in console.
2. Send another chat to trigger the upgrade modal.
3. Attempt both plan buttons (Monthly/Annual) and ensure Stripe redirect URL appears (can cancel).

## T. Persistence & Sync
1. Reload the page and verify documents/chat history restore from localStorage.
2. Log in with a Cognito test account, then trigger sync (check console log `☁️ Synced to cloud`).
3. Log out and confirm guest state rehydrates.

## U. Error Handling
1. Disconnect network (toggle offline in devtools) and try sending chat → expect offline banner + toast.
2. Reconnect, resend, verify banner disappears.
3. Force an OpenAI error by temporarily clearing API URL, confirm friendly error message.

## V. Streaming Resilience
1. During a long answer, close the sidebar, reopen it, ensure stream continues.
2. Switch focus to another tab, return, confirm stream resumes without duplication.
3. After `[DONE]`, confirm citations persisted in `state.chatHistory`.

## W. Mobile Responsiveness
1. Use responsive mode (375px width) and ensure layout collapses gracefully.
2. Test sidebar toggle, chat input resizing, and streaming in mobile view.
3. Verify modals remain scrollable and closable on small screens.

## X. Accessibility
1. Navigate to sidebar buttons using keyboard Tab order.
2. Activate upload + send via Enter/Space.
3. Use screen reader labels (VoiceOver/NVDA) for key controls (Upload, Send, Agents).

## Y. Performance Checks
1. Record Lighthouse performance on `dev.html` – note TTI & CLS.
2. Validate streaming starts <300ms by observing devtools network waterfall.
3. Ensure no console errors/warnings remain by end of run.

## Z. Final Verification
1. Review chat history to ensure correct user/bot alternation.
2. Clear local state via Settings → Reset (or `localStorage.clear()`), reload to confirm fresh start.
3. Capture screenshots of summary, streaming response, and citation jump as evidence.

> **Submission Note:** Attach logs/snapshots for any failing step, referencing the corresponding checklist letter.
