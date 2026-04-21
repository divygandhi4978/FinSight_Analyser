import pandas as pd
import numpy as np
import requests
import re



# =====================================
# FIND MF TABLE
# =====================================

def find_mf_table(portfolio):

    for key in portfolio:

        name = key.lower()

        if any(x in name for x in [

            "mf",
            "mutual",
            "fund"

        ]):

            df = portfolio[key]

            if isinstance(df, pd.DataFrame):

                print("MF table found:", key)

                return df

    print("MF table NOT found")

    return None



# =====================================
# FIND SCHEME COLUMN
# =====================================

def find_scheme_column(df):

    possible_cols = [

        "Scheme_Code",
        "Scheme Code",
        "Code",
        "AMFI_Code",
        "Fund_Code"

    ]

    for col in df.columns:

        clean = col.replace(" ", "").lower()

        for p in possible_cols:

            if clean == p.replace(" ", "").lower():

                print("Scheme column:", col)

                return col

    print("Scheme column NOT found")

    return None



# =====================================
# CLEAN CODE
# =====================================

def clean_scheme_code(value):

    digits = re.sub(r"\D", "", str(value))

    if digits == "":
        return None

    if len(digits) > 6:
        digits = digits[:6]

    return digits



# =====================================
# FETCH NAV
# =====================================

def fetch_nav_data(code):

    url = f"https://api.mfapi.in/mf/{code}"

    try:

        r = requests.get(url, timeout=15)

        data = r.json()

        nav_list = data.get("data", [])

        df = pd.DataFrame(nav_list)

        if df.empty:
            return None


        df["date"] = pd.to_datetime(
            df["date"],
            dayfirst=True,
            errors="coerce"
        )

        df["nav"] = pd.to_numeric(
            df["nav"],
            errors="coerce"
        )

        df = df.dropna()

        df = df.sort_values("date")

        return df

    except Exception as e:

        print("NAV fetch failed:", code, e)

        return None



# =====================================
# CALCULATE FUND METRICS
# =====================================

def calculate_metrics(nav_df):

    nav_df["Return"] = nav_df["nav"].pct_change()

    nav_df["Peak"] = nav_df["nav"].cummax()

    nav_df["Drawdown"] = (

        nav_df["nav"]
        - nav_df["Peak"]

    ) / nav_df["Peak"]


    # Rolling Returns

    for w in [30, 90, 180]:

        if len(nav_df) > w:

            nav_df[f"Rolling_{w}"] = (

                nav_df["nav"]

                .pct_change(w)

            )


    # CAGR

    start_val = nav_df["nav"].iloc[0]

    end_val = nav_df["nav"].iloc[-1]

    days = (

        nav_df["date"].iloc[-1]
        - nav_df["date"].iloc[0]

    ).days


    if days > 0:

        years = days / 365

        cagr = (

            (end_val / start_val)

            ** (1 / years)

        ) - 1

    else:

        cagr = None


    # Volatility

    volatility = (

        nav_df["Return"].std()

        * np.sqrt(252)

    )


    # Max Drawdown

    max_dd = nav_df["Drawdown"].min()


    return nav_df, cagr, volatility, max_dd



# =====================================
# MAIN ENGINE
# =====================================

def run_mf_engine(portfolio):

    mf_df = find_mf_table(portfolio)

    if mf_df is None:
        return {}


    code_col = find_scheme_column(mf_df)

    if code_col is None:
        return {}


    fund_data = {}

    allocation_df = mf_df.copy()

    name_col = mf_df.columns[0]


    portfolio_metrics = []


    for i, row in mf_df.iterrows():

        raw_code = row[code_col]

        scheme_code = clean_scheme_code(raw_code)

        if scheme_code is None:
            continue


        fund_name = str(row[name_col])


        print("Fetching:", fund_name, scheme_code)


        nav_df = fetch_nav_data(scheme_code)

        if nav_df is None:
            continue


        nav_df, cagr, vol, dd = calculate_metrics(nav_df)


        fund_data[fund_name] = nav_df


        portfolio_metrics.append({

            "Fund": fund_name,
            "CAGR": cagr,
            "Volatility": vol,
            "Max_Drawdown": dd

        })


    if len(fund_data) == 0:

        print("No NAV fetched")

        return {}


    metrics_df = pd.DataFrame(portfolio_metrics)


    print("Funds loaded:", len(fund_data))


    return {

        "allocation": allocation_df,
        "fund_nav": fund_data,
        "metrics": metrics_df

    }