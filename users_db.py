
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

# ---------------- MOBILE APP STYLE + PREMIUM UI ----------------
st.markdown("""
<style>

/* MOBILE STYLE */
.block-container{
max-width:700px;
margin:auto;
padding-top:1rem;
}

/* Background */
.stApp {
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
color:white;
}

/* Sidebar */
[data-testid="stSidebar"]{
background: linear-gradient(#1f4037,#99f2c8);
}

/* Text */
label,p,span {color:white !important;}
h1,h2,h3 {color:#ffd369;}

/* Buttons */
.stButton>button {
background:linear-gradient(90deg,#ff7e5f,#feb47b);
color:white;border-radius:10px;border:none;
}

/* Cards */
.metric-container{
background:rgba(255,255,255,0.1);
padding:15px;border-radius:12px;
}

/* Input */
.stTextInput>div>div>input{
border-radius:10px;
}

/* Mobile feel */
@media (max-width:768px){
.block-container{padding:10px;}
}

</style>
""", unsafe_allow_html=True)

# ---------------- FILE SETUP ----------------
def ensure_file(file, cols):
    if not os.path.exists(file):
        pd.DataFrame(columns=cols).to_csv(file,index=False)

ensure_file("families.csv",["Family_ID","Head_of_Family","Address"])
ensure_file("pupils.csv",["Name","Family_ID","Relation","Age","Voter_ID"])
ensure_file("places.csv",["Name","Type","Latitude","Longitude"])
ensure_file("team.csv",["Name","Role"])
ensure_file("gallery.csv",["Image"])
ensure_file("dashboard_media.csv",["Image","Caption"])

def load(file):
    return pd.read_csv(file)

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

st.markdown("""
<marquee style='font-size:20px;color:yellow'>
Welcome to SARVAPOOR KOTHAPALLE Digital Portal — New updates & announcements available here
</marquee>
""",unsafe_allow_html=True)

# ---------------- MENU ----------------
with st.sidebar:
    selected=option_menu(
        "Village Portal",
        ["Dashboard","Families","Pupils","Village Team","Places","Village Gallery","Dashboard Media"],
        icons=["house","people","person","person-workspace","geo","image","camera"]
    )

families=load("families.csv")
pupils=load("pupils.csv")
places=load("places.csv")
team=load("team.csv")
gallery=load("gallery.csv")
dash_media=load("dashboard_media.csv")

# ====================================================
# FAST SEARCH INDEX (NEW)
# ====================================================
@st.cache_data
def build_search_index(families,pupils,places,team):
    return {
        "families":families.astype(str),
        "pupils":pupils.astype(str),
        "places":places.astype(str),
        "team":team.astype(str)
    }

search_index=build_search_index(families,pupils,places,team)

# ====================================================
# DASHBOARD
# ====================================================
if selected=="Dashboard":

    st.title("🏡 Village Dashboard")

    # -------- DASHBOARD IMAGE SLIDER --------
    st.subheader("🌄 Village Highlights")
    for _,r in dash_media.iterrows():
        if os.path.exists(r["Image"]):
            st.image(r["Image"],use_column_width=True)
            st.caption(r["Caption"])

    st.divider()

    c1,c2,c3,c4=st.columns(4)
    c1.metric("Families",len(families))
    c2.metric("Members",len(pupils))
    c3.metric("Places",len(places))
    c4.metric("Team",len(team))

    st.divider()

    # -------- FAST GLOBAL SEARCH --------
    st.subheader("🌍 Smart Global Search")

    query=st.text_input("Search anything (name, place, family, team...)")

    if query:
        found=False

        # PUPIL SEARCH + FAMILY DETAILS
        res=search_index["pupils"][search_index["pupils"].apply(
            lambda x:x.str.contains(query,case=False)).any(axis=1)]

        if not res.empty:
            found=True
            st.success("👤 Person Found")
            st.dataframe(res)

            for _,row in res.iterrows():
                fam=families[families["Family_ID"]==row["Family_ID"]]
                if not fam.empty:
                    st.info("👨‍👩‍👧 Family Details")
                    st.write("Family Head:",fam.iloc[0]["Head_of_Family"])
                    st.write("Address:",fam.iloc[0]["Address"])
                    st.subheader("Full Family Members")
                    st.dataframe(pupils[pupils["Family_ID"]==row["Family_ID"]])

        # OTHER TABLES SEARCH
        for name,data in search_index.items():
            r=data[data.apply(lambda x:x.str.contains(query,case=False)).any(axis=1)]
            if not r.empty and name!="pupils":
                st.success(f"{name.title()} Results")
                st.dataframe(r)
                found=True

        if not found:
            st.error("Data Not Found")

    st.divider()

    # -------- MAP WITH VILLAGE OUTLINE (NEW) --------
    st.subheader("🗺 Village Map")

    main_lat=18.678054
    main_lon=78.961130

    m=folium.Map(location=[main_lat,main_lon],zoom_start=15)

    # Village center marker
    folium.Marker([main_lat,main_lon],
        popup="SARVAPOOR KOTHAPALLE",
        icon=folium.Icon(color="red")).add_to(m)

    # Village boundary outline (you can change coordinates)
    village_boundary=[
        [18.6795,78.9590],
        [18.6805,78.9620],
        [18.6775,78.9640],
        [18.6765,78.9605]
    ]

    folium.Polygon(
        locations=village_boundary,
        color="blue",
        fill=True,
        fill_opacity=0.2,
        popup="Sarvapoor Kothapalle Boundary"
    ).add_to(m)

    # places markers
    for _,r in places.iterrows():
        try:
            folium.Marker([float(r["Latitude"]),float(r["Longitude"])],
                          popup=r["Name"]).add_to(m)
        except: pass

    st_folium(m,width=700)

