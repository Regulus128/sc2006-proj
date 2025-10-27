import os, re, numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point

TARGET_CRS = 3414  # Singapore SVY21 (meters)
os.makedirs("content/out", exist_ok=True)

PATH_SUBZONES = "content/MasterPlan2019SubzoneBoundaryNoSeaGEOJSON.geojson"
PATH_MRT      = "content/LTAMRTStationExitGEOJSON.geojson"
PATH_HAWKER   = "content/HawkerCentresGEOJSON.geojson"
PATH_POP      = "content/ResidentPopulationbyPlanningAreaSubzoneofResidenceAgeGroupandSexCensusofPopulation2020.csv"

BUS_GPKG  = "content/out/bus_stops.gpkg"
BUS_LAYER = "bus_stops"


def kernel(dist_m, lam, kind="exp"):
    t = np.clip(dist_m / lam, 0, None)
    return np.exp(-t) if kind == "exp" else np.exp(-(t**2)/2)

def robust_z(x):
    x = np.asarray(x, float)
    med = np.median(x)
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    if iqr == 0:
        sd = np.std(x)
        iqr = sd if sd > 0 else 1.0
    return (x - med) / iqr

def xy_from_gdf(gdf):
    return np.vstack([gdf.geometry.x.to_numpy(), gdf.geometry.y.to_numpy()]).T

def pairwise_dist(A, B):
    A2 = np.sum(A**2, axis=1)[:, None]
    B2 = np.sum(B**2, axis=1)[None, :]
    D2 = np.clip(A2 + B2 - 2 * A @ B.T, 0, None)
    return np.sqrt(D2)

def compute_hawker_opportunity(
    eval_units_gdf, demand_gdf, supply_gdf, mrt_gdf=None, bus_gdf=None,
    *, pop_col="population", cap_col="capacity",
    mrt_w_col=None, bus_w_col=None,
    kernel_kind="exp",
    lambda_D=700, lambda_S=700, lambda_C=700, lambda_M=900, lambda_B=500,
    w_D=0.5, w_S=0.3, w_A=0.2, beta_MRT=1.0, beta_BUS=1.0
):
    # evaluation points = centroids if polygons
    eval_pts = (eval_units_gdf.geometry.centroid
                if eval_units_gdf.geom_type.isin(["Polygon","MultiPolygon"]).any()
                else eval_units_gdf.geometry)
    XY_i = xy_from_gdf(gpd.GeoDataFrame(geometry=eval_pts, crs=eval_units_gdf.crs))

    # coords
    XY_u = xy_from_gdf(demand_gdf)
    XY_j = xy_from_gdf(supply_gdf)

    P_u = demand_gdf[pop_col].to_numpy(float)
    C_j = supply_gdf[cap_col].to_numpy(float)

    # Demand
    D_ui = pairwise_dist(XY_u, XY_i)
    Dem_i = (P_u[:,None] * kernel(D_ui, lambda_D, kind=kernel_kind)).sum(axis=0)

    # Supply (competing adjusted)
    D_uj = pairwise_dist(XY_u, XY_j)
    denom_j = (P_u[:,None] * kernel(D_uj, lambda_C, kind=kernel_kind)).sum(axis=0)
    denom_j = np.where(denom_j<=0, 1.0, denom_j)

    D_ji = pairwise_dist(XY_j, XY_i)
    Sup_eff_i = ((C_j/denom_j)[:,None] * kernel(D_ji, lambda_S, kind=kernel_kind)).sum(axis=0)

    # Accessibility
    Acc_i = np.zeros_like(Dem_i)
    if mrt_gdf is not None and len(mrt_gdf):
        XY_m = xy_from_gdf(mrt_gdf)
        w_m = mrt_gdf[mrt_w_col].to_numpy(float) if mrt_w_col and mrt_w_col in mrt_gdf.columns else np.ones(len(mrt_gdf))
        D_mi = pairwise_dist(XY_m, XY_i)
        Acc_i += beta_MRT * (w_m[:,None] * kernel(D_mi, lambda_M, kind=kernel_kind)).sum(axis=0)
    if bus_gdf is not None and len(bus_gdf):
        XY_b = xy_from_gdf(bus_gdf)
        w_b = bus_gdf[bus_w_col].to_numpy(float) if bus_w_col and bus_w_col in bus_gdf.columns else np.ones(len(bus_gdf))
        D_bi = pairwise_dist(XY_b, XY_i)
        Acc_i += beta_BUS * (w_b[:,None] * kernel(D_bi, lambda_B, kind=kernel_kind)).sum(axis=0)

    Z_D, Z_S, Z_A = robust_z(Dem_i), robust_z(Sup_eff_i), robust_z(Acc_i)
    H_i = w_D*Z_D - w_S*Z_S + w_A*Z_A

    out = eval_units_gdf.copy()
    out["Dem"]   = Dem_i
    out["Sup"]   = Sup_eff_i
    out["Acc"]   = Acc_i
    out["Z_Dem"] = Z_D
    out["Z_Sup"] = Z_S
    out["Z_Acc"] = Z_A
    out["H_score"] = H_i
    return out

