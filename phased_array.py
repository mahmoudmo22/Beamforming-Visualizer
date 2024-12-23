import numpy as np
from scipy import constants

class PhasedArrayUnit:
    def __init__(self, position=(0, 0), num_elements=8, element_spacing=0.5, frequency=1e9, is_curved=False, curvature_radius=None):
        self.position = np.array(position)
        self.num_elements = num_elements
        self.element_spacing = element_spacing  # in wavelengths
        self.frequency = frequency
        self.is_curved = is_curved
        self.curvature_radius = curvature_radius
        self.wavelength = constants.c / frequency
        self.wave_number = 2 * np.pi / self.wavelength
        self.phase_shifts = np.zeros(num_elements)
        self.current_steering_angle = 0
        
        # Calculate element positions
        self.update_element_positions()
    
    def update_element_positions(self):
        if not self.is_curved:
            # Linear array
            x = np.arange(self.num_elements) * self.element_spacing * self.wavelength
            y = np.zeros_like(x)
        else:
            # Curved array
            theta = np.linspace(-np.pi/4, np.pi/4, self.num_elements)
            x = self.curvature_radius * np.sin(theta)
            y = self.curvature_radius * (1 - np.cos(theta))
        
        self.element_positions = np.column_stack((x, y)) + self.position

    def calculate_progressive_phase_shift(self, theta_desired):
        """
        Calculate progressive phase shift
        theta_desired is in standard mathematical angle (counterclockwise from x-axis)
        """
        # Ensure consistent coordinate system
        return -self.wave_number * self.element_spacing * self.wavelength * np.sin(theta_desired)

    def set_beam_direction(self, theta):
        """
        Set beam direction with proper handling of angles.
        Args:
            theta: Beam steering angle in radians
        """
        # Normalize angle to [-π, π] for proper calculation
        theta = np.arctan2(np.sin(theta), np.cos(theta))
        standard_theta = np.pi / 2 - theta

        self.current_steering_angle = theta
        self.phase_shifts = np.arange(self.num_elements) * self.calculate_progressive_phase_shift(standard_theta)

    def calculate_array_factor(self, theta):
        """Calculate array factor for given angles
        
        Args:
            theta: Array of angles to calculate pattern for (in radians)
            
        Returns:
            numpy.ndarray: Normalized array factor magnitude
        """
        array_factor = np.zeros_like(theta, dtype=complex)
        
        for n in range(self.num_elements):
            pos = self.element_positions[n]
            # Phase due to geometry and steering
            phase = (self.wave_number * (pos[0] * np.cos(theta) + pos[1] * np.sin(theta)) + 
                    self.phase_shifts[n])
            array_factor += np.exp(1j * phase)
            
        return np.abs(array_factor) / self.num_elements

    def calculate_element_phases(self, theta_desired):
        """Calculate the phase shift for each element

        Args:
            theta_desired: Desired steering angle in radians

        Returns:
            numpy.ndarray: Array of phase shifts for each element
        """
        beta = self.calculate_progressive_phase_shift(theta_desired)
        n = np.arange(self.num_elements)
        return n * beta

    def calculate_interference_map(self, x_range, y_range):
        x = np.linspace(x_range[0], x_range[1], x_range[2])
        y = np.linspace(y_range[0], y_range[1], y_range[2])
        X, Y = np.meshgrid(x, y)

        field = np.zeros_like(X, dtype=complex)

        for n in range(self.num_elements):
            pos = self.element_positions[n]
            # Use consistent coordinate system calculations
            R = np.sqrt((X - pos[0]) ** 2 + (Y - pos[1]) ** 2)
            phase = self.wave_number * R + self.phase_shifts[n]
            field += np.exp(-1j * phase) / np.sqrt(R)

        return X, Y, field
    
    def get_steering_info(self):
        """Get current steering parameters for display
        
        Returns:
            dict: Dictionary containing steering parameters
        """
        return {
            'steering_angle': np.rad2deg(self.current_steering_angle),
            'progressive_phase': self.calculate_progressive_phase_shift(self.current_steering_angle),
            'element_phases': self.phase_shifts,
            'element_spacing': self.element_spacing * self.wavelength,
            'frequency': self.frequency,
            'wavelength': self.wavelength
        }

class MultiArraySystem:
    def __init__(self):
        self.arrays = []
        
    def add_array(self, array):
        self.arrays.append(array)
        
    def remove_array(self, index):
        if 0 <= index < len(self.arrays):
            self.arrays.pop(index)
            
    def calculate_total_pattern(self, theta):
        if not self.arrays:
            return np.zeros_like(theta)
            
        total_pattern = np.zeros_like(theta, dtype=complex)
        for array in self.arrays:
            total_pattern += array.calculate_array_factor(theta)
            
        return np.abs(total_pattern) / len(self.arrays)
    
    def calculate_total_interference_map(self, x_range, y_range):
        """Calculate total interference pattern from all arrays"""
        if not self.arrays:
            x = np.linspace(x_range[0], x_range[1], x_range[2])
            y = np.linspace(y_range[0], y_range[1], y_range[2])
            X, Y = np.meshgrid(x, y)
            return X, Y, np.zeros_like(X, dtype=complex)
            
        X, Y, total_field = self.arrays[0].calculate_interference_map(x_range, y_range)
        
        for array in self.arrays[1:]:
            _, _, field = array.calculate_interference_map(x_range, y_range)
            total_field += field
            
        return X, Y, total_field
    
    def get_all_steering_info(self):
        """Get steering information for all arrays
        
        Returns:
            list: List of steering parameter dictionaries for each array
        """
        return [array.get_steering_info() for array in self.arrays]