# ====================================================
# ADMIN CONTROL PANEL (UNCHANGED)
# ====================================================
def admin_controls(df,file,cols,title):

    st.header(title)
    st.dataframe(df)

    if st.session_state.role!="admin":
        return

    st.markdown("### 🛠 Admin Panel")

    tab1,tab2,tab3=st.tabs(["Add","Edit","Delete"])

    with tab1:
        data={}
        for c in cols:
            data[c]=st.text_input(f"Enter {c}")
        if st.button("Add Record"):
            pd.DataFrame([data]).to_csv(file,mode="a",header=False,index=False)
            st.success("Added — Refresh")

    with tab2:
        if len(df)>0:
            idx=st.number_input("Row Number",0,len(df)-1)
            new={}
            for c in cols:
                new[c]=st.text_input(f"New {c}",df.iloc[idx][c])
            if st.button("Update Record"):
                df.loc[idx]=list(new.values())
                df.to_csv(file,index=False)
                st.success("Updated")

    with tab3:
        if len(df)>0:
            d=st.number_input("Row Number to Delete",0,len(df)-1)
            confirm=st.checkbox("Confirm Delete")
            if st.button("Delete Record") and confirm:
                df=df.drop(d)
                df.to_csv(file,index=False)
                st.success("Deleted")

# ====================================================
# DATA SECTIONS
# ====================================================
if selected=="Families":
    admin_controls(families,"families.csv",
        ["Family_ID","Head_of_Family","Address"],"Families")

if selected=="Pupils":
    admin_controls(pupils,"pupils.csv",
        ["Name","Family_ID","Relation","Age","Voter_ID"],"Pupils")

if selected=="Village Team":
    admin_controls(team,"team.csv",
        ["Name","Role"],"Village Team")

if selected=="Places":
    admin_controls(places,"places.csv",
        ["Name","Type","Latitude","Longitude"],"Village Places")

# ====================================================
# GALLERY
# ====================================================
if selected=="Village Gallery":

    st.header("Village Memories")

    if st.session_state.role=="admin":
        img=st.file_uploader("Upload Image",type=["jpg","png"])
        if img:
            os.makedirs("gallery",exist_ok=True)
            path=f"gallery/{time.time()}.jpg"
            with open(path,"wb") as f: f.write(img.read())
            pd.DataFrame([[path]],columns=["Image"]).to_csv("gallery.csv",mode="a",header=False,index=False)
            st.success("Uploaded")

    for _,r in gallery.iterrows():
        if os.path.exists(r["Image"]):
            st.image(r["Image"],width=300)

# ====================================================
# DASHBOARD MEDIA CONTROL
# ====================================================
if selected=="Dashboard Media":

    st.header("Dashboard Images & Captions")

    if st.session_state.role=="admin":
        img=st.file_uploader("Upload Dashboard Image",type=["jpg","png"])
        caption=st.text_input("Caption")
        if st.button("Upload"):
            os.makedirs("dashboard_media",exist_ok=True)
            path=f"dashboard_media/{time.time()}.jpg"
            with open(path,"wb") as f: f.write(img.read())
            pd.DataFrame([[path,caption]],columns=["Image","Caption"]).to_csv("dashboard_media.csv",mode="a",header=False,index=False)
            st.success("Added to Dashboard")
