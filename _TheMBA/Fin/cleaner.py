import pandas as pd


# =====================================
# SAFE NUMERIC CLEAN
# Works even if columns are duplicated
# =====================================

def try_numeric(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(s, errors="coerce")

def clean_numeric_columns(df):

    df = df.copy()

    # CRITICAL FIX:
    # Force object dtype to avoid Arrow string crash
    df = df.astype(object)

    for i in range(df.shape[1]):

        col = df.iloc[:, i]

        # Skip datetime
        if pd.api.types.is_datetime64_any_dtype(col):
            continue

        try:

            cleaned = (
                col
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )

            numeric = pd.to_numeric(
                cleaned,
                errors="coerce"
            )

            # Replace only if numeric detected
            if numeric.notna().sum() > 0:

                df.iloc[:, i] = numeric

        except:

            continue

    return df

# =====================================
# DROP FULLY EMPTY COLUMNS
# =====================================

def drop_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(axis=1, how="all")

def clean_overview(df):

    if df is None or df.empty:
        return df

    df = df.copy()

    # ----------------------------------
    # STEP 1 — Assign Correct Header
    # (Matches Overview_Snapshot)
    # ----------------------------------

    df.columns = [

        "Date",
        "Company_Name",
        "Number_of_Stocks",
        "Total_Value",
        "Current_Value",
        "Share_Price"

    ]


    # ----------------------------------
    # STEP 2 — Clean Company Column
    # ----------------------------------

    df["Company_Name"] = (

        df["Company_Name"]
        .astype(str)
        .str.strip()

    )


    df = df[

        df["Company_Name"] != ""

    ]


    df = df[

        df["Company_Name"].str.lower() != "nan"

    ]


    # ----------------------------------
    # STEP 3 — Convert Date
    # ----------------------------------

    df["Date"] = pd.to_datetime(

        df["Date"],
        dayfirst=True,
        errors="coerce"

    )


    # ----------------------------------
    # STEP 4 — Numeric Clean
    # ----------------------------------

    numeric_cols = [

        "Number_of_Stocks",
        "Total_Value",
        "Current_Value",
        "Share_Price"

    ]


    for col in numeric_cols:

        df[col] = (

            df[col]
            .astype(str)
            .str.replace(",", "")
            .str.replace("₹", "")
            .str.strip()

        )

        df[col] = pd.to_numeric(

            df[col],
            errors="coerce"

        )


    df = df.reset_index(drop=True)


    print(
        "Overview cleaned shape:",
        df.shape
    )

    return df

def clean_all_investment(df):

    if df is None or df.empty:
        return df

    df = df.copy()

    rows = []

    for i in range(len(df)):

        row = df.iloc[i]

        asset = str(row.iloc[0]).strip()

        if asset == "" or asset == "nan":
            continue

        if "Total" in asset:
            continue

        value = row.iloc[1]

        rows.append([
            asset,
            value
        ])

    clean_df = pd.DataFrame(
        rows,
        columns=[
            "Asset",
            "Value"
        ]
    )

    clean_df = clean_numeric_columns(
        clean_df
    )

    return clean_df
# =====================================
# REBUILD HEADER FROM A GIVEN ROW
# =====================================

def rebuild_header(df: pd.DataFrame, header_row: int) -> pd.DataFrame:
    df = df.copy()

    headers = (
        df.iloc[header_row]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(" ", "_", regex=False)
    )

    # Make headers unique enough to avoid collisions
    cleaned_headers = []
    seen = {}

    for h in headers.tolist():
        h = h if h else "Unnamed"
        if h in seen:
            seen[h] += 1
            h = f"{h}_{seen[h]}"
        else:
            seen[h] = 0
        cleaned_headers.append(h)

    df.columns = cleaned_headers
    df = df.iloc[header_row + 1 :].reset_index(drop=True)
    df = df.dropna(how="all")
    df = drop_empty_columns(df)

    return df


# =====================================
# CLEAN KVP
# Raw:
# row 0 -> junk
# row 1 -> junk/header-like
# row 2 -> real header
# =====================================

def clean_kvp(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    df = df.copy()

    if len(df) < 3:
        return df

    # Row 2 is the real header
    df = rebuild_header(df, header_row=2)

    # Standardize expected columns if present
    # Keep only what exists, but in the intended order when possible
    expected = [
        "Investment_Date",
        "Maturity_Date",
        "Amount",
        "Principal",
        "Interest",
        "Matured",
        "Details",
        "Maturity_In_Days",
    ]

    available = list(df.columns)
    keep = available[: len(expected)]
    df = df.iloc[:, : len(keep)]
    df.columns = expected[: len(keep)]

    df = clean_numeric_columns(df)

    if "Investment_Date" in df.columns:
        df["Investment_Date"] = pd.to_datetime(
            df["Investment_Date"], dayfirst=True, errors="coerce"
        )

    if "Maturity_Date" in df.columns:
        df["Maturity_Date"] = pd.to_datetime(
            df["Maturity_Date"], dayfirst=True, errors="coerce"
        )

    return df


# =====================================
# CLEAN MUTUAL FUNDS
# Raw:
# row 0 -> summary
# row 1 -> header
# row 2+ -> data
# =====================================

def clean_mutualfunds(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    df = df.copy()

    if len(df) < 2:
        return df

    # Row 1 is the real header
    df = rebuild_header(df, header_row=1)

    expected = ["Fund", "Code", "Units", "NAV", "Value", "Date"]
    available = list(df.columns)
    keep = available[: len(expected)]
    df = df.iloc[:, : len(keep)]
    df.columns = expected[: len(keep)]

    df = clean_numeric_columns(df)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(
            df["Date"], dayfirst=True, errors="coerce"
        )

    return df


# =====================================
# CLEAN HISTORY
# =====================================

def clean_history(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    df = df.copy()
    df = clean_numeric_columns(df)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(
            df["Date"], dayfirst=True, errors="coerce"
        )
        df = df.dropna(subset=["Date"])

    return df


# =====================================
# CLEAN FDs / GENERIC TABLES
# =====================================
def clean_fds(df):

    if df is None or df.empty:
        return df

    df = df.copy()

    print("Cleaning FDs — preserve rows")

    # Use generic WITHOUT row drop logic
    df = drop_empty_columns(df)

    # Normalize headers only
    df.columns = (

        df.columns
        .astype(str)
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("/", "_")
        .str.replace("(", "")
        .str.replace(")", "")
        .str.replace("%", "Pct")

    )

    # Parse dates safely

    if "Investment_Date" in df.columns:

        df["Investment_Date"] = pd.to_datetime(
            df["Investment_Date"],
            dayfirst=True,
            errors="coerce"
        )

    if "Maturity_Date" in df.columns:

        df["Maturity_Date"] = pd.to_datetime(
            df["Maturity_Date"],
            dayfirst=True,
            errors="coerce"
        )

    print(
        "FD cleaned shape:",
        df.shape
    )

    return df

def clean_generic(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    df = df.copy()
    df = drop_empty_columns(df)
    df = clean_numeric_columns(df)
    return df


# =====================================
# MASTER CLEAN FUNCTION
# =====================================

def clean_portfolio(portfolio: dict) -> dict:
    cleaned = portfolio.copy()

    print("Cleaning KVP...")
    if "kvp" in cleaned and cleaned["kvp"] is not None:
        cleaned["kvp"] = clean_kvp(cleaned["kvp"])

    print("Cleaning MutualFunds...")
    if "MutualFunds" in cleaned and cleaned["MutualFunds"] is not None:
        cleaned["MutualFunds"] = clean_mutualfunds(cleaned["MutualFunds"])

    print("Cleaning History...")
    if "history_daily" in cleaned and cleaned["history_daily"] is not None:
        cleaned["history_daily"] = clean_history(cleaned["history_daily"])

    if "history_monthly" in cleaned and cleaned["history_monthly"] is not None:
        cleaned["history_monthly"] = clean_history(cleaned["history_monthly"])

    print("Cleaning FDs...")
    if "FDs" in cleaned and cleaned["FDs"] is not None:
        cleaned["FDs"] = clean_fds(cleaned["FDs"])

    # print("Cleaning Overview...")
    # if "Overview" in cleaned and cleaned["Overview"] is not None:
    #     cleaned["Overview"] = clean_generic(cleaned["Overview"])

    print("Cleaning Trades...")
    if "Trades" in cleaned and cleaned["Trades"] is not None:
        cleaned["Trades"] = clean_generic(cleaned["Trades"])

    print("Cleaning Overview...")

    if "Overview" in cleaned:
        cleaned["Overview"] = clean_overview(
            cleaned["Overview"]
        )


    print("Cleaning All_Investment...")

    if "All_Investment" in cleaned:
        cleaned["All_Investment"] = clean_all_investment(
            cleaned["All_Investment"]
        )
    return cleaned