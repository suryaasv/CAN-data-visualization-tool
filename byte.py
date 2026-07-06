import pandas as pd
import re
import os

def normalize_can_id(can_id):
    can_id = str(can_id).upper().strip()

    if can_id.startswith("0X"):
        can_id = can_id[2:]

    if can_id.endswith("X"):
        can_id = can_id[:-1]

    return can_id.zfill(8)

def load_input_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".trc":
        return load_trc(file_path)

    elif ext in (".csv", ".log"):
        return load_busmaster(file_path)

    elif ext == ".asc":
        return load_asc(file_path)

    elif ext == ".txt":
        return load_txt(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            "Supported: .trc, .csv, .log, .asc, .txt"
        )

def load_busmaster(file_path):
    pattern = re.compile(
    r'^(\d+:\d+:\d+:\d+)\s+'      # Time
    r'(Rx|Tx)\s+'                 # Direction
    r'(\d+)\s+'                   # Channel
    r'(0x[0-9A-Fa-f]+)\s+'        # CAN ID
    r'([sx])\s+'                  # Frame type
    r'(\d+)\s+'                   # DLC
    r'((?:[0-9A-Fa-f]{2}\s*)+)'   # Data bytes
    r'.*$'                        # Ignore anything after bytes (e.g. trailing 't')
)

    rows = []
    num = 1

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

        # Skip BUSMASTER header lines
            if line.startswith("***"):
                continue

        # Skip comment lines if any
            if line.startswith("//"):
                continue

            match = pattern.match(line)

        # Skip anything that is not a CAN frame
            if not match:
                 continue
            # Convert HH:MM:SS:mmm → seconds
            time_stamp = match.group(1)

# Convert 4-digit milliseconds to 2 digits
            h, m, s, ms = time_stamp.split(":")
            ms = str(round(int(ms) / 100)).zfill(2)
            time_stamp = f"{h}:{m}:{s}:{ms}"
            direction = match.group(2)
            can_id = match.group(4).upper().replace("0X", "")
            length = int(match.group(6))
            data = match.group(7).split()

            while len(data) < 8:
                data.append("00")

            rows.append([
                num,
                time_stamp,
                direction,
                can_id,
                length,
                data[0],
                data[1],
                data[2],
                data[3],
                data[4],
                data[5],
                data[6],
                data[7]
            ])
            num += 1

    columns = ["num", "time", "type", "can_id", "length",
               "byte0", "byte1", "byte2", "byte3",
               "byte4", "byte5", "byte6", "byte7"]
    df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        raise ValueError(
            f"No valid CAN frames found in BUSMASTER file: {file_path}"
        )
    return df

load_csv = load_busmaster

def load_trc(file_path):
    rows = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith(";"):
                continue
            if line.startswith("---"):
                continue

            parts = line.split()

            if len(parts) < 6:
                continue

            try:
                num = int(parts[0].replace(")", ""))
                timestamp = float(parts[1])

                if parts[2] in ("Rx", "Tx"):

                    direction = parts[2]
                    can_id = parts[3].upper()
                    length = int(parts[4])
                    data = parts[5:5 + length]

                else:
                    direction = parts[3]
                    can_id = parts[4].upper()
                    length = int(parts[6])
                    data = parts[7:7 + length]

                while len(data) < 8:
                    data.append("00")

                rows.append([
                    num,
                    timestamp,
                    direction,
                    can_id,
                    length,
                    data[0],
                    data[1],
                    data[2],
                    data[3],
                    data[4],
                    data[5],
                    data[6],
                    data[7]
                ])

            except Exception:
                continue

    columns = [
        "num",
        "time",
        "type",
        "can_id",
        "length",
        "byte0",
        "byte1",
        "byte2",
        "byte3",
        "byte4",
        "byte5",
        "byte6",
        "byte7"
    ]

    df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        raise ValueError(
            f"No valid CAN frames found in TRC file: {file_path}"
        )

    return df

