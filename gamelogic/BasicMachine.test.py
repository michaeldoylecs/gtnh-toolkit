# Write tests to check the correctness of VoltageTier and Voltage from the BasicMachine.py file AI!
import unittest
import math
from gamelogic.BasicMachine import VoltageTier, Voltage, GameTicks

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
        self.assertEqual(Voltage(8).tier, VoltageTier.LV)
        self.assertEqual(Voltage(32).tier, VoltageTier.MV)
        self.assertEqual(Voltage(128).tier, VoltageTier.HV)
        self.assertEqual(Voltage(512).tier, VoltageTier.EV)
        
        # Test tier calculation for in-between voltages
        self.assertEqual(Voltage(20).tier, VoltageTier.MV)  # Between LV and MV, should round up to MV
        self.assertEqual(Voltage(100).tier, VoltageTier.HV)  # Between MV and HV, should round up to HV
        
        # Test very high voltage
        very_high = 8 * (4 ** 15)  # Beyond MAX tier
        self.assertEqual(Voltage(very_high).tier, VoltageTier.MAX)  # Should clamp to MAX
    
    def test_from_tier(self):
        # Test creating voltage from tier
        self.assertEqual(Voltage.from_tier(VoltageTier.ULV).voltage, 0)
        self.assertEqual(Voltage.from_tier(VoltageTier.LV).voltage, 8)
        self.assertEqual(Voltage.from_tier(VoltageTier.MV).voltage, 32)
        self.assertEqual(Voltage.from_tier(VoltageTier.HV).voltage, 128)
        self.assertEqual(Voltage.from_tier(VoltageTier.EV).voltage, 512)
    
    def test_equality(self):
        # Test equality comparison
        self.assertEqual(Voltage(32), Voltage(32))
        self.assertNotEqual(Voltage(32), Voltage(64))
        
        # Test equality with non-Voltage objects
        self.assertNotEqual(Voltage(32), 32)
    
    def test_representation(self):
        # Test string representation
        v = Voltage(32)
        self.assertEqual(repr(v), f"Voltage(32, {VoltageTier.MV})")

class TestOverclockCalculations(unittest.TestCase):
    def test_overclock_calculation(self):
        from gamelogic.BasicMachine import BasicMachineRecipe, ItemStack
        
        # Create a basic recipe
        machine_name = "Electric Furnace"
        machine_voltage = Voltage.from_tier(VoltageTier.MV)  # MV tier (32 EU/t)
        inputs = [ItemStack("Iron Ore", 1)]
        outputs = [ItemStack("Iron Ingot", 1)]
        duration = GameTicks(200)
        eu_per_gametick = 16  # LV recipe
        
        # Create the recipe
        recipe = BasicMachineRecipe(
            machine_name=machine_name,
            machine_voltage=machine_voltage,
            inputs=inputs,
            outputs=outputs,
            duration=duration,
            eu_per_gametick=eu_per_gametick
        )
        
        # Check that overclock was applied correctly
        # LV recipe in MV machine: tier_ratio = 1/2 = 0.5
        # speed_overclock = 2^0.5 = 1.414
        # power_overclock = 4^0.5 = 2
        # new_duration = 200 / 1.414 ≈ 142 (rounded up)
        # new_eu = 16 * 2 = 32
        self.assertEqual(recipe.duration, GameTicks(142))
        self.assertEqual(recipe.eu_per_gametick, 32)
        
        # Test with higher tier machine
        machine_voltage_hv = Voltage.from_tier(VoltageTier.HV)  # HV tier (128 EU/t)
        recipe_hv = BasicMachineRecipe(
            machine_name=machine_name,
            machine_voltage=machine_voltage_hv,
            inputs=inputs,
            outputs=outputs,
            duration=duration,
            eu_per_gametick=eu_per_gametick
        )
        
        # LV recipe in HV machine: tier_ratio = 1/3 = 0.333
        # speed_overclock = 2^0.333 ≈ 1.26
        # power_overclock = 4^0.333 ≈ 1.587
        # new_duration = 200 / 1.26 ≈ 159 (rounded up)
        # new_eu = 16 * 1.587 ≈ 25
        self.assertEqual(recipe_hv.duration, GameTicks(159))
        self.assertEqual(recipe_hv.eu_per_gametick, 25)

if __name__ == '__main__':
    unittest.main()