subzones = gpd.read_file(PATH_SUBZONES)
if subzones.crs is None:  # just in case
    subzones.set_crs(4326, inplace=True)
subzones = subzones.to_crs(TARGET_CRS)

# Identify the subzone name column to show later
subzone_name_col = next((c for c in subzones.columns if re.search("subzone", c, re.I)), subzones.columns[0])

print(subzones.crs)
print(subzones.shape)
subzones.head(2)

hawker = gpd.read_file(PATH_HAWKER)
if hawker.crs is None:
    hawker.set_crs(4326, inplace=True)  # NEA geojson typically WGS84
hawker = hawker.to_crs(TARGET_CRS)

# Parse 'Description' HTML to get NAME/STATUS if present (optional)
if "Description" in hawker.columns:
    def parse_field(html, key):
        m = re.search(fr"<th[^>]*>{key}</th>\s*<td[^>]*>(.*?)</td>", str(html), flags=re.I|re.S)
        return re.sub("<.*?>","",m.group(1)).strip() if m else None
    hawker["NAME_EXTRACT"] = hawker["Description"].apply(lambda h: parse_field(h, "NAME") or parse_field(h, "NAME OF HAWKER CENTRE"))
    hawker["STATUS"] = hawker["Description"].apply(lambda h: parse_field(h, "STATUS"))

# capacity proxy
if "capacity" not in hawker.columns:
    hawker["capacity"] = 1.0

print(hawker.crs, hawker.shape)
hawker.head(2)

mrt = gpd.read_file(PATH_MRT)
if mrt.crs is None:
    mrt.set_crs(4326, inplace=True)
mrt = mrt.to_crs(TARGET_CRS)

print(mrt.crs, mrt.shape)
mrt.head(2)



# --- Bus Stops via LTA DataMall API (geocoded points) ---
# NOTE: Keep your key secret. For Colab, consider using an env var instead of hardcoding.
# e.g., in a cell:  import os; os.environ["LTA_ACCOUNT_KEY"] = "xxxxx"
# then here: ACCOUNT_KEY = os.environ["LTA_ACCOUNT_KEY"]

import os, requests, pandas as pd, geopandas as gpd
from shapely.geometry import Point


# Load into `bus` for the scorer
try:
    if BUS_LAYER:
        bus = gpd.read_file(BUS_GPKG, layer=BUS_LAYER).to_crs(TARGET_CRS)
    else:
        bus = gpd.read_file(BUS_GPKG).to_crs(TARGET_CRS)
    print("Bus stops loaded:", bus.shape)
except Exception as e:
    print("Bus load failed, proceeding without bus:", e)
    bus = None

import pandas as pd, re
pop_df = pd.read_csv(PATH_POP)

# 1) Normalize name column
df = pop_df.rename(columns={"Number":"name"}).copy()
df["name"] = df["name"].str.strip()

# 2) Identify row types
is_grand_total = df["name"].str.fullmatch(r"Total", case=False, na=False)
is_pa_total    = df["name"].str.contains(r"\s-\sTotal$", na=False)  # e.g., "Ang Mo Kio - Total"

