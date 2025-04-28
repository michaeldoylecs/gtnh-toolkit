# Write tests to check the correctness of VoltageTier and Voltage from gamelogic.Electricity
import unittest
# Correct the import path
from gamelogic.Electricity import VoltageTier, Voltage

class TestVoltageTier(unittest.TestCase):
    def test_from_tier_num(self):
        # Test the from_tier_num class method
        self.assertEqual(VoltageTier.from_tier_num(1), VoltageTier.LV) # LV is now 1
        self.assertEqual(VoltageTier.from_tier_num(2), VoltageTier.MV) # MV is now 2
        self.assertEqual(VoltageTier.from_tier_num(5), VoltageTier.IV) # IV is now tier 5
        self.assertEqual(VoltageTier.from_tier_num(14), VoltageTier.MAX) # MAX is now 14

        # Test boundary conditions (should clamp between 1 and 14)
        self.assertEqual(VoltageTier.from_tier_num(0), VoltageTier.LV)  # Should clamp to min (LV=1)
        self.assertEqual(VoltageTier.from_tier_num(-1), VoltageTier.LV) # Should clamp to min (LV=1)
        self.assertEqual(VoltageTier.from_tier_num(15), VoltageTier.MAX) # Should clamp to max (MAX=14)
        self.assertEqual(VoltageTier.from_tier_num(20), VoltageTier.MAX) # Should clamp to max (MAX=14)

    def test_from_name(self):
        # Test the from_name class method
        self.assertEqual(VoltageTier.from_name("MV"), VoltageTier.MV)
        self.assertEqual(VoltageTier.from_name("MAX"), VoltageTier.MAX)

        # Test case insensitivity
        self.assertEqual(VoltageTier.from_name("lv"), VoltageTier.LV)
        self.assertEqual(VoltageTier.from_name("mV"), VoltageTier.MV)

        # Test invalid name
        with self.assertRaises(ValueError):
            VoltageTier.from_name("NotATier")

