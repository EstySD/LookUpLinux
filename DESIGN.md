# Native KDE design contract

The established visual authority is KDE Breeze, explicitly chosen in the project
brief. Qt's system style, palette, font and platform icons supply the visual
system. This is an Operate surface for quick dictionary reading.

The popup presents the searched form first, optional lemma/transcription next,
then ordered dictionary sources and part-of-speech senses, full article text,
source context and optional translation, and the confirmed search count.
Absent metadata stays absent. A single vertical scroll area bounds long content.

Use normal Qt layouts and style metrics; hierarchy comes from text size/weight
and spacing, without nested decorative cards, custom gradients, shadows or a
new color palette. All dictionary and provider content is plain selectable text.
Control labels and errors are Russian. Icons supplement text labels.

Loading, no match, platform/dependency failure, offline failure and save failure
are distinct readable states. Results never reopen a dismissed popup or replace
a newer request. Theme changes follow the system palette without application
restart. Exact surface dimensions and timings belong to Phase 5 UI-SPEC.md.
