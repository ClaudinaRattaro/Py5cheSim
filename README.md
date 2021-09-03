# Py5cheSim
Py5cheSim is a flexible and open-source simulator based on Python and 
specially oriented to simulate cell capacity in 3GPP 5G networks and beyond. 
To the best of our knowledge, Py5cheSim is the first simulator that supports 
Network Slicing at the Radio Access Network (RAN), one of the main innovations of 5G. 

Py5cheSim was designed to simplify new schedulers implementation. 
The main network model abstractions are contained in the simulator Core, so there is no need to have deep knowledge on that field to run a simulation or to integrate a new scheduler. In this way Py5cheSim provides a framework for 5G new scheduler algorithms implementation in a straightforward and intuitive way.

The tool used to implement Discrete Event Simulation was SimPy and code documentation was made using pydoctor.

Py5cheSim is build on the next modules:
• UE.py: UE parameters and traffic generation.
• Cell.py: Cell configuration and statistics management.
• Slice.py: Slice configuration.
• IntraSliceSch.py: Base intra slice scheduler implementation.
• InterSliceSch.py: Base inter slice scheduler implementation.
• Scheds Intra.py: Other intra slice schedulers implementation.
• Scheds Inter.py: Other inter slice schedulers implementation.
• simulation.py: Is the simulation script. It configures and runs a simulation.
• Results.py: Provides auxiliary methods to present simulation results, and configure traffic profiles.

