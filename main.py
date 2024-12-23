import sys
import numpy as np
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox,
                           QPushButton, QListWidget, QGroupBox, QCheckBox,
                           QGridLayout, QFrame, QSlider)
from PyQt5.QtCore import Qt, QLocale
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from phased_array import PhasedArrayUnit, MultiArraySystem
from scipy import constants
from scenario_manager import ScenarioManager


class ScientificSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        locale = QLocale(QLocale.English, QLocale.UnitedStates)
        self.setLocale(locale)
        self.setDecimals(3)
        self.setMinimumWidth(100)

class BeamformingSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Beamforming Simulator - Scientific Version")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Initialize the multi-array system
        self.system = MultiArraySystem()
        
        # Set style
        self.setStyle()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel, 1)
        
        # Create visualization panel
        viz_panel = self.create_visualization_panel()
        layout.addWidget(viz_panel, 3)
        
        # Initialize plots
        self.update_plots()
        self.steering_slider.setMinimum(-180)
        self.steering_slider.setMaximum(180)
        self.steering_slider.setValue(0)
        # Add scenario manager
        self.scenario_manager = ScenarioManager(self)

        # Add scenario selection to control panel
        scenario_group = QGroupBox("Scenario Selection")
        scenario_layout = QVBoxLayout()

        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(self.scenario_manager.list_scenarios())
        scenario_layout.addWidget(self.scenario_combo)

        load_scenario_button = QPushButton("Load Scenario")
        load_scenario_button.clicked.connect(self.load_selected_scenario)
        scenario_layout.addWidget(load_scenario_button)

        scenario_group.setLayout(scenario_layout)

        # Add to control panel layout
        control_panel.layout().addWidget(scenario_group)
        # Add save scenario button
        save_scenario_button = QPushButton("Save Current Scenario")
        save_scenario_button.clicked.connect(self.scenario_manager.save_current_scenario)
        scenario_layout.addWidget(save_scenario_button)

        # Connect array selection change
        self.array_list.currentRowChanged.connect(self.array_list_selection_changed)

    def modify_simulator_init(self):
        # Add scenario manager to simulator
        self.scenario_manager = ScenarioManager(self)

        # Add scenario selection dropdown or button
        scenario_group = QGroupBox("Scenario Selection")
        scenario_layout = QVBoxLayout()

        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(self.scenario_manager.list_scenarios())
        scenario_layout.addWidget(self.scenario_combo)

        load_scenario_button = QPushButton("Load Scenario")
        load_scenario_button.clicked.connect(self.load_selected_scenario)
        scenario_layout.addWidget(load_scenario_button)

        scenario_group.setLayout(scenario_layout)

        # Add to existing control panel layout
        self.layout().addWidget(scenario_group)

    def load_selected_scenario(self):
        scenario_name = self.scenario_combo.currentText()
        self.scenario_manager.load_scenario(scenario_name)

    def setStyle(self):
        # Set scientific style for matplotlib
        plt.style.use('bmh')  # Using a built-in style that's more scientific

    def create_control_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Array creation controls
        array_group = QGroupBox("Array Configuration Parameters")
        array_layout = QGridLayout()

        # Number of elements
        array_layout.addWidget(QLabel("Number of Elements (N):"), 0, 0)
        self.num_elements_slider = QSlider(Qt.Horizontal)
        self.num_elements_slider.setRange(2, 32)
        self.num_elements_slider.setValue(8)
        self.num_elements_slider.setTickPosition(QSlider.TicksBelow)
        self.num_elements_slider.setTickInterval(2)
        self.num_elements_label = QLabel("8")
        array_layout.addWidget(self.num_elements_slider, 0, 1)
        array_layout.addWidget(self.num_elements_label, 0, 2)

        # Element spacing
        array_layout.addWidget(QLabel("Element Spacing (λ):"), 1, 0)
        self.spacing_slider = QSlider(Qt.Horizontal)
        self.spacing_slider.setRange(10, 200)  # 0.1 to 2.0 with 100x scale
        self.spacing_slider.setValue(50)  # 0.5 default
        self.spacing_slider.setTickPosition(QSlider.TicksBelow)
        self.spacing_slider.setTickInterval(10)
        self.spacing_label = QLabel("0.5")
        array_layout.addWidget(self.spacing_slider, 1, 1)
        array_layout.addWidget(self.spacing_label, 1, 2)

        # Frequency
        array_layout.addWidget(QLabel("Frequency (GHz):"), 2, 0)
        self.freq_slider = QSlider(Qt.Horizontal)
        self.freq_slider.setRange(1, 1000)  # 0.1 to 100.0 with 10x scale
        self.freq_slider.setValue(10)  # 1.0 default
        self.freq_slider.setTickPosition(QSlider.TicksBelow)
        self.freq_slider.setTickInterval(100)
        self.freq_label = QLabel("1.0")
        array_layout.addWidget(self.freq_slider, 2, 1)
        array_layout.addWidget(self.freq_label, 2, 2)

        # Position controls
        array_layout.addWidget(QLabel("Position (x, y) [m]:"), 3, 0)
        pos_layout = QHBoxLayout()
        
        self.pos_x_slider = QSlider(Qt.Horizontal)
        self.pos_x_slider.setRange(-500, 500)  # -50 to 50 with 10x scale
        self.pos_x_slider.setValue(0)
        self.pos_x_label = QLabel("0.0")
        
        self.pos_y_slider = QSlider(Qt.Horizontal)
        self.pos_y_slider.setRange(-500, 500)  # -50 to 50 with 10x scale
        self.pos_y_slider.setValue(0)
        self.pos_y_label = QLabel("0.0")
        
        pos_layout.addWidget(self.pos_x_slider)
        pos_layout.addWidget(self.pos_x_label)
        pos_layout.addWidget(self.pos_y_slider)
        pos_layout.addWidget(self.pos_y_label)
        array_layout.addLayout(pos_layout, 3, 1, 1, 2)

        # Connect slider signals
        self.num_elements_slider.valueChanged.connect(self.update_num_elements_label)
        self.spacing_slider.valueChanged.connect(self.update_spacing_label)
        self.freq_slider.valueChanged.connect(self.update_freq_label)
        self.pos_x_slider.valueChanged.connect(self.update_pos_x_label)
        self.pos_y_slider.valueChanged.connect(self.update_pos_y_label)

        # Curved array options
        curved_layout = QHBoxLayout()
        self.curved_check = QCheckBox("Enable Curved Array")
        curved_layout.addWidget(self.curved_check)
        self.radius_spin = ScientificSpinBox()
        self.radius_spin.setRange(1, 100)
        self.radius_spin.setValue(10)
        self.radius_spin.setEnabled(False)
        curved_layout.addWidget(QLabel("Radius [m]:"))
        curved_layout.addWidget(self.radius_spin)
        array_layout.addLayout(curved_layout, 4, 0, 1, 2)

        self.curved_check.stateChanged.connect(lambda state: self.radius_spin.setEnabled(state == Qt.Checked))

        array_group.setLayout(array_layout)
        layout.addWidget(array_group)

        # Add a separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Array Management Group
        management_group = QGroupBox("Array Management")
        management_layout = QVBoxLayout()

        # Add array button
        add_button = QPushButton("Add New Array Unit")
        add_button.setMinimumHeight(30)
        management_layout.addWidget(add_button)
        add_button.clicked.connect(self.add_array)

        # Array list
        management_layout.addWidget(QLabel("Deployed Array Units:"))
        self.array_list = QListWidget()
        self.array_list.setMinimumHeight(100)
        management_layout.addWidget(self.array_list)

        # Remove array button
        remove_button = QPushButton("Remove Selected Array")
        remove_button.setMinimumHeight(30)
        management_layout.addWidget(remove_button)
        remove_button.clicked.connect(self.remove_array)

        management_group.setLayout(management_layout)
        layout.addWidget(management_group)

        # Beam steering controls
        steering_group = QGroupBox("Beam Steering Control")
        steering_layout = QGridLayout()

        # Update slider and spinbox configuration
        self.steering_slider = QSlider(Qt.Horizontal)
        self.steering_slider.setRange(0, 360)
        self.steering_slider.setValue(0)
        self.steering_slider.setTickInterval(45)

        steering_layout.addWidget(QLabel("Steering Angle (°):"), 0, 0)
        self.steering_angle_spin = ScientificSpinBox()
        self.steering_angle_spin.setRange(0, 360)
        self.steering_angle_spin.setValue(0)

        steering_layout.addWidget(self.steering_angle_spin, 0, 1)
        steering_layout.addWidget(self.steering_slider, 2, 0, 1, 2)

        # Remove the direction label
        # self.direction_label = QLabel("Current Direction: 0° (North)")
        # This line is removed completely

        # Connect slider and spinbox
        self.steering_angle_spin.setRange(-180, 180)
        self.steering_angle_spin.setValue(90)
        self.steering_slider.valueChanged.connect(self.update_steering_from_slider)
        self.steering_angle_spin.valueChanged.connect(self.update_steering_from_spinbox)
        steering_group.setLayout(steering_layout)
        layout.addWidget(steering_group)

        # Add phase information display
        phase_info_group = QGroupBox("Phase Information")
        phase_layout = QVBoxLayout()
        self.phase_info_label = QLabel()
        self.phase_info_label.setWordWrap(True)
        phase_layout.addWidget(self.phase_info_label)
        phase_info_group.setLayout(phase_layout)
        layout.addWidget(phase_info_group)

        # Connect slider signals for both label updates and real-time plot updates
        self.num_elements_slider.valueChanged.connect(self.on_parameter_changed)
        self.spacing_slider.valueChanged.connect(self.on_parameter_changed)
        self.freq_slider.valueChanged.connect(self.on_parameter_changed)
        self.pos_x_slider.valueChanged.connect(self.on_parameter_changed)
        self.pos_y_slider.valueChanged.connect(self.on_parameter_changed)
        self.curved_check.stateChanged.connect(self.on_parameter_changed)
        self.radius_spin.valueChanged.connect(self.on_parameter_changed)

        return panel

    # Add these new methods
    def on_parameter_changed(self, _):
        """Handle any parameter change by updating the selected array"""
        current_row = self.array_list.currentRow()
        if current_row >= 0:  # Only update if an array is selected
            array = self.system.arrays[current_row]
            self.update_array_parameters(array)
            self.update_plots()

    def update_array_parameters(self, array):
        """Update the parameters of the selected array"""
        array.num_elements = self.num_elements_slider.value()
        array.element_spacing = self.spacing_slider.value() / 100.0
        array.frequency = self.freq_slider.value() / 10.0 * 1e9
        array.position = np.array([self.pos_x_slider.value() / 10.0, 
                                 self.pos_y_slider.value() / 10.0])
        array.is_curved = self.curved_check.isChecked()
        array.curvature_radius = (self.radius_spin.value() 
                                if self.curved_check.isChecked() else None)
        array.wavelength = constants.c / array.frequency
        array.wave_number = 2 * np.pi / array.wavelength
        array.update_element_positions()
        array.set_beam_direction(np.deg2rad(self.steering_angle_spin.value()))

    def array_list_selection_changed(self):
        """Update control values when different array is selected"""
        current_row = self.array_list.currentRow()
        if current_row >= 0:
            array = self.system.arrays[current_row]
            # Update sliders without triggering updates
            self.num_elements_slider.blockSignals(True)
            self.spacing_slider.blockSignals(True)
            self.freq_slider.blockSignals(True)
            self.pos_x_slider.blockSignals(True)
            self.pos_y_slider.blockSignals(True)
            
            self.num_elements_slider.setValue(array.num_elements)
            self.spacing_slider.setValue(int(array.element_spacing * 100))
            self.freq_slider.setValue(int(array.frequency / 1e8))
            self.pos_x_slider.setValue(int(array.position[0] * 10))
            self.pos_y_slider.setValue(int(array.position[1] * 10))
            self.curved_check.setChecked(array.is_curved)
            if array.is_curved:
                self.radius_spin.setValue(array.curvature_radius)
            
            self.num_elements_slider.blockSignals(False)
            self.spacing_slider.blockSignals(False)
            self.freq_slider.blockSignals(False)
            self.pos_x_slider.blockSignals(False)
            self.pos_y_slider.blockSignals(False)

    def update_num_elements_label(self, value):
        self.num_elements_label.setText(str(value))

    def update_spacing_label(self, value):
        spacing = value / 100.0
        self.spacing_label.setText(f"{spacing:.2f}")

    def update_freq_label(self, value):
        freq = value / 10.0
        self.freq_label.setText(f"{freq:.1f}")

    def update_pos_x_label(self, value):
        pos = value / 10.0
        self.pos_x_label.setText(f"{pos:.1f}")

    def update_pos_y_label(self, value):
        pos = value / 10.0
        self.pos_y_label.setText(f"{pos:.1f}")

    def create_visualization_panel(self):
        panel = QWidget()
        main_layout = QVBoxLayout(panel)

        # Create top row with radiation pattern and interference map side by side
        top_row = QHBoxLayout()

        # Left side: Radiation pattern (polar plot)
        pattern_container = QWidget()
        pattern_layout = QVBoxLayout(pattern_container)
        self.pattern_fig = Figure(figsize=(6, 6))
        self.pattern_canvas = FigureCanvas(self.pattern_fig)
        pattern_layout.addWidget(self.pattern_canvas)
        top_row.addWidget(pattern_container)

        # Right side: Interference map
        interference_container = QWidget()
        interference_layout = QVBoxLayout(interference_container)
        self.interference_fig = Figure(figsize=(6, 6))
        self.interference_canvas = FigureCanvas(self.interference_fig)
        interference_layout.addWidget(self.interference_canvas)
        top_row.addWidget(interference_container)

        main_layout.addLayout(top_row)

        # Bottom: Array geometry
        geometry_container = QWidget()
        geometry_layout = QVBoxLayout(geometry_container)
        self.array_fig = Figure(figsize=(12, 4))
        self.array_canvas = FigureCanvas(self.array_fig)
        geometry_layout.addWidget(self.array_canvas)
        main_layout.addWidget(geometry_container)

        return panel

    def add_array(self):
        array = PhasedArrayUnit(
            position=(self.pos_x_slider.value() / 10.0, self.pos_y_slider.value() / 10.0),
            num_elements=self.num_elements_slider.value(),
            element_spacing=self.spacing_slider.value() / 100.0,
            frequency=self.freq_slider.value() / 10.0 * 1e9,
            is_curved=self.curved_check.isChecked(),
            curvature_radius=self.radius_spin.value() if self.curved_check.isChecked() else None
        )

        self.system.add_array(array)
        self.array_list.addItem(f"Array {len(self.system.arrays)}")
        self.update_plots()

    def remove_array(self):
        current_row = self.array_list.currentRow()
        if current_row >= 0:
            self.system.remove_array(current_row)
            self.array_list.takeItem(current_row)
            self.update_plots()

    def update_steering_from_slider(self, value):
        # Update spin box with wrapped value
        if value > 180:
            adjusted_value = value - 360  # Wrap around
        elif value < -180:
            adjusted_value = value + 360  # Wrap around
        else:
            adjusted_value = value

        self.steering_angle_spin.setValue(adjusted_value)
        self.update_beam_steering()

    def update_steering_from_spinbox(self, value):
        # Wrap the value to stay within -180 to 180
        if value > 180:
            adjusted_value = value - 360  # Wrap around
        elif value < -180:
            adjusted_value = value + 360  # Wrap around
        else:
            adjusted_value = value

        self.steering_slider.setValue(int(adjusted_value))
        self.update_beam_steering()

    def update_beam_steering(self):
        angle_deg = self.steering_angle_spin.value()
        # Convert to radians
        angle_rad = np.deg2rad(angle_deg)

        for array in self.system.arrays:
            array.set_beam_direction(angle_rad)

        # Update plots less frequently to reduce computational load
        self.update_plots()

    def get_direction_text(self, angle):
        """Convert angle to text representation
        Angle is in degrees, 0 at North, going clockwise"""
        angle = angle % 360
        if 337.5 <= angle or angle < 22.5:
            return "North"
        elif 22.5 <= angle < 67.5:
            return "Northeast"
        elif 67.5 <= angle < 112.5:
            return "East"
        elif 112.5 <= angle < 157.5:
            return "Southeast"
        elif 157.5 <= angle < 202.5:
            return "South"
        elif 202.5 <= angle < 247.5:
            return "Southwest"
        elif 247.5 <= angle < 292.5:
            return "West"
        else:  # 292.5 <= angle < 337.5
            return "Northwest"

    def update_plots(self):
        # Clear figures
        self.pattern_fig.clear()
        self.interference_fig.clear()
        self.array_fig.clear()

        # Plot radiation pattern
        ax_pattern = self.pattern_fig.add_subplot(111, projection='polar')
        theta = np.linspace(0, 2 * np.pi, 361)
        pattern = self.system.calculate_total_pattern(theta)

        ax_pattern.set_title("Radiation Pattern", pad=20, fontsize=12)
        ax_pattern.grid(True, linestyle='--', alpha=0.7)

        # Set 0 at positive x-axis (East), counterclockwise
        ax_pattern.set_theta_zero_location('E')  # 0 degrees at East
        ax_pattern.set_theta_direction(1)  # Counterclockwise

        # Remove direction labels
        ax_pattern.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315],
                                  ['0', '45', '90', '135', '180', '225', '270', '315'])

        # Plot pattern and beam direction
        ax_pattern.plot(theta, pattern, 'b-', linewidth=2)

        # Add beam direction indicator
        angle_rad = np.deg2rad(self.steering_angle_spin.value())
        max_radius = np.max(pattern)
        ax_pattern.plot([angle_rad, angle_rad], [0, max_radius], 'r--', linewidth=2, label='Steering Direction')
        # Plot interference map
        ax_interference = self.interference_fig.add_subplot(111)

        # Increase the range and resolution
        # Interference map calculation
        wavelength = constants.c / (self.system.arrays[0].frequency if self.system.arrays else 1e9)
        x_range = (-10 * wavelength, 10 * wavelength, 400)
        y_range = (-10 * wavelength, 10 * wavelength, 400)

        X, Y, field = self.system.calculate_total_interference_map(x_range, y_range)

        # Rotate the interference map to match radiation pattern
        intensity = np.abs(field) ** 2
        rotated_intensity = np.rot90(intensity, k=2)  # Rotate 90 degrees

        log_intensity = np.log1p(rotated_intensity)
        if np.max(log_intensity) > 0:
            log_intensity = log_intensity / np.max(log_intensity)
        else:
            log_intensity = np.zeros_like(log_intensity)
        log_intensity = log_intensity / np.max(log_intensity)

        im = ax_interference.imshow(log_intensity,
                                    extent=[x_range[0], x_range[1], y_range[0], y_range[1]],
                                    origin='lower',
                                    cmap='viridis',
                                    aspect='equal')

        ax_interference.set_title("Interference Pattern\nBrighter areas: Constructive Interference", pad=20,
                                  fontsize=12)
        ax_interference.set_xlabel("X Position (m)", fontsize=10)
        ax_interference.set_ylabel("Y Position (m)", fontsize=10)

        # Add a colorbar with log-scaled labels
        cbar = self.interference_fig.colorbar(im, ax=ax_interference, label="Log Normalized Intensity")
        # Plot array geometry
        ax_array = self.array_fig.add_subplot(111)
        for i, array in enumerate(self.system.arrays):
            positions = array.element_positions
            ax_array.scatter(positions[:, 0], positions[:, 1], marker='o',
                           label=f'Array {i+1}', s=50)

        ax_array.set_title("Array Geometry", pad=20, fontsize=12)
        ax_array.set_xlabel("X Position (m)", fontsize=10)
        ax_array.set_ylabel("Y Position (m)", fontsize=10)
        ax_array.grid(True, linestyle='--', alpha=0.7)
        ax_array.set_aspect('equal')
        if self.system.arrays:
            ax_array.legend()

        # Update all canvases
        self.pattern_canvas.draw()
        self.interference_canvas.draw()
        self.array_canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BeamformingSimulator()
    window.show()
    sys.exit(app.exec_())
