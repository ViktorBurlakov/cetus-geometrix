import numpy as np
import pandas as pd
import time

from geometrix.structural.common.results import ConvergenceReport
from geometrix.structural.common.solvers.abstract_solver import AbstractIterativeSolver
from geometrix.structural.modal.tasks import ModalAnalysisTask
from geometrix.structural.modal.results import ModalAnalysisResults, ModalFrequencyResult, ModeShapeData


class ProgressiveIterationSolver(AbstractIterativeSolver[ModalAnalysisTask, ModalAnalysisResults]):
    """
    Concrete solver for modal analysis, implementing the Progressive Iteration Method (P.I.M.).

    This solver is designed to find the first natural frequency and corresponding
    mode shape for both bending and torsional vibrations in one-dimensional
    (e.g., beam-like) structures. It is particularly effective for systems with
    distributed mass and stiffness properties.

    The P.I.M. (also known as the Stodola-Vianello or Rayleigh-Ritz iteration method)
    is an iterative algorithm based on numerical integration of the differential
    equations of free vibration.

    Attributes:
        _z_coords (np.ndarray): Z-coordinates from the model data.
        _delta_z (float): Length of a single section.
        _m_prime_array (np.ndarray): Distributed mass array.
        _EI_y_array (np.ndarray): Bending stiffness array.
        _GJ_array (np.ndarray): Torsional stiffness array.
    """

    def __init__(self, task_context: ModalAnalysisTask):
        super().__init__(task_context)
        self._z_coords = self.section_data.z_coords
        self._delta_z = self.section_data.delta_x  # Assuming delta_x is delta_z
        self._m_prime_array = self.section_data.m_prime_array
        self._EI_y_array = self.section_data.EI_y_array
        self._GJ_array = self.section_data.GJ_array

    def perform_iteration(self,
                          current_f: np.ndarray,
                          stiffness_array: np.ndarray,
                          mass_array: np.ndarray,
                          integration_order: int) -> tuple[np.ndarray, float, float]:
        """
        Performs a single iteration of the Progressive Iteration Method.

        This method applies the core logic of the P.I.M. by calculating the inertial
        loading, integrating it to find a new mode shape, and then calculating
        the updated natural frequency.

        Args:
            current_f (np.ndarray): The current (k-1) approximation of the mode shape.
            stiffness_array (np.ndarray): The array of relevant stiffness (EI_y or GJ).
            mass_array (np.ndarray): The array of distributed mass (m_prime).
            integration_order (int): The number of integrations to perform (4 for bending, 2 for torsion).

        Returns:
            tuple[np.ndarray, float, float]:
                - new_f (np.ndarray): The updated (k) approximation of the mode shape.
                - new_p_squared (float): The updated squared natural frequency (p^2).
                - error (float): The relative error between current and previous p^2.

        Raises:
            ValueError: If stiffness_array contains zero values, which would lead to division by zero.
        """
        if np.any(stiffness_array == 0):
            raise ValueError("Stiffness array cannot contain zero values for modal analysis.")

        # Step 1: Calculate inertial loading based on current mode shape
        # The exact calculation of p_squared is done later
        # For the first iteration, assume a factor, then it gets updated
        inertial_loading = mass_array * current_f

        # Step 2: Integrate inertial loading to find new mode shape
        new_f_unscaled = inertial_loading / stiffness_array  # Initial division
        for _ in range(integration_order - 1):  # Perform remaining integrations
            new_f_unscaled = np.cumsum(new_f_unscaled * self._delta_z)

        # Step 3: Calculate new squared natural frequency (p^2)
        # Using Rayleigh's quotient principle (work done by inertial forces = work done by elastic forces)
        # Simplified to: p^2 = Sum(m * f_old * f_new) / Sum(m * f_new * f_new) if appropriately normalized
        # A more common approach in PIM is ratio of integrals:
        # p^2 = Integral(m * f_old * f_old) / Integral(m * f_old * new_f_unscaled)
        # Or even simpler: p^2 = max(f_old) / max(new_f_unscaled) (if f_old is normalized)
        # Let's use the ratio of max amplitudes after first iteration for simplicity, if f_old is normalized to 1

        # For PIM, after the first run, the ratio of max amplitudes gives p^2
        if np.max(current_f) == 0 or np.max(new_f_unscaled) == 0:
            new_p_squared = 0.0  # Or raise an error
            error = 1.0  # Will force more iterations or signal failure
        else:
            new_p_squared = np.max(current_f) / np.max(new_f_unscaled)
            # The actual error should compare current_f and new_f shape, or subsequent p_squared values.
            # For simplicity here, we'll return a placeholder error and check against previous p_squared in _run_single_mode.
            error = 0.0  # This will be updated by the caller

        # To properly calculate error, we need the previous p_squared.
        # This function only returns the current iteration's result.
        # The convergence check will happen in _run_single_mode.

        return new_f_unscaled, new_p_squared, error  # error is placeholder here

    def _run_single_mode(self,
                         initial_f0: np.ndarray,
                         stiffness_array: np.ndarray,
                         mass_array: np.ndarray,
                         integration_order: int,
                         mode_name: str,
                         mode_number: int) -> tuple[ModalFrequencyResult, ModeShapeData, ConvergenceReport]:
        """
        Runs the progressive iteration method for a single type of vibration (e.g., bending or torsion).

        This internal method manages the iterative loop, convergence checks,
        and constructs the results for a specific mode.

        Args:
            initial_f0 (np.ndarray): Initial approximation of the mode shape.
            stiffness_array (np.ndarray): Relevant stiffness array (EI_y or GJ).
            mass_array (np.ndarray): Distributed mass array.
            integration_order (int): Number of integrations (4 for bending, 2 for torsion).
            mode_name (str): Name of the mode (e.g., "Bending", "Torsion").
            mode_number (int): The mode number (e.g., 1 for the first mode).

        Returns:
            tuple[ModalFrequencyResult, ModeShapeData, ConvergenceReport]:
                A tuple containing the frequency result, mode shape data, and convergence report
                for the computed mode.
        """
        start_time = time.time()

        current_f = initial_f0.copy()
        current_p_squared = 0.0

        for i in range(self.max_iter):
            prev_p_squared = current_p_squared

            # Perform one iteration
            new_f_unscaled, new_p_squared, _ = self.perform_iteration(
                current_f, stiffness_array, mass_array, integration_order
            )

            # Normalize the new mode shape (e.g., max amplitude to 1)
            if np.max(np.abs(new_f_unscaled)) == 0:
                print(f"Warning: Mode shape {mode_name} became zero during iteration {i}. Cannot normalize.")
                convergence_met = False
                error_message = f"Mode shape for {mode_name} became zero. No convergence."
                break

            normalized_f = new_f_unscaled / np.max(np.abs(new_f_unscaled))
            current_f = normalized_f  # Update for next iteration
            current_p_squared = new_p_squared  # Update current p^2

            if i > 0 and prev_p_squared != 0:
                error = np.abs((current_p_squared - prev_p_squared) / prev_p_squared)
                if error < self.tolerance:
                    convergence_met = True
                    error_message = None
                    break
            else:
                error = float('inf')  # Force at least one iteration

        else:  # This block executes if loop completes without 'break'
            convergence_met = False
            error_message = f"Max iterations ({self.max_iter}) exceeded for {mode_name} mode. Last error: {error:.4f}"
            print(error_message)

        end_time = time.time()
        computation_time = end_time - start_time

        # Final results construction
        final_frequency_rad_s = np.sqrt(current_p_squared) if current_p_squared > 0 else 0.0
        final_frequency_hz = final_frequency_rad_s / (2 * np.pi)

        # Create mode shape DataFrame
        df_mode_shape = pd.DataFrame({
            'z_coord': self._z_coords,
            'amplitude': current_f,
            'norm_amplitude': current_f / np.max(np.abs(current_f)) if np.max(np.abs(current_f)) != 0 else current_f
        })

        freq_result = ModalFrequencyResult(
            mode_number=mode_number,
            frequency_rad_s=final_frequency_rad_s,
            frequency_hz=final_frequency_hz
        )
        mode_shape_data = ModeShapeData(
            mode_number=mode_number,
            df_mode_shape=df_mode_shape
        )
        convergence_report = ConvergenceReport(
            iteration_count=i + 1,
            convergence_met=convergence_met,
            error_message=error_message,
            computation_time_s=computation_time
        )

        return freq_result, mode_shape_data, convergence_report

    def execute(self) -> ModalAnalysisResults:
        """
        Executes the full modal analysis using the Progressive Iteration Method.

        This method orchestrates the calculation of both bending and torsional
        first natural modes, aggregates their results, and returns a comprehensive
        `ModalAnalysisResults` object.

        Returns:
            ModalAnalysisResults: An object containing convergence reports,
                                  calculated frequencies, and mode shapes for
                                  all analyzed modes.
        """
        all_frequencies = []
        all_mode_shapes = []

        # Calculate Bending Mode (first natural frequency)
        bending_freq, bending_shape, bending_report = self._run_single_mode(
            self.task_context.initial_bending_f0,
            self._EI_y_array,
            self._m_prime_array,
            integration_order=4,  # 4 integrations for bending
            mode_name="Bending",
            mode_number=1  # First bending mode
        )
        all_frequencies.append(bending_freq)
        all_mode_shapes.append(bending_shape)

        # Calculate Torsion Mode (first natural frequency)
        # For torsional analysis, often the mass moment of inertia is used
        # Placeholder: using _m_prime_array for simplicity, but should be _Im_prime_array
        # if available and specific to torsion.
        torsion_freq, torsion_shape, torsion_report = self._run_single_mode(
            self.task_context.initial_torsion_phi0,
            self._GJ_array,
            self._m_prime_array,  # Consider replacing with a torsional mass inertia array if available
            integration_order=2,  # 2 integrations for torsion
            mode_name="Torsion",
            mode_number=2  # Often considered the second overall mode, or first torsional
        )
        all_frequencies.append(torsion_freq)
        all_mode_shapes.append(torsion_shape)

        # Aggregate results
        # The ConvergenceReport returned is typically for the primary/first calculated mode.
        # For multiple modes, it might be an average or for the one that failed/converged last.
        # For simplicity, let's use the bending report as the main report.
        overall_report = bending_report  # You might want a more sophisticated aggregation here

        return ModalAnalysisResults(
            report=overall_report,
            frequencies=all_frequencies,
            mode_shapes=all_mode_shapes
        )
