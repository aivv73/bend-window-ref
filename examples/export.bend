import Base
import ../winref.bend as W

def show_ref(ref: W.WindowRef) -> IO(Unit):
  match ref:
    case W.X11WindowRef{display, id}:
      do IO<Unit>:
        IO.print(display)
        IO.print(U32.show(id))

def report(result: Result<&1, &1, U32 & String, W.WindowRef>) -> IO(Unit):
  match result:
    case Done{ref}:
      show_ref(ref)
    case Fail{(code, message)}:
      IO.die(Unit, code, message)

def exported(pair: Window & Result<&1, &1, U32 & String, W.WindowRef>) -> IO(Unit):
  (window, result) = pair
  do IO<Unit>:
    window : Window <- Window.set_title(window, "Window reference exported")
    report(result)
    IO.sleep(3000)
    Window.close(window)

def framed(frame: Window & Image & List<Event>) -> IO(Unit):
  (window, image, events) = frame
  IO.bind(Window & Result<&1, &1, U32 & String, W.WindowRef>, Unit,
    W.WinRef.export(window), exported)

def opened(result: Result<&1, &1, U32 & String, Window>) -> IO(Unit):
  match result:
    case Done{window}:
      IO.bind(Window & Image & List<Event>, Unit,
        Window.frame(window, Pix{0}), framed)
    case Fail{(code, message)}:
      IO.die(Unit, code, message)

def main() -> IO(Unit):
  IO.bind(Result<&1, &1, U32 & String, Window>, Unit,
    Window.open("Window reference", 64, 48), opened)
