import pandas as pd
import numpy as np



# =====================================
# FIND MONTHLY OR DAILY HISTORY
# =====================================

def get_history_table(portfolio):

    # Try monthly first

    for key in portfolio:

        if "monthly" in key.lower():

            df = portfolio[key]

            if isinstance(df, pd.DataFrame):

                print("Using monthly history:", key)

                return df.copy()


    # fallback daily

    for key in portfolio:

        if "daily" in key.lower():

            df = portfolio[key]

            if isinstance(df, pd.DataFrame):

                print("Using daily history:", key)

                return df.copy()

    print("No history found")

    return None



# =====================================
# DETECT DATE COLUMN
# =====================================

def detect_date_column(df):

    for col in df.columns:

        if "date" in col.lower():

            return col

    return df.columns[0]



# =====================================
# DETECT VALUE COLUMN
# =====================================

def detect_value_column(df):

    for col in df.columns:

        if "value" in col.lower():

            return col

    return df.columns[1]



# =====================================
# PREPARE DATA
# =====================================

def prepare_history(df):

    df = df.copy()

    date_col = detect_date_column(df)

    value_col = detect_value_column(df)


    # robust parsing

    df["Date"] = pd.to_datetime(

        df[date_col],

        dayfirst=True,

        errors="coerce"

    )


    df["Total_Value"] = pd.to_numeric(

        df[value_col],

        errors="coerce"

    )


    df = df.dropna()

    df = df.sort_values("Date")


    if len(df) < 3:

        print("Not enough data rows")

        return None


    return df[["Date", "Total_Value"]]



# =====================================
# RETURNS
# =====================================

def calculate_returns(df):

    df["Monthly_Return"] = (

        df["Total_Value"]

        .pct_change()

    )

    return df



# =====================================
# DRAWDOWN
# =====================================

def calculate_drawdown(df):

    df["Peak"] = (

        df["Total_Value"]

        .cummax()

    )

    df["Drawdown"] = (

        df["Total_Value"]

        - df["Peak"]

    ) / df["Peak"]

    return df



# =====================================
# DRIFT
# =====================================

def calculate_drift(df):

    df["MoM_Change"] = (

        df["Total_Value"]

        .pct_change()

    )

    return df



# =====================================
# RISK METRICS
# =====================================

def calculate_risk(df):

    r = df["Monthly_Return"].dropna()

    if len(r) < 2:

        print("Return series too short")

        return {

            "Volatility": np.nan,

            "VaR_95": np.nan,

            "Max_Drawdown": df["Drawdown"].min()

        }


    volatility = (

        r.std()

        * np.sqrt(12)

    )

    var_95 = np.percentile(

        r,

        5

    )

    max_dd = df["Drawdown"].min()


    return {

        "Volatility": volatility,

        "VaR_95": var_95,

        "Max_Drawdown": max_dd

    }



# =====================================
# CONCENTRATION
# =====================================

def calculate_concentration(portfolio):

    df = portfolio.get("Overview")

    if df is None:

        return None


    df = df.copy()

    total = df["Current_Value"].sum()

    df["Weight"] = (

        df["Current_Value"]

        / total

    )


    df = df.sort_values(

        "Weight",

        ascending=False

    )


    top5 = df.head(5)["Weight"].sum()

    hhi = (df["Weight"] ** 2).sum()


    return {

        "Top5_Weight": top5,

        "HHI": hhi,

        "weights_df": df

    }



# =====================================
# MAIN ENGINE
# =====================================

def run_research_engine(portfolio):

    history_raw = get_history_table(

        portfolio

    )

    if history_raw is None:

        return {}


    history = prepare_history(

        history_raw

    )

    if history is None:

        return {}


    history = calculate_returns(

        history

    )

    history = calculate_drawdown(

        history

    )

    history = calculate_drift(

        history

    )


    risk = calculate_risk(

        history

    )


    concentration = calculate_concentration(

        portfolio

    )


    return {

        "monthly": history,

        "risk": risk,

        "concentration": concentration,

        "drift": history

    }