# Todo
 - Machine overclocking
 - Fix multiple destination machine outputs not having an ItemNode joint
 - Add overview panel for item input, item output, and energy input and output
 - Add recipe input/output numbers to each machine

# Problem Modeling
 - Every recipe input has a M#_IN node.
 - Every unique recipe input has a SOURCE node and a SOURCE_OUT node.
 - Every recipe output has a M#_OUT node.
 - Every unique recipe output has a ITEM_

# Basic Program Flow
 1. Parse factory config
 2. Normalize machine names
 3. Apply machine overclocks and logic
 4. Solve factory
 5. Graph factory