def load_asc(file_path):
    rows = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        num = 1

        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            lower = line.lower()

            if lower.startswith(("date", "base", "internal", "begin",
                                 "end", "version", "//", "statistic", "no")):
                continue

            parts = line.split()

            if len(parts) < 7:
                continue

            try:
                timestamp = float(parts[0])
            except ValueError:
                continue

            try:
                direction = parts[3]

                if direction not in ("Rx", "Tx"):
                    continue

                can_id = parts[2].upper()
                if can_id.endswith("X"):
                    can_id = can_id[:-1]

                if can_id.startswith("0X"):
                    can_id = can_id[2:]

                length = int(parts[5])

                data = parts[6:6 + length]

                while len(data) < 8:
                    data.append("00")

                rows.append([
                    num,
                    timestamp,
                    direction,
                    can_id,
                    length,
                    data[0],
                    data[1],
                    data[2],
                    data[3],
                    data[4],
                    data[5],
                    data[6],
                    data[7]
                ])

                num += 1

            except Exception:
                continue

    columns = [
        "num",
        "time",
        "type",
        "can_id",
        "length",
        "byte0",
        "byte1",
        "byte2",
        "byte3",
        "byte4",
        "byte5",
        "byte6",
        "byte7"
    ]

    df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        raise ValueError(
            f"No valid CAN frames found in ASC file: {file_path}"
        )

    return df

def load_txt(file_path):
    rows = []
    num = 1

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:

        for raw_line in f:
            line = raw_line.strip()

            # Skip blank lines
            if not line:
                continue

            # Skip header/comment lines
            if line.startswith(("Logging", "//", "Date", "Begin", "End")):
                continue

            # Split by semicolon
            parts = [p.strip() for p in line.split(";")]

            # Need at least:
            # Time;Type;ID;DLC;Byte0
            if len(parts) < 5:
                continue

            # -----------------------
            # Time
            # -----------------------
            try:
                timestamp = float(parts[0])
            except ValueError:
                continue

            # -----------------------
            # Direction
            # -----------------------
            direction = parts[1].upper()

            if direction == "RX":
                direction = "Rx"
            elif direction == "TX":
                direction = "Tx"
            else:
                continue

            # -----------------------
            # CAN ID
            # Example:
            # 0xCFF4500x
            # -> CFF4500
            # -----------------------
            can_id = parts[2].upper().strip()

            if can_id.startswith("0X"):
                can_id = can_id[2:]

            if can_id.endswith("X"):
                can_id = can_id[:-1]

            # Validate hex ID
            if not re.fullmatch(r"[0-9A-F]+", can_id):
                continue

            # -----------------------
            # DLC
            # -----------------------
            try:
                length = int(parts[3])
            except ValueError:
                continue

            # -----------------------
            # Data bytes
            # -----------------------
            raw_bytes = parts[4:4 + length]

            data = []

            for b in raw_bytes:

                b = b.upper().strip()

                if b.startswith("0X"):
                    b = b[2:]

                if re.fullmatch(r"[0-9A-F]{1,2}", b):
                    data.append(b.zfill(2))

            if len(data) < length:
                continue

            while len(data) < 8:
                data.append("00")

            rows.append([
                num,
                timestamp,
                direction,
                can_id,
                length,
                data[0],
                data[1],
                data[2],
                data[3],
                data[4],
                data[5],
                data[6],
                data[7]
            ])

            num += 1

    columns = [
        "num",
        "time",
        "type",
        "can_id",
        "length",
        "byte0",
        "byte1",
        "byte2",
        "byte3",
        "byte4",
        "byte5",
        "byte6",
        "byte7"
    ]

    df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        raise ValueError(
            f"No valid CAN frames found in TXT file: {file_path}"
        )

    return df

