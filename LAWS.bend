import Base

# The same affine owner can accompany either outcome without consuming it.
# This structural rule does not prove the foreign bridge's behavior.
law return_window:
  for -A: Type
  for window: Window
  for result: Result<&1, &1, U32 & String, A>
  Window & Result<&1, &1, U32 & String, A>

# Native requirements:
# - Return the owner's X11 display name and resource ID.
# - Keep ownership outside Result on success and failure.
# - Synchronize prior requests without discarding queued events.
# - References own no resource and expire when the owner closes.
# - IDs may be reused after close; a reference cannot recreate a Window.
# - Unsupported backends return ENOTSUP.
# Xlib operations share state and must remain on Bend's IO thread.
