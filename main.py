import os
import sys

import cv2
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class FrameExtractorMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Frame Extractor")
        self.setMinimumSize(980, 720)

        self.video_path = None
        self.cap = None
        self.frame_count = 0
        self.fps = 0.0
        self.width = 0
        self.height = 0

        self.current_preview_pixmap = None
        self.clipboard = QApplication.clipboard()

        self.selected_export_folder = None

        self.setup_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def setup_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)

        # --------------------------------------------------------------
        # Top Controls
        # --------------------------------------------------------------

        file_layout = QHBoxLayout()
        file_layout.setSpacing(10)

        self.open_button = QPushButton("Open Video")
        self.open_button.clicked.connect(self.open_video)

        self.folder_button = QPushButton("Select Export Folder")
        self.folder_button.clicked.connect(self.pick_export_folder)

        self.folder_label = QLabel("Export folder: not selected")
        self.folder_label.setStyleSheet(
            "color: #555; font-size: 12px;"
        )

        button_style = """
            QPushButton {
                padding: 10px 16px;
                border-radius: 8px;
                background-color: #2e86ff;
                color: white;
                border: none;
            }

            QPushButton:hover {
                background-color: #1f6fe5;
            }

            QPushButton:disabled {
                background-color: #666;
                color: #bbb;
            }
        """

        self.open_button.setStyleSheet(button_style)
        self.folder_button.setStyleSheet(button_style)

        self.open_button.setCursor(Qt.PointingHandCursor)
        self.folder_button.setCursor(Qt.PointingHandCursor)

        file_layout.addWidget(self.open_button)
        file_layout.addWidget(self.folder_button)
        file_layout.addWidget(self.folder_label, 1)

        main_layout.addLayout(file_layout)

        # --------------------------------------------------------------
        # Video Preview Area
        # --------------------------------------------------------------

        self.image_display = QLabel()

        self.image_display.setAlignment(Qt.AlignCenter)

        self.image_display.setStyleSheet("""
            border: none;
            background: transparent;
            padding: 0px;
            margin: 0px;
        """)

        self.image_display.setMinimumSize(0, 0)

        self.preview_scroll = QScrollArea()

        self.preview_scroll.setWidgetResizable(True)

        self.preview_scroll.setAlignment(Qt.AlignCenter)

        self.preview_scroll.setFrameShape(QScrollArea.NoFrame)

        self.preview_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: black;
            }

            QScrollArea > QWidget > QWidget {
                background: black;
            }
        """)

        self.preview_scroll.setWidget(self.image_display)

        main_layout.addWidget(self.preview_scroll, 1)

        # --------------------------------------------------------------
        # Export Buttons
        # --------------------------------------------------------------

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.export_selected_button = QPushButton(
            "Export Selected Frames"
        )

        self.export_selected_button.clicked.connect(
            self.export_selected_frames
        )

        self.export_current_button = QPushButton(
            "Export Current Frame"
        )

        self.export_current_button.clicked.connect(
            self.export_current_frame
        )

        self.copy_button = QPushButton(
            "Copy Preview to Clipboard"
        )

        self.copy_button.clicked.connect(
            self.copy_preview_to_clipboard
        )

        self.export_selected_button.setEnabled(False)
        self.export_current_button.setEnabled(False)
        self.copy_button.setEnabled(False)

        for button in (
            self.export_selected_button,
            self.export_current_button,
            self.copy_button,
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setStyleSheet(button_style)

        button_layout.addStretch(1)

        button_layout.addWidget(
            self.export_selected_button
        )

        button_layout.addWidget(
            self.export_current_button
        )

        button_layout.addWidget(self.copy_button)

        button_layout.addStretch(1)

        main_layout.addLayout(button_layout)

        # --------------------------------------------------------------
        # Sliders
        # --------------------------------------------------------------

        slider_group = QGroupBox(
            "Range and Preview"
        )

        slider_layout = QVBoxLayout()

        self.start_label = QLabel(
            "Start frame: 0"
        )

        self.start_slider = QSlider(Qt.Horizontal)

        self.start_slider.setMinimum(0)
        self.start_slider.setEnabled(False)

        self.start_slider.valueChanged.connect(
            self.start_slider_changed
        )

        self.end_label = QLabel(
            "End frame: 0"
        )

        self.end_slider = QSlider(Qt.Horizontal)

        self.end_slider.setMinimum(0)
        self.end_slider.setEnabled(False)

        self.end_slider.valueChanged.connect(
            self.end_slider_changed
        )

        self.preview_index_label = QLabel(
            "Preview frame: 0"
        )

        self.preview_slider = QSlider(Qt.Horizontal)

        self.preview_slider.setMinimum(0)
        self.preview_slider.setEnabled(False)

        self.preview_slider.valueChanged.connect(
            self.preview_slider_changed
        )

        self.range_label = QLabel(
            "Selected range: 0 - 0 (0 frames)"
        )

        self.range_label.setStyleSheet("""
            color: #ffffff;
            font-weight: bold;
        """)

        slider_layout.addWidget(self.start_label)
        slider_layout.addWidget(self.start_slider)

        slider_layout.addWidget(self.end_label)
        slider_layout.addWidget(self.end_slider)

        slider_layout.addWidget(
            self.preview_index_label
        )

        slider_layout.addWidget(
            self.preview_slider
        )

        slider_layout.addWidget(
            self.range_label
        )

        slider_group.setLayout(slider_layout)

        main_layout.addWidget(slider_group)

        # --------------------------------------------------------------
        # Status
        # --------------------------------------------------------------

        self.status_label = QLabel(
            "Open a video to begin."
        )

        self.status_label.setWordWrap(True)

        main_layout.addWidget(self.status_label)

    # ------------------------------------------------------------------
    # Window Resize
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.current_preview_pixmap:
            self.update_preview()

    # ------------------------------------------------------------------
    # Video Loading
    # ------------------------------------------------------------------

    def open_video(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            (
                "Video Files (*.mp4 *.mov *.avi *.mkv);;"
                "MP4 Files (*.mp4);;"
                "All Files (*)"
            ),
        )

        if not filename:
            return

        self.load_video(filename)

    def load_video(self, path):
        if self.cap:
            self.cap.release()
            self.cap = None

        cap = cv2.VideoCapture(path)

        if not cap.isOpened():
            QMessageBox.critical(
                self,
                "Error",
                "Unable to open the selected video.",
            )
            return

        frame_count = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        if frame_count <= 0:
            cap.release()

            QMessageBox.critical(
                self,
                "Error",
                "Unable to determine frame count.",
            )

            return

        self.video_path = path
        self.cap = cap
        self.frame_count = frame_count

        self.fps = (
            cap.get(cv2.CAP_PROP_FPS) or 0.0
        )

        self.width = int(
            cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        )

        self.height = int(
            cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )

        max_index = self.frame_count - 1

        self.start_slider.setMaximum(max_index)
        self.end_slider.setMaximum(max_index)
        self.preview_slider.setMaximum(max_index)

        self.start_slider.setEnabled(True)
        self.end_slider.setEnabled(True)
        self.preview_slider.setEnabled(True)

        self.start_slider.setValue(0)
        self.end_slider.setValue(max_index)
        self.preview_slider.setValue(0)

        self.export_selected_button.setEnabled(True)

        self.export_current_button.setEnabled(True)

        self.copy_button.setEnabled(True)

        self.update_slider_labels()
        self.update_preview()

        self.status_label.setText(
            "Video loaded. Use the preview slider "
            "to see individual frames."
        )

    # ------------------------------------------------------------------
    # Sliders
    # ------------------------------------------------------------------

    def update_slider_labels(self):
        start_value = self.start_slider.value()
        end_value = self.end_slider.value()

        self.start_label.setText(
            f"Start frame: {start_value}"
        )

        self.end_label.setText(
            f"End frame: {end_value}"
        )

        self.preview_index_label.setText(
            f"Preview frame: "
            f"{self.preview_slider.value()}"
        )

        self.range_label.setText(
            f"Selected range: "
            f"{start_value} - {end_value} "
            f"({end_value - start_value + 1} frame(s))"
        )

    def start_slider_changed(self, value):
        end_val = self.end_slider.value()

        if value > end_val:
            self.end_slider.setValue(value)

        self.end_slider.setMinimum(value)

        self.preview_slider.blockSignals(True)

        self.preview_slider.setValue(value)

        self.preview_slider.blockSignals(False)

        self.update_slider_labels()
        self.update_preview()

    def end_slider_changed(self, value):
        start_val = self.start_slider.value()

        if value < start_val:
            self.start_slider.setValue(value)

        self.start_slider.setMaximum(value)

        if self.preview_slider.value() > value:
            self.preview_slider.blockSignals(True)

            self.preview_slider.setValue(value)

            self.preview_slider.blockSignals(False)

        self.update_slider_labels()
        self.update_preview()

    def preview_slider_changed(self):
        preview_val = self.preview_slider.value()

        if preview_val < self.start_slider.value():
            self.start_slider.blockSignals(True)

            self.start_slider.setValue(preview_val)

            self.start_slider.blockSignals(False)

        if preview_val > self.end_slider.value():
            self.end_slider.blockSignals(True)

            self.end_slider.setValue(preview_val)

            self.end_slider.blockSignals(False)

        self.update_slider_labels()
        self.update_preview()

    # ------------------------------------------------------------------
    # Export Folder
    # ------------------------------------------------------------------

    def pick_export_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Export Folder",
            self.selected_export_folder or "",
        )

        if not folder:
            return

        self.selected_export_folder = folder

        self.folder_label.setText(
            f"Export folder: {folder}"
        )

        self.status_label.setText(
            f"Export folder set to {folder}."
        )

    # ------------------------------------------------------------------
    # Frame Handling
    # ------------------------------------------------------------------

    def read_frame(self, frame_index):
        if not self.cap:
            return None

        self.cap.set(
            cv2.CAP_PROP_POS_FRAMES,
            frame_index,
        )

        success, frame = self.cap.read()

        return frame if success else None

    def frame_to_pixmap(self, frame):
        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        height, width, channels = rgb.shape

        bytes_per_line = channels * width

        qimage = QImage(
            rgb.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888,
        )

        return QPixmap.fromImage(qimage)

    def update_preview(self):
        frame_index = self.preview_slider.value()

        frame = self.read_frame(frame_index)

        if frame is None:
            self.status_label.setText(
                "Unable to load preview frame."
            )
            return

        pixmap = self.frame_to_pixmap(frame)

        self.current_preview_pixmap = pixmap

        viewport_size = (
            self.preview_scroll.viewport().size()
        )

        scaled_pixmap = pixmap.scaled(
            viewport_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image_display.setPixmap(
            scaled_pixmap
        )

        self.image_display.resize(
            scaled_pixmap.size()
        )

        self.status_label.setText(
            f"Previewing frame {frame_index}."
        )

    # ------------------------------------------------------------------
    # Export Selected Frames
    # ------------------------------------------------------------------

    def export_selected_frames(self):
        if not self.cap:
            QMessageBox.warning(
                self,
                "Warning",
                "No video loaded.",
            )
            return

        start = self.start_slider.value()
        end = self.end_slider.value()

        if start > end:
            QMessageBox.warning(
                self,
                "Warning",
                "Start frame cannot be greater than end frame.",
            )
            return

        export_folder = self.selected_export_folder

        if not export_folder:
            export_folder = QFileDialog.getExistingDirectory(
                self,
                "Select Export Folder",
                "",
            )

            if not export_folder:
                return

            self.selected_export_folder = export_folder

            self.folder_label.setText(
                f"Export folder: {export_folder}"
            )

        total = end - start + 1

        progress = QProgressDialog(
            "Exporting frames...",
            "Cancel",
            0,
            total,
            self,
        )

        progress.setWindowModality(
            Qt.WindowModal
        )

        progress.setMinimumDuration(0)

        exported = 0

        for index, frame_number in enumerate(
            range(start, end + 1),
            start=1,
        ):
            if progress.wasCanceled():
                break

            frame = self.read_frame(
                frame_number
            )

            if frame is None:
                continue

            filename = (
                f"frame_{frame_number:06d}.jpg"
            )

            output_path = os.path.join(
                export_folder,
                filename,
            )

            cv2.imwrite(
                output_path,
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 100],
            )

            exported += 1

            progress.setValue(index)

        progress.close()

        if exported == 0:
            QMessageBox.information(
                self,
                "Export Finished",
                "No frames were exported.",
            )

            self.status_label.setText(
                "Export finished with no frames saved."
            )

        else:
            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {exported} frame(s) "
                f"to:\n{export_folder}",
            )

            self.status_label.setText(
                f"Export complete: "
                f"{exported} frame(s) "
                f"saved to {export_folder}"
            )

    # ------------------------------------------------------------------
    # Export Current Frame
    # ------------------------------------------------------------------

    def export_current_frame(self):
        if not self.cap:
            QMessageBox.warning(
                self,
                "Warning",
                "No video loaded.",
            )
            return

        frame_index = (
            self.preview_slider.value()
        )

        frame = self.read_frame(frame_index)

        if frame is None:
            QMessageBox.warning(
                self,
                "Warning",
                "Unable to capture "
                "the current frame.",
            )

            return

        export_folder = self.selected_export_folder

        if not export_folder:
            export_folder = QFileDialog.getExistingDirectory(
                self,
                "Select Export Folder",
                "",
            )

            if not export_folder:
                return

            self.selected_export_folder = export_folder

            self.folder_label.setText(
                f"Export folder: {export_folder}"
            )

        filename = (
            f"frame_{frame_index:06d}.jpg"
        )

        output_path = os.path.join(
            export_folder,
            filename,
        )

        cv2.imwrite(
            output_path,
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 100],
        )

        QMessageBox.information(
            self,
            "Export Current Frame",
            f"Current frame {frame_index} "
            f"exported to:\n{output_path}",
        )

        self.status_label.setText(
            f"Current frame {frame_index} "
            f"exported to {export_folder}."
        )

    # ------------------------------------------------------------------
    # Clipboard
    # ------------------------------------------------------------------

    def copy_preview_to_clipboard(self):
        if not self.current_preview_pixmap:
            QMessageBox.warning(
                self,
                "Warning",
                "No preview image available.",
            )

            return

        self.clipboard.setPixmap(
            self.current_preview_pixmap
        )

        QMessageBox.information(
            self,
            "Copied to Clipboard",
            "The current preview image "
            "has been copied to the clipboard.",
        )

        self.status_label.setText(
            "Current preview copied to clipboard."
        )


def main():
    app = QApplication(sys.argv)

    window = FrameExtractorMainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()