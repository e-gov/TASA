"""TASA GUI"""

import os
import sys
import platform
import threading

# pylint: disable=no-member
from typing import Any, Callable, Dict
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
import db_act
import helper
import prog

# Constants for window dimensions
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 500
Window.size = (WINDOW_WIDTH, WINDOW_HEIGHT)


def enforce_fixed_size(window: Any, width: int, height: int) -> None:
    """
    Ensure the application window remains a fixed size.

    Args:
        window (Any): The application window object.
        width (int): Desired window width.
        height (int): Desired window height.
    """
    window.size = (width, height)


Window.bind(
    on_resize=lambda instance, w, h: enforce_fixed_size(
        instance, WINDOW_WIDTH, WINDOW_HEIGHT
    )
)


def resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource, whether running as a script or executable.

    Args:
        relative_path (str): The relative path to the resource.

    Returns:
        str: The absolute path to the resource.
    """
    if hasattr(sys, "_MEIPASS"):  # For bundled executables
        base_path = sys._MEIPASS  # pylint: disable=protected-access
    else:  # For development
        base_path = os.path.dirname(os.path.abspath(__file__))

    absolute_path = os.path.join(base_path, relative_path)

    if not os.path.exists(absolute_path):
        print(f"[ERROR] Resource not found at path: {absolute_path}")

    return absolute_path


if platform.system() == "Windows":
    Window.icon = ""
    Window.icon = resource_path("low.ico")
else:
    Window.icon = ""
    Window.icon = resource_path("low.png")


class LoadingPopup(Popup):
    """Popup for displaying a loading indicator."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the loading popup with a title and layout.

        Args:
            **kwargs (Any): Additional keyword arguments for the popup.
        """
        super().__init__(**kwargs)
        self.size_hint = (0.5, 0.3)
        self.auto_dismiss = False
        self.title = "Loading"
        self.add_widget(self._create_layout())

    @staticmethod
    def _create_layout() -> BoxLayout:
        """
        Create the layout for the loading popup.

        Returns:
            BoxLayout: The layout containing the loading message.
        """
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        layout.add_widget(
            Label(text="Please wait...", font_size=18, size_hint=(1, 0.8))
        )
        return layout


class InputPopup(Popup):
    """Popup for accepting user input."""

    def __init__(
        self, title: str, hint_text: str, callback: Callable[[str], None], **kwargs: Any
    ) -> None:
        """
        Initialize the input popup with a title, text input, and submit button.

        Args:
            title (str): Title of the popup.
            hint_text (str): Placeholder text for the input field.
            callback (Callable[[str], None]): Function to handle submitted input.
            **kwargs (Any): Additional keyword arguments for the popup.
        """
        super().__init__(title=title, size_hint=(0.8, 0.35), **kwargs)
        self.callback = callback
        self.input_field = TextInput(
            hint_text=hint_text, multiline=False, size_hint=(1, None), height=40
        )
        submit_button = Button(
            text="Submit", size_hint=(1, None), height=40, background_color=[0, 1, 0, 1]
        )
        submit_button.bind(on_press=self._submit)

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        layout.add_widget(self.input_field)
        layout.add_widget(submit_button)
        self.add_widget(layout)

    def _submit(self, _instance: Button) -> None:
        """
        Handle the submission of user input.

        Args:
            instance (Button): The submit button instance.
        """
        self.callback(self.input_field.text)
        self.dismiss()


class CopyDataPopup(Popup):
    """Popup for copying data between tables."""

    def __init__(
        self, callback: Callable[[str, str, str], None], **kwargs: Any
    ) -> None:
        """
        Initialize the CopyDataPopup with required fields and submit action.

        Args:
            callback (Callable[[str, str, str], None]): Function to call when data is submitted.
            **kwargs (Any): Additional keyword arguments for the popup.
        """
        super().__init__(title="Copy Data", size_hint=(0.8, 0.55), **kwargs)
        self.callback = callback
        self.project_name = TextInput(
            hint_text="Project Name", multiline=False, size_hint=(1, None), height=40
        )
        self.source_env = Spinner(
            text="Source Env",
            values=["dev", "test", "prod"],
            size_hint=(1, None),
            height=40,
        )
        self.target_env = Spinner(
            text="Target Env",
            values=["dev", "test", "prod"],
            size_hint=(1, None),
            height=40,
        )

        submit_button = Button(
            text="Submit", size_hint=(1, None), height=40, background_color=[0, 1, 0, 1]
        )
        submit_button.bind(on_press=self._submit)

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        layout.add_widget(self.project_name)
        layout.add_widget(self.source_env)
        layout.add_widget(self.target_env)
        layout.add_widget(submit_button)
        self.add_widget(layout)

    def _submit(self, _instance: Button) -> None:
        """
        Handle the submission of data from the popup.

        Args:
            instance (Button): The button instance that triggered the submission.
        """
        self.callback(
            self.project_name.text, self.source_env.text, self.target_env.text
        )
        self.dismiss()


class PullWorkflowPopup(Popup):
    """Popup for pulling data from ARVA."""

    def __init__(
        self, callback: Callable[[str, str, str, str], None], **kwargs: Any
    ) -> None:
        """
        Initialize the PullWorkflowPopup with required fields and submit action.

        Args:
            callback (Callable[[str, str, str, str], None]):
            Function to call when data is submitted.
            **kwargs (Any): Additional keyword arguments for the popup.
        """
        super().__init__(title="Pull Data from ARVA", size_hint=(0.8, 0.65), **kwargs)
        self.callback = callback
        self.project_name = TextInput(
            hint_text="Project Name", multiline=False, size_hint=(1, None), height=40
        )
        self.source_env = Spinner(
            text="Source Env",
            values=["dev", "test", "prod"],
            size_hint=(1, None),
            height=40,
        )
        self.token_input = TextInput(
            hint_text="ARVA Token", multiline=False, size_hint=(1, None), height=40
        )
        self.article_id_input = TextInput(
            hint_text="Article IDs (comma-separated)",
            multiline=False,
            size_hint=(1, None),
            height=40,
        )

        submit_button = Button(
            text="Submit", size_hint=(1, None), height=40, background_color=[0, 1, 0, 1]
        )
        submit_button.bind(on_press=self._submit)

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        layout.add_widget(self.project_name)
        layout.add_widget(self.token_input)
        layout.add_widget(self.article_id_input)
        layout.add_widget(self.source_env)
        layout.add_widget(submit_button)
        self.add_widget(layout)

    def _submit(self, _instance: Button) -> None:
        """
        Handle the submission of data from the popup.

        Args:
            instance (Button): The button instance that triggered the submission.
        """
        self.callback(
            self.project_name.text,
            self.source_env.text,
            self.token_input.text,
            self.article_id_input.text,
        )
        self.dismiss()


class InsertWorkflowPopup(Popup):
    """Popup for inserting data into ARVA."""

    def __init__(
        self, callback: Callable[[str, str, str], None], **kwargs: Any
    ) -> None:
        """
        Initialize the InsertWorkflowPopup with required fields and submit action.

        Args:
            callback (Callable[[str, str, str], None]): Function to call when data is submitted.
            **kwargs (Any): Additional keyword arguments for the popup.
        """
        super().__init__(title="Insert Data to ARVA", size_hint=(0.8, 0.55), **kwargs)
        self.callback = callback
        self.project_name = TextInput(
            hint_text="Project Name", multiline=False, size_hint=(1, None), height=40
        )
        self.target_env = Spinner(
            text="Target Env",
            values=["dev", "test", "prod"],
            size_hint=(1, None),
            height=40,
        )
        self.token_input = TextInput(
            hint_text="ARVA Token", multiline=False, size_hint=(1, None), height=40
        )

        submit_button = Button(
            text="Submit", size_hint=(1, None), height=40, background_color=[0, 1, 0, 1]
        )
        submit_button.bind(on_press=self._submit)

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        layout.add_widget(self.project_name)
        layout.add_widget(self.token_input)
        layout.add_widget(self.target_env)
        layout.add_widget(submit_button)
        self.add_widget(layout)

    def _submit(self, _instance: Button) -> None:
        """
        Handle the submission of data from the popup.

        Args:
            instance (Button): The button instance that triggered the submission.
        """
        self.callback(
            self.project_name.text, self.target_env.text, self.token_input.text
        )
        self.dismiss()


class MainScreen(BoxLayout):
    """Main application screen."""

    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        """
        Initialize the main application screen.

        Args:
            **kwargs (Dict[str, Any]): Additional keyword arguments for the layout.
        """
        super().__init__(orientation="vertical", spacing=10, padding=20, **kwargs)
        self.loading_popup = LoadingPopup()
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the main UI components."""
        # Add logo at the top
        self.add_widget(
            Image(
                source=resource_path("low.png"),
                size_hint=(1, 0.3),
            )
        )

        # Add title
        self.add_widget(Label(text="TASA", font_size=28, size_hint=(1, 0.1)))

        # Add buttons
        buttons = [
            ("Create a DB File", self.create_db),
            ("Copy Data Between Tables", self.copy_data),
            ("Pull Data from ARVA", self.pull_data),
            ("Insert Data to ARVA", self.insert_data),
        ]
        for label, action in buttons:
            self.add_widget(self._create_button(label, action))

        # Add log area at the bottom
        self.log_output = self._create_log_area()
        self.add_widget(self.log_output)

    @staticmethod
    def _create_button(label: str, action: Callable[[Button], None]) -> Button:
        """
        Create a standardized button with the given label and action.

        Args:
            label (str): The text to display on the button.
            action (Callable[[Button], None]): The function to call when the button is pressed.

        Returns:
            Button: The created button widget.
        """
        button = Button(text=label, size_hint=(1, None), height=50)
        button.bind(on_press=action)
        return button

    @staticmethod
    def _create_log_area() -> TextInput:
        """
        Create a text input widget to serve as the log area.

        Returns:
            TextInput: The text input widget configured as a log area.
        """
        return TextInput(
            multiline=True,
            readonly=True,
            size_hint=(1, 0.4),
            background_color=[0.9, 0.9, 0.9, 1],
            foreground_color=[0, 0, 0, 1],
        )

    def log_message(self, message: str) -> None:
        """
        Log a message to the log area asynchronously.

        Args:
            message (str): The message to log.
        """
        Clock.schedule_once(lambda dt: self._append_message(message))

    def _append_message(self, message: str) -> None:
        """
        Append a message to the log output.

        Args:
            message (str): The message to append.
        """
        self.log_output.text += f"{message}\n"

    def show_loading(self) -> None:
        """Show the loading popup."""
        self.loading_popup.open()

    def hide_loading(self) -> None:
        """Hide the loading popup."""
        self.loading_popup.dismiss()

    def create_db(self, _instance: Button) -> None:
        """Open popup to create a database."""
        popup = InputPopup(
            title="Enter New Project Name",
            hint_text="Project Name",
            callback=self._handle_create_db,
        )
        popup.open()

    def _handle_create_db(self, project_name: str) -> None:
        """
        Handle the creation of a new database.

        Args:
            project_name (str): The name of the new project/database.
        """
        if helper.valid_project_name(project_name, callback=self.log_message):
            db_path = f"{project_name}.db"
            if not db_act.db_exists(project_name, callback=self.log_message):
                self.show_loading()
                threading.Thread(
                    target=self._perform_create_db, args=(db_path,)
                ).start()
            else:
                self.log_message(f"Database '{db_path}' already exists!")

    def _perform_create_db(self, db_path: str) -> None:
        """
        Perform the database creation in a separate thread.

        Args:
            db_path (str): The file path for the new database.
        """
        try:
            db_act.create_db(db_path, callback=self.log_message)
            self.log_message(f"Database '{db_path}' created successfully!")
        except Exception as e:  # pylint: disable=broad-except
            self.log_message(f"Error: {e}")
        finally:
            self.hide_loading()

    def copy_data(self, _instance: Button) -> None:
        """Copy data between tables."""
        popup = CopyDataPopup(callback=self._handle_copy_data)
        popup.open()

    def _handle_copy_data(
        self, project_name: str, source_env: str, target_env: str
    ) -> None:
        """
        Handle the copy data action from the user input.

        Args:
            project_name (str): The name of the project/database.
            source_env (str): The source environment to copy data from.
            target_env (str): The target environment to copy data to.
        """
        if (
            helper.valid_project_name(project_name, callback=self.log_message)
            and db_act.db_exists(project_name, callback=self.log_message)
            and helper.check_target_env(source_env, callback=self.log_message)
            and helper.check_target_env(target_env, callback=self.log_message)
        ):
            self.show_loading()
            threading.Thread(
                target=self._perform_copy_data,
                args=(project_name, source_env, target_env),
            ).start()

    def _perform_copy_data(
        self, project_name: str, source_env: str, target_env: str
    ) -> None:
        """
        Perform the data copy operation in a separate thread.

        Args:
            project_name (str): The name of the project/database.
            source_env (str): The source environment.
            target_env (str): The target environment.
        """
        try:
            db_act.copy_table(
                f"{project_name}.db", source_env, target_env, callback=self.log_message
            )
            self.log_message(
                f"Data copied from {source_env} to {target_env} successfully!"
            )
        except Exception as e:  # pylint: disable=broad-except
            self.log_message(f"Error: {e}")
        finally:
            self.hide_loading()

    def pull_data(self, _instance: Button) -> None:
        """Pull data from ARVA."""
        popup = PullWorkflowPopup(callback=self._handle_pull_data)
        popup.open()

    def _handle_pull_data(
        self, project_name: str, source_env: str, token: str, article_ids: str
    ) -> None:
        """
        Handle the pull data action from the user input.

        Args:
            project_name (str): The name of the project/database.
            source_env (str): The source environment to pull data from.
            token (str): The ARVA authentication token.
            article_ids (str): Comma-separated list of article IDs.
        """
        if (
            helper.valid_project_name(project_name, callback=self.log_message)
            and db_act.db_exists(project_name, callback=self.log_message)
            and helper.check_target_env(source_env, callback=self.log_message)
        ):
            self.show_loading()
            threading.Thread(
                target=self._perform_pull_data,
                args=(project_name, source_env, token, article_ids),
            ).start()

    def _perform_pull_data(
        self, project_name: str, source_env: str, token: str, article_ids: str
    ) -> None:
        """
        Perform the data pull operation in a separate thread.

        Args:
            project_name (str): The name of the project/database.
            source_env (str): The source environment.
            token (str): The ARVA authentication token.
            article_ids (str): Comma-separated list of article IDs.
        """
        try:
            config = {
                "db": f"{project_name}.db",
                "env": source_env,
                "bearer_token": token,
                "graphql_url": helper.get_env_url(source_env),
            }
            prog.get_arva_records(config, article_ids, callback=self.log_message)
        except Exception as e:  # pylint: disable=broad-except
            self.log_message(f"Error: {e}")
        finally:
            self.hide_loading()

    def insert_data(self, _instance: Button) -> None:
        """Insert data into ARVA."""
        popup = InsertWorkflowPopup(callback=self._handle_insert_data)
        popup.open()

    def _handle_insert_data(
        self, project_name: str, target_env: str, token: str
    ) -> None:
        """
        Handle the insert data action from the user input.

        Args:
            project_name (str): The name of the project/database.
            target_env (str): The target environment to insert data into.
            token (str): The ARVA authentication token.
        """
        if (
            helper.valid_project_name(project_name, callback=self.log_message)
            and db_act.db_exists(project_name, callback=self.log_message)
            and helper.check_target_env(target_env, callback=self.log_message)
        ):
            self.show_loading()
            threading.Thread(
                target=self._perform_insert_data, args=(project_name, target_env, token)
            ).start()

    def _perform_insert_data(
        self, project_name: str, target_env: str, token: str
    ) -> None:
        """
        Perform the data insertion operation in a separate thread.

        Args:
            project_name (str): The name of the project/database.
            target_env (str): The target environment.
            token (str): The ARVA authentication token.
        """
        graphql_url = helper.get_env_url(target_env)
        if not graphql_url:
            self.log_message(
                f"Error: GraphQL URL for environment '{target_env}' not found."
            )
            self.hide_loading()
            return

        try:
            prog.process_records(
                f"{project_name}.db",
                target_env,
                token,
                graphql_url,  # Now guaranteed to be a valid string
                callback=self.log_message,
            )
            self.log_message("Data inserted into ARVA successfully!")
        except Exception as e:  # pylint: disable=broad-except
            self.log_message(f"Error: {e}")
        finally:
            self.hide_loading()


class TASAApp(App):
    """Main application class."""

    def build(self) -> MainScreen:
        """Build and return the main screen of the application."""
        return MainScreen()


if __name__ == "__main__":
    TASAApp().run()
