CAN DATA VISUALIZATION TOOL 
- A Python-based desktop application developed for decoding, processing, and visualizing CAN (Controller Area Network) bus data used in automotive systems. The tool supports multiple CAN log formats, 
including TRC, ASC, LOG, CSV, and TXT, enabling seamless analysis of vehicle communication data.
- The application parses CAN frames, matches CAN IDs with a configurable signal database, extracts the required bytes, converts raw hexadecimal values into engineering units using 
predefined conversion formulas, and prepares the decoded data for visualization.
- The GUI provides interactive plotting features, including multiple configurable subplots, dual Y-axes (LHS/RHS), custom Y-axis limits, adjustable marker sizes, and support for both line and scatter plots. 
Decoded data can also be exported as CSV files for further analysis.

PROJECT WORKFLOW:
1) Read CAN log files from supported formats.
2) Parse CAN frames and extract message information.
3) Match CAN IDs with the signal database.
4) Decode raw hexadecimal bytes into engineering values.
5) Generate processed datasets.
6) Visualize decoded signals through an interactive plotting interface.

FEATURES:
1) Supports multiple CAN log formats - TRC, CSV, ASC, LOG, TXT
2) Automatic CAN frame parsing and signal decoding.
3) Configurable signal database with support for custom signal definitions in the format of .csv file format.
4) Converts raw CAN data into engineering values using predefined conversion formulas.
5) Interactive multi-subplot visualization with:
   - Multiple signals per subplot
   - Dual Y-axes (LHS/RHS)
   - Custom Y-axis limits
   - Adjustable marker sizes
   - Scatter and line plot support.
6) Automatic generation of decoded signal CSV files.
7) User-friendly GUI built with Python.
