#!/usr/bin/env python3
"""Test script for AndersenEvConnectionSessionEnergySensor logic.

This script simulates the sensor behavior to test energy accumulation
within a connection session.
"""

class MockDevice:
    """Mock device to simulate the EV charger."""
    
    def __init__(self, friendly_name="Test Charger"):
        self.friendly_name = friendly_name
        self.device_id = "test_device_001"
        self._last_status = {}
    
    def set_status(self, evse_state, charge_energy=None, locked=False):
        """Update device status."""
        self._last_status = {
            'evseState': evse_state,
            'sysUserLock': locked
        }
        if charge_energy is not None:
            self._last_status['chargeStatus'] = {
                'chargeEnergyTotal': charge_energy
            }


class ConnectionSessionEnergySimulator:
    """Simulates the AndersenEvConnectionSessionEnergySensor logic."""
    
    def __init__(self, device):
        self._device = device
        self._accumulated_energy = 0.0
        self._last_charge_energy = None
        self._session_active = False
        self._last_evse_state = None
        self._is_locked = False
    
    def update(self):
        """Update the sensor - mimics the native_value property."""
        status = self._device._last_status
        
        # Get current evseState and lock status
        current_evse_state = status.get('evseState')
        current_locked = status.get('sysUserLock', False)
        
        # Check if we need to reset (cable disconnected or locked)
        if current_evse_state == "1" or current_evse_state == 1 or current_locked:
            # Cable disconnected or charger locked
            if self._session_active:
                print(f"🔌 Connection session ENDED. Total energy: {self._accumulated_energy} kWh")
                self._session_active = False
                self._last_charge_energy = None
                # Reset after session ends
                self._accumulated_energy = 0.0
            self._is_locked = current_locked
        
        # Check if session is starting (connected or charging)
        elif current_evse_state in ["2", "3", 2, 3]:
            # Cable connected or charging
            if not self._session_active:
                print(f"🔌 New connection session STARTED")
                self._session_active = True
                self._accumulated_energy = 0.0
                self._last_charge_energy = None
            
            # Accumulate energy if chargeStatus exists
            if 'chargeStatus' in status and 'chargeEnergyTotal' in status['chargeStatus']:
                current_charge_energy = status['chargeStatus']['chargeEnergyTotal']
                
                if current_charge_energy is not None:
                    # Sum all readings within the session
                    # If this is a new reading (different from last), add it to the total
                    if self._last_charge_energy is None:
                        # First reading in this session
                        self._accumulated_energy += current_charge_energy
                        print(f"  ⚡ Initial charge energy: {current_charge_energy} kWh, total: {self._accumulated_energy} kWh")
                    elif current_charge_energy != self._last_charge_energy:
                        # New reading - add it to accumulated total
                        self._accumulated_energy += current_charge_energy
                        print(f"  ⚡ Added energy reading: {current_charge_energy} kWh, total: {self._accumulated_energy} kWh")
                    
                    self._last_charge_energy = current_charge_energy
        
        self._last_evse_state = current_evse_state
        
        return round(self._accumulated_energy, 3)
    
    def get_value(self):
        """Get current accumulated energy."""
        return round(self._accumulated_energy, 3)


def run_test_scenario(name, steps):
    """Run a test scenario."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    device = MockDevice()
    sensor = ConnectionSessionEnergySimulator(device)
    
    for step_num, (description, evse_state, charge_energy, locked) in enumerate(steps, 1):
        print(f"\n--- Step {step_num}: {description} ---")
        print(f"  EVSE State: {evse_state}, Charge Energy: {charge_energy} kWh, Locked: {locked}")
        
        device.set_status(evse_state, charge_energy, locked)
        result = sensor.update()
        
        print(f"  📊 Current total: {result} kWh")


def main():
    """Run all test scenarios."""
    
    print("="*60)
    print("AndersenEV Connection Session Energy Sensor - Test Suite")
    print("="*60)
    
    # Test Scenario 1: Your example - multiple readings in one session
    run_test_scenario(
        "Multiple Readings in One Session",
        [
            ("Cable connected (evseState=2)", 2, None, False),
            ("First energy reading", 3, 3.1, False),
            ("Second energy reading", 3, 4.5, False),
            ("Third energy reading", 3, 6.3, False),
            ("Fourth energy reading", 3, 2.0, False),
            ("Fifth energy reading", 3, 14.0, False),
            ("Cable disconnected", 1, None, False),
        ]
    )
    
    # Test Scenario 2: Normal charging session with increasing values
    run_test_scenario(
        "Normal Charging Session (Cumulative Values)",
        [
            ("Cable connected", 2, None, False),
            ("Start charging - 5 kWh", 3, 5.0, False),
            ("Charging continues - 10 kWh", 3, 10.0, False),
            ("Charging continues - 15 kWh", 3, 15.0, False),
            ("Cable disconnected", 1, None, False),
        ]
    )
    
    # Test Scenario 3: Session reset by lock
    run_test_scenario(
        "Session Ended by Lock",
        [
            ("Cable connected", 2, None, False),
            ("Charging - 8 kWh", 3, 8.0, False),
            ("Charging - 12 kWh", 3, 12.0, False),
            ("Charger locked (session ends)", 3, 12.0, True),
            ("Charger unlocked", 3, None, False),
        ]
    )
    
    # Test Scenario 4: Multiple sessions
    run_test_scenario(
        "Multiple Connection Sessions",
        [
            ("Session 1: Cable connected", 2, None, False),
            ("Session 1: Charging - 7 kWh", 3, 7.0, False),
            ("Session 1: Cable disconnected", 1, None, False),
            ("Session 2: Cable connected", 2, None, False),
            ("Session 2: Charging - 5 kWh", 3, 5.0, False),
            ("Session 2: Cable disconnected", 1, None, False),
        ]
    )
    
    # Test Scenario 5: Duplicate readings (no change)
    run_test_scenario(
        "Duplicate Readings (Should Not Add)",
        [
            ("Cable connected", 2, None, False),
            ("First reading - 4 kWh", 3, 4.0, False),
            ("Same reading (duplicate) - 4 kWh", 3, 4.0, False),
            ("Same reading (duplicate) - 4 kWh", 3, 4.0, False),
            ("New reading - 6 kWh", 3, 6.0, False),
            ("Cable disconnected", 1, None, False),
        ]
    )
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()