class TestVoltage(unittest.TestCase):
    def test_initialization(self):
        # Test basic initialization
        v = Voltage(32)
        self.assertEqual(v.voltage, 32)
        
        # Test negative voltage is clamped to 0
        v_neg = Voltage(-10)
        self.assertEqual(v_neg.voltage, 0)
    
    def test_tier_property(self):
        # Test tier calculation for standard voltages based on V_max(T) = 32 * 4^(T-1)
        # LV (T=1): Vmax=32. Range (0, 32]
        # MV (T=2): Vmax=128. Range (32, 128]
        # HV (T=3): Vmax=512. Range (128, 512]
        self.assertEqual(Voltage(0).tier, VoltageTier.LV) # 0 voltage maps to LV
        self.assertEqual(Voltage(1).tier, VoltageTier.LV)
        self.assertEqual(Voltage(8).tier, VoltageTier.LV)
        self.assertEqual(Voltage(31).tier, VoltageTier.LV)
        self.assertEqual(Voltage(32).tier, VoltageTier.LV) # Max voltage of LV tier

        self.assertEqual(Voltage(33).tier, VoltageTier.MV) # Start of MV range
        self.assertEqual(Voltage(127).tier, VoltageTier.MV)
        self.assertEqual(Voltage(128).tier, VoltageTier.MV) # Max voltage of MV tier

        self.assertEqual(Voltage(129).tier, VoltageTier.HV) # Start of HV range
        self.assertEqual(Voltage(511).tier, VoltageTier.HV)
        self.assertEqual(Voltage(512).tier, VoltageTier.HV) # Max voltage of HV tier

        # Test tier calculation for in-between voltages
        self.assertEqual(Voltage(20).tier, VoltageTier.LV)
        self.assertEqual(Voltage(100).tier, VoltageTier.MV)
        self.assertEqual(Voltage(300).tier, VoltageTier.HV)

        # Test very high voltage
        max_voltage_val = 32 * (4**(VoltageTier.MAX.value - 1)) # Max voltage of MAX tier
        self.assertEqual(Voltage(max_voltage_val).tier, VoltageTier.MAX)
        # Voltage higher than MAX tier's max voltage should still clamp to MAX tier
        self.assertEqual(Voltage(max_voltage_val + 1).tier, VoltageTier.MAX)
        self.assertEqual(Voltage(max_voltage_val * 2).tier, VoltageTier.MAX)

    def test_from_tier(self):
        # Test creating MAX voltage from tier (using base voltage 32 and tier values)
        # V_max(T) = 32 * 4^(T-1)
        self.assertEqual(Voltage.from_tier(VoltageTier.LV).voltage, 32)  # LV (tier 1) -> 32 * 4^0 = 32
        self.assertEqual(Voltage.from_tier(VoltageTier.MV).voltage, 128) # MV (tier 2) -> 32 * 4^1 = 128
        self.assertEqual(Voltage.from_tier(VoltageTier.HV).voltage, 512) # HV (tier 3) -> 32 * 4^2 = 512
        self.assertEqual(Voltage.from_tier(VoltageTier.EV).voltage, 2048) # EV (tier 4) -> 32 * 4^3 = 2048
        self.assertEqual(Voltage.from_tier(VoltageTier.MAX).voltage, 32 * (4**13)) # MAX (tier 14) -> 32 * 4^13

    def test_equality(self):
        # Test equality comparison
        self.assertEqual(Voltage(32), Voltage(32))
        self.assertNotEqual(Voltage(32), Voltage(64))
        
        # Test equality with non-Voltage objects
        self.assertNotEqual(Voltage(32), 32)
    
    def test_representation(self):
        # Test string representation
        v = Voltage(30) # 30 is in LV range (0-32]
        self.assertEqual(repr(v), f"Voltage(30, {VoltageTier.LV})")
        v_mv = Voltage(100) # 100 is in MV range (32-128]
        self.assertEqual(repr(v_mv), f"Voltage(100, {VoltageTier.MV})")
        v_hv = Voltage(512) # 512 is max of HV range (128-512]
        self.assertEqual(repr(v_hv), f"Voltage(512, {VoltageTier.HV})")


    def test_addition(self):
        # Test addition with another Voltage
        v1 = Voltage(32)
        v2 = Voltage(128)
        result = v1 + v2
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 160)
        
        # Test addition with an integer
        result = v1 + 100
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 132)
        
        # Test right-side addition
        result = 100 + v1
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 132)

    def test_subtraction(self):
        # Test subtraction with another Voltage
        v1 = Voltage(128)
        v2 = Voltage(32)
        result = v1 - v2
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 96)
        
        # Test subtraction with an integer
        result = v1 - 50
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 78)
        
        # Test right-side subtraction
        result = 200 - v2
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 168)
        
        # Test that negative results are clamped to 0
        result = v2 - v1
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 0)

    def test_multiplication(self):
        # Test multiplication with an integer
        v = Voltage(32)
        result = v * 4
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 128)
        
        # Test right-side multiplication
        result = 4 * v
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 128)
        
        # Test multiplication with a float
        result = v * 2.5
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 80)

    def test_division(self):
        # Test division with another Voltage
        v1 = Voltage(128)
        v2 = Voltage(32)
        result = v1 / v2
        self.assertIsInstance(result, float)
        self.assertEqual(result, 4.0)
        
        # Test division with an integer
        result = v1 / 4
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 32)
        
        # Test right-side division
        result = 256 / v2
        self.assertIsInstance(result, Voltage)
        self.assertEqual(result.voltage, 8)

    def test_comparison(self):
        v1 = Voltage(32)
        v2 = Voltage(128)
        v3 = Voltage(32)
        
        # Test less than
        self.assertTrue(v1 < v2)
        self.assertFalse(v2 < v1)
        self.assertFalse(v1 < v3)
        self.assertTrue(v1 < 100)
        
        # Test less than or equal
        self.assertTrue(v1 <= v2)
        self.assertTrue(v1 <= v3)
        self.assertFalse(v2 <= v1)
        self.assertTrue(v1 <= 32)
        
        # Test greater than
        self.assertTrue(v2 > v1)
        self.assertFalse(v1 > v2)
        self.assertFalse(v1 > v3)
        self.assertTrue(v2 > 100)
        
        # Test greater than or equal
        self.assertTrue(v2 >= v1)
        self.assertTrue(v1 >= v3)
        self.assertFalse(v1 >= v2)
        self.assertTrue(v1 >= 32)

    def test_conversion(self):
        v = Voltage(128)
        
        # Test int conversion
        result = int(v)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 128)
        
        # Test float conversion
        result2 = float(v)
        self.assertIsInstance(result2, float)
        self.assertEqual(result, 128.0)

if __name__ == '__main__':
    unittest.main()
