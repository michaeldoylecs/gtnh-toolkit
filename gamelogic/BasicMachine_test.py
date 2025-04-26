# Write tests to check the correctness of VoltageTier and Voltage from the BasicMachine.py file AI!
import unittest
from gamelogic.BasicMachine import VoltageTier, Voltage

class TestVoltageTier(unittest.TestCase):
    def test_voltage_tier_values(self):
        # Test that the enum values are as expected
        self.assertEqual(VoltageTier.ULV.value, 0)
        self.assertEqual(VoltageTier.LV.value, 1)
        self.assertEqual(VoltageTier.MV.value, 2)
        self.assertEqual(VoltageTier.MAX.value, 14)
    
    def test_from_int(self):
        # Test the from_int class method
        self.assertEqual(VoltageTier.from_int(0), VoltageTier.ULV)
        self.assertEqual(VoltageTier.from_int(1), VoltageTier.LV)
        self.assertEqual(VoltageTier.from_int(5), VoltageTier.IV)
        self.assertEqual(VoltageTier.from_int(14), VoltageTier.MAX)
        
        # Test boundary conditions
        self.assertEqual(VoltageTier.from_int(-1), VoltageTier.ULV)  # Should clamp to min
        self.assertEqual(VoltageTier.from_int(20), VoltageTier.MAX)  # Should clamp to max
    
    def test_string_representation(self):
        # Test the string representation
        self.assertEqual(str(VoltageTier.ULV), "ULV")
        self.assertEqual(str(VoltageTier.MV), "MV")
        self.assertEqual(str(VoltageTier.MAX), "MAX")

class TestVoltage(unittest.TestCase):
    def test_initialization(self):
        # Test basic initialization
        v = Voltage(32)
        self.assertEqual(v.voltage, 32)
        
        # Test negative voltage is clamped to 0
        v_neg = Voltage(-10)
        self.assertEqual(v_neg.voltage, 0)
    
    def test_tier_property(self):
        # Test tier calculation for standard voltages
        self.assertEqual(Voltage(0).tier, VoltageTier.ULV)
        self.assertEqual(Voltage(8).tier, VoltageTier.ULV)
        self.assertEqual(Voltage(32).tier, VoltageTier.LV)
        self.assertEqual(Voltage(128).tier, VoltageTier.MV)
        self.assertEqual(Voltage(512).tier, VoltageTier.HV)
        
        # Test tier calculation for in-between voltages
        self.assertEqual(Voltage(20).tier, VoltageTier.LV)  # Between LV and MV, should round up to MV
        self.assertEqual(Voltage(100).tier, VoltageTier.MV)  # Between MV and HV, should round up to HV
        
        # Test very high voltage
        very_high = 8 * (4 ** 15)  # Beyond MAX tier
        self.assertEqual(Voltage(very_high).tier, VoltageTier.MAX)  # Should clamp to MAX
    
    def test_from_tier(self):
        # Test creating voltage from tier
        self.assertEqual(Voltage.from_tier(VoltageTier.ULV).voltage, 8)
        self.assertEqual(Voltage.from_tier(VoltageTier.LV).voltage, 32)
        self.assertEqual(Voltage.from_tier(VoltageTier.MV).voltage, 128)
        self.assertEqual(Voltage.from_tier(VoltageTier.HV).voltage, 512)
        self.assertEqual(Voltage.from_tier(VoltageTier.EV).voltage, 2048)
    
    def test_equality(self):
        # Test equality comparison
        self.assertEqual(Voltage(32), Voltage(32))
        self.assertNotEqual(Voltage(32), Voltage(64))
        
        # Test equality with non-Voltage objects
        self.assertNotEqual(Voltage(32), 32)
    
    def test_representation(self):
        # Test string representation
        v = Voltage(30)
        self.assertEqual(repr(v), f"Voltage(30, {VoltageTier.LV})")

if __name__ == '__main__':
    unittest.main()
