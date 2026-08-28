from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TextArea, DirectoryTree, Button, Input, Label, Static
from textual.binding import Binding
from textual.reactive import reactive
from textual import events, on
from textual.screen import ModalScreen
from textual.containers import Center, Middle, Vertical
from typing import Iterable
from pathlib import Path
import os

TEXT = ""

class FileSystemTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if not path.name.startswith('.')]

class Editor(TextArea):
    async def _on_key(self, event: events.Key) -> None:
        pairs = {"(": ")", "[": "]", "{": "}", "\"": "\"", "\'": "\'"}
        if event.character in pairs:
            self.insert(event.character + pairs[event.character])
            self.move_cursor_relative(columns=-1)
            event.prevent_default()
        else:
            await super()._on_key(event)

class Walrus(App):
    CSS_PATH = "walrus.tcss"
    BINDINGS = [
        Binding("ctrl+q", "quit_walrus", "Quit", show=True),
        Binding("ctrl+s", "save_file", "Save", show=True),
        Binding("ctrl+r", "refresh_file_explorer", "Refresh explorer", show=True),
        Binding("ctrl+t", "toggle_dark", "Toggle dark mode", show=True),
    ]
    
    current_file = reactive[Path | None](None)
    
    def on_mount(self) -> None:
        self.query_one(TextArea).focus()
        self.theme = "dracula"
        self.title = "Walrus v0.1"
        self.query_one(Editor).load_text(TEXT)

    def action_quit_walrus(self):
        self.exit()

    def action_toggle_dark(self) -> None:
        self.theme = ("dracula" if self.theme == "textual-light" else "textual-light")

    def action_refresh_file_explorer(self) -> None:
        self.query_one(FileSystemTree).reload()

    def action_save_file(self) -> None:
        self.push_screen(
            SaveFileScreen(self.current_file),
            self._save_file,
        )

    def _save_file(self, path: Path | None) -> None:
        if path is None:
            return
        try:
            path.write_text(self.query_one(Editor).text)
            self.current_file = path
            self.sub_title = str(path)
            self.push_screen(MessageScreen("File saved successfully!"))
        except Exception as e:
            self.push_screen(MessageScreen(f"Error saving file: {e}"))

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.current_file = event.path
        try:
            content = self.current_file.read_text()
            self.query_one(Editor).load_text(content)
            self.sub_title = str(self.current_file)
        except UnicodeDecodeError:
            self.query_one(Editor).load_text("[Binary file content not displayable]")
            self.sub_title = f"[Binary] {self.current_file}"
        except Exception as e:
            self.query_one(Editor).load_text(f"Error reading file: {e}")
            self.sub_title = "[Error]"
        
        self.query_one(Editor).focus()

    def compose(self) -> ComposeResult:
        yield FileSystemTree("./", classes="box file", name="systemtree")
        yield Header()
        yield Footer()
        yield Editor.code_editor(TEXT, language=None, theme="monokai", name="code_editor", classes="box")

class SaveFileScreen(ModalScreen[Path | None]):
    def __init__(self, current_file: Path | None):
        super().__init__()
        self.current_file = current_file

    def compose(self) -> ComposeResult:
        title = "Save file..." if self.current_file else "Save file as..."
        yield Middle(
            Center(
                Vertical(
                    Label(title, id="save-title"),
                    Input(
                        value=str(self.current_file) if self.current_file else "",
                        placeholder="File name",
                        id="save-path",
                    ),
                    Center(
                        Button("Cancel", id="cancel-save"),
                        Button("Save", variant="primary", id="confirm-save"),
                    ),
                    classes="dialog",
                )
            )
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-save":
            self.dismiss(None)
            return

        path = self.query_one("#save-path", Input).value.strip()
        if path:
            self.dismiss(Path(path))

    def on_mount(self) -> None:
        self.query_one(Input).focus()

class MessageScreen(ModalScreen):
    def __init__(self, message: str):
        super().__init__()
        self.message = message
    
    def compose(self) -> ComposeResult:
        yield Middle(Center(Static(self.message), classes="dialog"))
        yield Footer()

    def on_mount(self) -> None:
        self.set_timer(2, self.app.pop_screen)
        

if __name__ == "__main__":
    app = Walrus()
    app.run()