def get_signal_database():
    signal_data = [
        ["18FD2000", "A1DOC", "Exhaust Temperature",
         "Byte 1 & 2", "Exh_tOxiCatUs",
         "x0.03125 - 273", "Working"],

        ["18FD2000", "A1DOC", "Exhaust Temperature",
         "Byte 3 & 4", "Exh_tPFltUs",
         "x0.03125 - 273", "Working"],

        ["18FEF500", "AMB", "Ambient Details",
         "Byte1", "ENVP",
         "x0.5", "Working"],

        ["18FEF500", "AMB", "Ambient Details",
         "Byte 4 & 5", "ENVT",
         "x0.03125 - 273", "Working"],

        ["18FDB200", "AT1IMG", "Delta P",
         "Byte 5 & 6", "Exh_pFltPPFltDif",
         "x0.1", "Working"],

        ["18FDB300", "AT1OG2", "Exhaust Temperature",
         "Byte 1 & 2", "SCRT_tUCatDsT",
         "x0.03125 - 273", "Working"],

        ["18FEF600", "IC1", "Inlet Information",
         "Byte2", "Air_pIntkVUs (Gauge)",
         "x2", "Working"],

        ["18FEF600", "IC1", "Inlet Information",
         "Byte3", "Air_tCACDs",
         "x1", "Working"],

        ["18FEF600", "IC1", "Inlet Information",
         "Byte4", "Air_pIntkVUs (Absolute)",
         "x2", "Working"],

        ["0CF00400", "EEC1", "Engine Speed & Torque",
         "Byte3", "% Torque",
         "x1 - 125", "Working"],

        ["0CF00400", "EEC1", "Engine Speed & Torque",
         "Byte 4 & 5", "Engine Speed",
         "x0.125", "Working"],

        ["0CF00300", "EEC2", "APP",
         "Byte2", "Acc pedal %",
         "x0.4", "Working"],

        ["18FEEE00", "ET1", "Engine Temperature",
         "Byte1", "Coolant Temperature",
         "x1 - 40", "Working"],

        ["18FEEE00", "ET1", "Engine Temperature",
         "Byte 3 & 4", "Oil Temperature",
         "x0.03125 - 273", "Working"],

        ["18FEF700", "VEP", "Battery Voltage",
         "Byte 5 & 6", "Battery",
         "x0.05", "Working"],

        ["18FEF700", "VEP", "Battery Voltage",
         "Byte 7 & 8", "Key Voltage",
         "x0.05", "Working"],

        ["18FEEF00", "EFL", "Oil Pressure",
         "Byte 4", "Oil Pressure",
         "x4", "Working"],

        ["18FD7C00", "DPFC1", "DPF Information",
         "Byte 1 (1-3)", "DPFLmp",
         "x1", "Working"],

        ["18FD7C00", "DPFC1", "DPF Information",
         "Byte 2 (3-4)", "Regeneration Status",
         "x1", "Working"],

        ["18FD7C00", "DPFC1", "DPF Information",
         "Byte 3 (3-4)", "Inhibit Switch",
         "x1", "Working"],

        ["18FD7C00", "DPFC1", "DPF Information",
         "Byte 7 (3-5)", "HESTLmp",
         "x1", "Working"]
    ]

    columns = [
        "Message ID", "PGN Name", "Information",
        "Byte", "INCA Variable / Signal", "Conversion", "Status"
    ]
    return pd.DataFrame(signal_data, columns=columns)

def get_concatenated_bytes(row, byte_spec):
    byte_spec = str(byte_spec).strip()
    if "-" in byte_spec:
        start, end = map(int, byte_spec.split("-"))
        nums = list(range(start, end + 1))
    elif "&" in byte_spec:
        nums = [int(x) for x in byte_spec.split("&")]
    else:
        nums = [int(byte_spec)]

    nums = nums[::-1]
    hex_parts = []
    for n in nums:
        byte_col = f"byte{n-1}"
        if byte_col not in row.index:
            continue
        value = row[byte_col]
        if pd.isna(value):
            continue
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                continue
            hex_parts.append(value.upper())
        else:
            hex_parts.append(f"{int(value):02X}")
    return "".join(hex_parts)


def apply_conversion(decimal_byte, conversion):
    if pd.isna(conversion):
        return None
    conversion = str(conversion).strip().replace(" ", "")
    try:
        if "-" in conversion:
            multiplier, offset = conversion[1:].split("-", 1)
            return float(decimal_byte) * float(multiplier) - float(offset)
        elif "+" in conversion:
            multiplier, offset = conversion[1:].split("+", 1)
            return float(decimal_byte) * float(multiplier) + float(offset)
        else:
            multiplier = conversion[1:]
            return float(decimal_byte) * float(multiplier)
    except Exception:
        return None

