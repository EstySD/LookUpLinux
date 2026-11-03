# Phase 13: Discoverable application

Agent choices under --auto: a small native home window opens from an explicit application launch, with current shortcut instructions and buttons for settings, saved words and review. Left-click tray reopens it. Closing home hides it and keeps translation running. Autostart and cold hotkey launch remain background operations. Repeated explicit launch activates the existing owner home via DBus.

Use existing PyQt6 widgets, system font/palette/spacing and existing child windows. No new wizard, dependency or persistent onboarding flag. Keep the trigger desktop identity for shortcut compatibility; add a separate visible launcher, hide the trigger entry from application menus.