# 3) Extract planning area from "PA - Total" rows and forward-fill
df["pa_marker"] = df["name"].where(is_pa_total).str.replace(r"\s-\sTotal$","", regex=True)
df["planning_area"] = df["pa_marker"].ffill()

# 4) Keep only **subzone** rows (exclude grand total + "PA - Total")
sub_df = df[~is_grand_total & ~is_pa_total].copy()

# 5) Rename to standard keys + clean numeric
sub_df["subzone"] = sub_df["name"]

# clean "Total_Total": remove commas/spaces, turn '-' to NaN, then to 0, then int
pop_clean = (
    sub_df["Total_Total"]
      .astype(str)
      .str.replace(",", "", regex=False)
      .str.strip()
      .replace({"-": np.nan, "": np.nan})
)

sub_df["population"] = pd.to_numeric(pop_clean, errors="coerce").fillna(0).astype("int64")

pop_tot = sub_df[["planning_area", "subzone", "population"]].reset_index(drop=True)

print(pop_tot.head(8))
print("Rows kept (subzones):", len(pop_tot))
print("Zero-pop rows (check if expected):", (pop_tot["population"]==0).sum())

# --- Join population to URA subzone polygons ---
poly_cols_lower = {c.lower(): c for c in subzones.columns}
subzone_name_col = next((c for c in subzones.columns if re.search("subzone", c, re.I)), subzones.columns[0])

if "planning_area" in poly_cols_lower:
    subzones_joinkey = subzones.rename(columns={
        poly_cols_lower["planning_area"]: "planning_area",
        subzone_name_col: "subzone"
    })
    join_on = ["planning_area","subzone"]
else:
    subzones_joinkey = subzones.rename(columns={subzone_name_col:"subzone"})
    join_on = ["subzone"]

sub_pop = subzones_joinkey.merge(pop_tot, on=join_on, how="left", validate="one_to_one")
sub_pop["population"] = sub_pop["population"].fillna(0)

# Check for unmatched subzones (optional)
unmatched = subzones_joinkey.loc[~subzones_joinkey["subzone"].isin(pop_tot["subzone"])]
print("Unmatched polygons:", len(unmatched))
print(unmatched.head(10))

# --- Create demand points (centroids) ---
demand_pts = sub_pop.copy()
demand_pts["geometry"] = demand_pts.geometry.centroid
demand_pts = demand_pts.set_geometry("geometry").to_crs(TARGET_CRS)
demand_pts = demand_pts[["population","geometry"]]

print("Demand points ready:", demand_pts.shape)
demand_pts.head(3)

result = compute_hawker_opportunity(
    eval_units_gdf=subzones,
    demand_gdf=demand_pts,
    supply_gdf=hawker,
    mrt_gdf=mrt,
    bus_gdf=bus,   # None if bus not loaded
    pop_col="population",
    cap_col="capacity",
    kernel_kind="exp",
    lambda_D=700, lambda_S=700, lambda_C=700, lambda_M=900, lambda_B=500,
    w_D=0.5, w_S=0.3, w_A=0.2,
    beta_MRT=1.0, beta_BUS=1.0
)

print("Scoring done:", len(result))
result[[subzone_name_col, "H_score","Z_Dem","Z_Sup","Z_Acc"]].sort_values("H_score", ascending=False).head(10)

# Save results in both GPKG and GeoJSON
try:
    result.to_file("content/out/hawker_opportunity.gpkg", layer="score", driver="GPKG")
    print("Saved GeoPackage → content/out/hawker_opportunity.gpkg")
except Exception as e:
    print("⚠️ GPKG save failed:", e)

result.to_file("content/out/hawker_opportunity.geojson", driver="GeoJSON")
print("Saved GeoJSON → content/out/hawker_opportunity.geojson")

ax = result.plot(column="H_score", legend=True, figsize=(7,7), linewidth=0.2, edgecolor="gray")
ax.set_title("Hawker Opportunity Score (higher = better candidate)")
ax.set_axis_off()
import matplotlib.pyplot as plt
plt.show()

