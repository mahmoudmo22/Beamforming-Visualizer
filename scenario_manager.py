import json
import os
from PyQt5.QtWidgets import (QInputDialog, QMessageBox)

class ScenarioManager:
    def __init__(self, simulator):
        self.simulator = simulator
        self.scenarios_dir = "scenarios"

        # Ensure scenarios directory exists
        os.makedirs(self.scenarios_dir, exist_ok=True)

        # Predefined scenarios
        self.default_scenarios = {
            "5G_urban_small_cell": {
                "num_elements": 16,
                "element_spacing": 0.4,
                "frequency": 28.0,  # 28 GHz typical for 5G mmWave
                "position": (0, 0),
                "curved_array": False
            },
            "medical_ultrasound_imaging": {
                "num_elements": 128,
                "element_spacing": 0.25,
                "frequency": 7.5,  # 7.5 MHz typical for medical ultrasound
                "position": (0, 0),
                "curved_array": True,
                "curvature_radius": 15
            },
            "tumor_ablation_adaptive": {
                "num_elements": 64,
                "element_spacing": 0.5,
                "frequency": 2.45,  # 2.45 GHz typical for ablation systems
                "position": (0, 0),
                "curved_array": True,
                "curvature_radius": 10
            }
        }

        self.create_scenario_files()

    def create_scenario_files(self):
        """Create JSON files for predefined scenarios"""
        for name, config in self.default_scenarios.items():
            filepath = os.path.join(self.scenarios_dir, f"{name}.json")
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=4)

    def save_current_scenario(self):
        """Save current system configuration as a new scenario"""
        # Collect current parameters
        scenario_config = {
            "num_elements": self.simulator.num_elements_spin.value(),
            "element_spacing": self.simulator.spacing_spin.value(),
            "frequency": self.simulator.freq_spin.value(),
            "position": (
                self.simulator.pos_x_spin.value(),
                self.simulator.pos_y_spin.value()
            ),
            "curved_array": self.simulator.curved_check.isChecked(),
            "curvature_radius": (self.simulator.radius_spin.value()
                                 if self.simulator.curved_check.isChecked()
                                 else None)
        }

        # Prompt for scenario name
        name, ok = QInputDialog.getText(
            self.simulator,
            "Save Scenario",
            "Enter scenario name:"
        )

        if ok and name:
            # Sanitize filename
            safe_name = "".join(x for x in name if x.isalnum() or x in "_ ").rstrip()

            # Create filepath
            filepath = os.path.join(self.scenarios_dir, f"{safe_name}.json")

            try:
                # Save scenario
                with open(filepath, 'w') as f:
                    json.dump(scenario_config, f, indent=4)

                # Update scenario list in combo box
                self.simulator.scenario_combo.addItem(safe_name)

                QMessageBox.information(
                    self.simulator,
                    "Scenario Saved",
                    f"Scenario '{safe_name}' saved successfully!"
                )

            except Exception as e:
                QMessageBox.warning(
                    self.simulator,
                    "Save Error",
                    f"Could not save scenario: {str(e)}"
                )

    def load_scenario(self, scenario_name: str):
        """Load a scenario from file and configure simulator with correct array indexing"""
        filepath = os.path.join(self.scenarios_dir, f"{scenario_name}.json")

        try:
            with open(filepath, 'r') as f:
                scenario_config = json.load(f)

            # Clear existing arrays
            while self.simulator.system.arrays:
                self.simulator.system.remove_array(0)

            # Reset array list widget
            self.simulator.array_list.clear()

            # Configure UI elements
            self.simulator.num_elements_spin.setValue(scenario_config.get('num_elements', 8))
            self.simulator.spacing_spin.setValue(scenario_config.get('element_spacing', 0.5))
            self.simulator.freq_spin.setValue(scenario_config.get('frequency', 1.0))
            self.simulator.pos_x_spin.setValue(scenario_config.get('position', (0, 0))[0])
            self.simulator.pos_y_spin.setValue(scenario_config.get('position', (0, 0))[1])

            # Curved array configuration
            self.simulator.curved_check.setChecked(scenario_config.get('curved_array', False))
            if scenario_config.get('curved_array', False):
                self.simulator.radius_spin.setValue(scenario_config.get('curvature_radius', 10))
                self.simulator.radius_spin.setEnabled(True)

            # Add the configured array
            self.simulator.add_array()

            # Update array list to show correct indexing
            self.simulator.array_list.clear()
            for i in range(len(self.simulator.system.arrays)):
                self.simulator.array_list.addItem(f"Array {i + 1}")

            # Update plots
            self.simulator.update_plots()

        except FileNotFoundError:
            print(f"Scenario {scenario_name} not found.")
        except json.JSONDecodeError:
            print(f"Error decoding scenario {scenario_name}.")

    def list_scenarios(self):
        """List available scenario names"""
        return list(self.default_scenarios.keys())


