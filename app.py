import streamlit as st
import pandas as pd
from pathlib import Path
import os
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
import time

st.set_page_config(page_title="My Village Digital Portal", page_icon="🏡", layout="wide")
BASE_DIR = Path(__file__).parent


# ---------------- FILE SETUP (FIXED PATH STORAGE) ----------------
def ensure_file(file, cols):
    path = BASE_DIR / file
    if not path.exists():
        pd.DataFrame(columns=cols).to_csv(path, index=False)


def load(file):
    path = BASE_DIR / file
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


# ---------------- PREMIUM + MOBILE UI ----------------
st.markdown("""
<style>
.block-container{max-width:700px;margin:auto;padding-top:1rem;}
.stApp {background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:white;}
[data-testid="stSidebar"]{background: linear-gradient(#1f4037,#99f2c8);}
label,p,span {color:white !important;}
h1,h2,h3 {color:#ffd369;}

.stButton>button {
background:linear-gradient(90deg,#ff7e5f,#feb47b);
color:white;border-radius:10px;border:none;
}

/* SLIDER */
.slider-container{position:relative;width:100%;border-radius:15px;overflow:hidden}
.slide{display:none;width:100%;animation:fade 1.5s}
@keyframes fade {from{opacity:.4} to{opacity:1}}
.slider-text{
position:absolute;top:10px;left:20px;
background:rgba(0,0,0,0.6);
padding:10px 20px;border-radius:10px;color:white;font-size:22px;
}

/* ANNOUNCEMENT TICKER */
.ticker{
width:100%;
overflow:hidden;
white-space:nowrap;
box-sizing:border-box;
}
.ticker span{
display:inline-block;
padding-left:100%;
animation:ticker 15s linear infinite;
font-size:18px;
color:#ffd369;
}
@keyframes ticker{
0%{transform:translate(0,0);}
100%{transform:translate(-100%,0);}
}
</style>
""", unsafe_allow_html=True)


# ---------------- CREATE FILES ----------------
ensure_file("families.csv",["Family_ID","Head_of_Family","Address"])
ensure_file("pupils.csv",["Name","Family_ID","Relation","Age","Voter_ID"])
ensure_file("places.csv",["Name","Type","Latitude","Longitude"])
ensure_file("team.csv",["Name","Role"])
ensure_file("gallery.csv",["Image"])
ensure_file("dashboard_media.csv",["Image","Caption"])
ensure_file("leagues.csv",["Sport","Season","Winner","Runner"])
ensure_file("ward_ranges.csv",["Ward","Start","End"])


# ---------------- REAL WARD DETECTION ----------------
def detect_ward(voter_id):
    if pd.isna(voter_id):
        return "Unknown"

    voter_id=str(voter_id)

    # extract numbers from voter id
    number="".join(filter(str.isdigit, voter_id))
    if number=="":
        return "Unknown"

    number=int(number)
    ward_ranges=load("ward_ranges.csv")

    for _,row in ward_ranges.iterrows():
        try:
            if int(row["Start"]) <= number <= int(row["End"]):
                return int(row["Ward"])
        except:
            pass

    return "Unknown"


# ---------------- LOGIN ----------------
if "role" not in st.session_state:
    st.session_state.role=None

st.sidebar.title("🔐 Login")
login_type=st.sidebar.selectbox("Login As",["User","Admin"])

if login_type=="User":
    name=st.sidebar.text_input("Enter Name")
    if st.sidebar.button("Enter"):
        st.session_state.role="user"
        st.session_state.username=name

if login_type=="Admin":
    aid=st.sidebar.text_input("Admin ID")
    pwd=st.sidebar.text_input("Password",type="password")
    if st.sidebar.button("Login"):
        if aid=="admin" and pwd=="admin123":
            st.session_state.role="admin"
            st.session_state.username="Administrator"
        else:
            st.sidebar.error("Wrong Credentials")

if st.session_state.role is None:
    st.stop()


# ---------------- HEADER ----------------
st.markdown(f"""
<div style='padding:15px;border-radius:10px;background:linear-gradient(90deg,#4facfe,#00f2fe);text-align:center'>
<h3>👋 Welcome {st.session_state.username}</h3>
</div>
""",unsafe_allow_html=True)


# ANNOUNCEMENT
st.markdown("""
<div class="ticker">
<span>📢 Welcome to Sarvapoor Kothapalle Village Digital Portal • Latest Updates Available • Village Development News</span>
</div>
""", unsafe_allow_html=True)


# ---------------- MENU ----------------
with st.sidebar:
    selected=option_menu(
        "Village Portal",
        ["Dashboard","Families","Pupils","Village Team","Places",
         "Village Leagues","Village Gallery","Dashboard Media","Ward Settings"],
        icons=["house","people","person","person-workspace","geo",
               "trophy","image","camera","gear"]
    )


# ---------------- LOAD DATA ----------------
families=load("families.csv")
pupils=load("pupils.csv")
places=load("places.csv")
team=load("team.csv")
gallery=load("gallery.csv")
dash_media=load("dashboard_media.csv")
leagues=load("leagues.csv")


# ---------------- FAST SEARCH ----------------
@st.cache_data
def prepare_search_data(df):
    return df.astype(str).apply(lambda x: x.str.lower())

pupils_fast=prepare_search_data(pupils)
families_fast=prepare_search_data(families)
places_fast=prepare_search_data(places)
team_fast=prepare_search_data(team)
leagues_fast=prepare_search_data(leagues)