def decode_signals(input_file, custom_signal_csv=None):
    """
    Main decoding pipeline.
    1. Load the input file via the appropriate parser.
    2. Match each CAN frame against the signal database.
    3. Concatenate bytes, apply conversion, export CSVs.
    Returns the long-format decoded DataFrame.
    """
    df = load_input_file(input_file)
    
    if isinstance(df["time"].iloc[0], str):

        dt = pd.to_datetime(
            df["time"],
            format="%H:%M:%S:%f"
        )
        ms = dt.dt.microsecond.div(10000).round().astype(int)
        df["time"] = (
            dt.dt.strftime("%H:%M:%S:")
            + ms.astype(str).str.zfill(2)
        )
        
    df["can_id"] = df["can_id"].apply(normalize_can_id)
    
    file_type = os.path.splitext(input_file)[1].replace(".", "").upper()
    print(f"{file_type} File - Dataframe :")
    print(df.head())

    signal_df = get_signal_database()

    if custom_signal_csv and os.path.exists(custom_signal_csv):
        custom_df = pd.read_csv(custom_signal_csv)
        signal_df = pd.concat([signal_df, custom_df], ignore_index=True)
        signal_df = signal_df.drop_duplicates(
            subset=["Message ID", "INCA Variable / Signal"],
            keep="last"
        )

    signal_df["Message ID"] = signal_df["Message ID"].apply(normalize_can_id)
    signal_df["Message ID"] = (
        signal_df["Message ID"]
        .astype(str).str.strip().str.upper()
        .str.replace("0X", "", regex=False)
    )
    signal_df["Byte"] = (
        signal_df["Byte"]
        .astype(str)
        .str.replace("Byte", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(r'^\d+\((.*?)\)$', r'\1', regex=True)
    )

    results = []
    for _, sig in signal_df.iterrows():
        message_id = str(sig["Message ID"]).strip()
        temp_df = df[df["can_id"] == message_id]
        for _, row in temp_df.iterrows():
            concat_value = get_concatenated_bytes(row, sig["Byte"])
            if concat_value == "":
                continue
            results.append({
                "time":             row["time"],
                "message_id":       message_id,
                "signal":           sig.get("INCA Variable / Signal", ""),
                "byte_spec":        sig["Byte"],
                "conversion":       sig.get("Conversion", ""),
                "concatenated_byte": concat_value
            })

    result_df = pd.DataFrame(results)

    print("Fixed Data - Dataframe :")
    print(signal_df.head())
    print("Concatenated Bytes - Dataframe :")
    print(result_df.head())

    if result_df.empty:
        return pd.DataFrame()

    decoded_df = result_df[
        ["time", "signal", "concatenated_byte", "conversion"]
    ].copy()
    decoded_df["decimal_byte"] = decoded_df["concatenated_byte"].apply(
        lambda x: int(str(x), 16)
    )

    print("Decimal Bytes - Dataframe :")
    print(decoded_df.head())

    final_df = decoded_df[
        ["time", "signal", "decimal_byte", "conversion"]
    ].copy()
    final_df["decoded_value"] = final_df.apply(
        lambda row: apply_conversion(row["decimal_byte"], row["conversion"]),
        axis=1
    )

    final_df.to_csv("final_df.csv", index=False)

    wide_df = (
        final_df
        .pivot_table(index="time", columns="signal",
                     values="decoded_value", aggfunc="last")
        .reset_index()
        .sort_values("time")
        .reset_index(drop=True)
    )
    wide_df.to_csv("signals_by_time.csv", index=False)

    return final_df

if __name__ == "__main__":
    candidates = [
        "data.trc", "data.csv", "log file.log",
        "data.asc", "data.txt"
    ]
    input_file = next((f for f in candidates if os.path.exists(f)), None)

    if input_file is None:
        raise FileNotFoundError(
            "No supported input file found. "
            "Expected one of: " + ", ".join(candidates)
        )

    final_df = decode_signals(input_file)

    print("Final Converted Bytes - Dataframe :")
    print(final_df.head())
    
    plot_data = final_df[["time", "signal", "decoded_value"]].copy()
    plot_data.to_csv("plot_data.csv", index=False)

    print("Plotting Data Dataframe :")
    print(plot_data.head())
    print(f"\nTotal Rows: {len(final_df):,}")