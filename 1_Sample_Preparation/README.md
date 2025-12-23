# Sample Preparation Protocols

Automated Hamilton liquid handling protocols for high-throughput microbial interaction studies on solid media.

## Overview

This repository contains two Hamilton Microlab STAR protocols for preparing yeast strain interaction experiments:

1. **Mix and Dispense** - Automated mixing of strain pairs and distribution into 96-well plates
2. **Plating** - Automated transfer from liquid culture to solid agar plates using a custom pinning tool

These protocols enable systematic analysis of pairwise interactions between multiple yeast strains in different environmental conditions.

## System Requirements

- **Hamilton Microlab STAR/Starlet** liquid handling system
- **Venus 4** software (version 4.7.0.7744)
- **Hardware**: 4x 1000µL pipetting heads, CO-RE grippers
- **Custom pinning tool**: 96-pin array (0.8mm diameter steel pins, 1.5mm head)

## Protocol 1: Mix and Dispense

Automates the preparation of strain mixtures in defined ratios and distributes them into 96-well format.

**Key features**:
- User-defined mixing ratios via Excel worksheet
- Customizable plate layouts
- Automated liquid handling for replicates
- Simple UI for everyday lab use

**Files**:
- `Dispense.hsl` - Main protocol script
- `Dispense.lay` - Deck layout
- `Dispense.med` - Method file
- `Package/Dispense_v6.1_MethodsPaper_Compact.pkg` - Complete package
- `Manual/Mix_and_Dispence_Manual.pdf` - User manual

## Protocol 2: Plating (Colony Screening)

Transfers liquid cultures from 96-well plates onto solid agar media using a custom 96-pin stamping tool.

**Key features**:
- Custom pinning tool for precise inoculation
- Multiple immersion to prevent bubble formation
- Processes 3 plates per cycle
- Excel-based worklist configuration

**Files**:
- `colony_screening.hsl` - Main protocol script
- `colony_screening.lay` - Deck layout
- `colony_screening_systems_deck.lay` - System deck layout
- `colony_screening.med` - Method file
- `Package/2025.12.19_ColonyScreening_6_Methods_Compact.pkg` - Complete package
- `Manual/Plating_Manual.odp` - User manual (presentation format)