# ====================================================
# DASHBOARD
# ====================================================
if selected=="Dashboard":

    st.title("🏡 Village Dashboard")
    st.markdown("## Welcome to SARVAPOOR KOTHAPALLE Village Digital Portal")

    c1,c2,c3,c4=st.columns(4)
    c1.metric("Families",len(families))
    c2.metric("Members",len(pupils))
    c3.metric("Places",len(places))
    c4.metric("Team",len(team))

    st.divider()

    st.subheader("🔍 Smart Search")

    search_pool=pd.concat([
        pupils["Name"],
        families["Head_of_Family"],
        places["Name"],
        team["Name"],
        leagues["Sport"]
    ]).dropna().unique()

    query=st.selectbox("Search anything",[""]+list(search_pool))

    if query:
        q=query.lower()
        found=False

        person=pupils[pupils_fast.apply(lambda x:x.str.contains(q)).any(axis=1)]
        if not person.empty:
            st.success("Person Found")
            st.dataframe(person)

            voter=person.iloc[0]["Voter_ID"]
            ward=detect_ward(voter)

            st.subheader("Detected Ward")
            st.info(f"Ward: {ward}")

            fid=person.iloc[0]["Family_ID"]
            st.subheader("Family Head Details")
            st.dataframe(families[families["Family_ID"]==fid])

            st.subheader("Full Family Members")
            st.dataframe(pupils[pupils["Family_ID"]==fid])

            found=True

        if query.isdigit():
            ward_number=int(query)
            pupils["Detected_Ward"]=pupils["Voter_ID"].apply(detect_ward)
            ward_members=pupils[pupils["Detected_Ward"]==ward_number]

            if not ward_members.empty:
                st.success(f"Ward {ward_number} Members")
                st.dataframe(ward_members)
                found=True

        if not found:
            st.error("Data Not Found")

    st.divider()

    st.subheader("🗺 Village Map")
    m=folium.Map(location=[18.678054,78.961130],zoom_start=15)
    folium.Marker([18.678054,78.961130],popup="SARVAPOOR KOTHAPALLE").add_to(m)
    st_folium(m,width=700)


# ====================================================
# ADMIN CONTROL
# ====================================================
def admin_controls(df,file,cols,title):
    st.header(title)
    st.dataframe(df)

    if st.session_state.role!="admin":
        return

    file_path=BASE_DIR / file

    st.markdown("### Admin Panel")
    tab1,tab2,tab3=st.tabs(["Add","Edit","Delete"])

    with tab1:
        data={}
        for c in cols:
            data[c]=st.text_input(f"Enter {c}",key=f"{title}_{c}")
        if st.button("Add Record",key=f"{title}_add"):
            pd.DataFrame([data]).to_csv(file_path,mode="a",header=not file_path.exists(),index=False)
            st.success("Added — Refresh")

    with tab2:
        if len(df)>0:
            idx=st.number_input("Row",0,len(df)-1,key=f"{title}_row")
            new={}
            for c in cols:
                new[c]=st.text_input(f"New {c}",df.iloc[idx][c],key=f"{title}_edit_{c}")
            if st.button("Update Record",key=f"{title}_update"):
                df.loc[idx]=list(new.values())
                df.to_csv(file_path,index=False)
                st.success("Updated")

    with tab3:
        if len(df)>0:
            d=st.number_input("Delete Row",0,len(df)-1,key=f"{title}_delete_row")
            if st.button("Delete Record",key=f"{title}_delete"):
                df=df.drop(d)
                df.to_csv(file_path,index=False)
                st.success("Deleted")


if selected=="Families":
    admin_controls(families,"families.csv",["Family_ID","Head_of_Family","Address"],"Families")

if selected=="Pupils":
    admin_controls(pupils,"pupils.csv",["Name","Family_ID","Relation","Age","Voter_ID"],"Pupils")

if selected=="Village Team":
    admin_controls(team,"team.csv",["Name","Role"],"Village Team")

if selected=="Places":
    admin_controls(places,"places.csv",["Name","Type","Latitude","Longitude"],"Village Places")

if selected=="Village Leagues":
    admin_controls(leagues,"leagues.csv",["Sport","Season","Winner","Runner"],"Village Leagues")


# ====================================================
# WARD SETTINGS
# ====================================================
if selected=="Ward Settings":

    ward_ranges=load("ward_ranges.csv")

    st.header("Ward Range Management")
    st.dataframe(ward_ranges)

    if st.session_state.role!="admin":
        st.warning("Only admin can manage ward ranges")
        st.stop()

    ward=st.number_input("Ward Number",step=1)
    start=st.number_input("Start Range",step=1)
    end=st.number_input("End Range",step=1)

    if st.button("Save Range"):
        new=pd.DataFrame([[ward,start,end]],columns=["Ward","Start","End"])
        ward_ranges=pd.concat([ward_ranges,new],ignore_index=True)
        ward_ranges.to_csv(BASE_DIR/"ward_ranges.csv",index=False)
        st.success("Saved")

    if len(ward_ranges)>0:
        idx=st.number_input("Row to Delete",0,len(ward_ranges)-1)
        if st.button("Delete Range"):
            ward_ranges.drop(idx,inplace=True)
            ward_ranges.to_csv(BASE_DIR/"ward_ranges.csv",index=False)
            st.success("Deleted")