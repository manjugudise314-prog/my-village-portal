import streamlit as st
import pandas as pd
from pathlib import Path
import os
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
import base64
import time
from datetime import datetime, timedelta

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="My Village Digital Portal", page_icon="🏡", layout="wide")
BASE_DIR = Path(__file__).parent

# --------------------------------------------------
# LANGUAGE SYSTEM
# --------------------------------------------------
LANG = {
    "English":{
        "welcome":"MY VILLAGE DIGITAL PORTAL WELCOME",
        "enter":"Enter Portal",
        "stories":"Today Stories"
    },
    "Telugu":{
        "welcome":"MY VILLAGE DIGITAL PORTAL కు స్వాగతం",
        "enter":"ప్రవేశించండి",
        "stories":"ఈ రోజు కథలు"
    }
}

if "lang" not in st.session_state:
    st.session_state.lang="English"

# --------------------------------------------------
# PREMIUM STYLE + FOOTER
# --------------------------------------------------
st.markdown("""
<style>
.stApp {background:#f5f7fa;}
[data-testid="stSidebar"]{
background:linear-gradient(#0f2027,#203a43,#2c5364);
}
.footer{
position:fixed;
bottom:10px;
width:100%;
text-align:center;
color:gray;
}
</style>
<div class="footer">Developed by ANJI</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CREATE FILE IF NOT EXISTS
# --------------------------------------------------
def ensure_file(file, columns):
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)

ensure_file("families.csv", ["Family_ID","Head_of_Family","Address"])
ensure_file("pupils.csv", ["Name","Family_ID","Relation","Age","Voter_ID"])
ensure_file("places.csv", ["Name","Type","Latitude","Longitude"])
ensure_file("team.csv", ["Name","Role"])
ensure_file("wards.csv", ["Ward","Start","End"])
ensure_file("stories.csv", ["User","Text","Image","Time"])

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
def load(file):
    return pd.read_csv(file)

families = load("families.csv")
pupils = load("pupils.csv")
places = load("places.csv")
team = load("team.csv")
wards = load("wards.csv")
stories = load("stories.csv")

# --------------------------------------------------
# AUTO DELETE OLD STORIES (24 HRS)
# --------------------------------------------------
if not stories.empty:
    stories["Time"]=pd.to_datetime(stories["Time"],errors="coerce")
    stories=stories[stories["Time"]>datetime.now()-timedelta(hours=24)]
    stories.to_csv("stories.csv",index=False)

# --------------------------------------------------
# WARD DETECTION
# --------------------------------------------------
def get_ward(voter_id):

    if wards.empty:
        return "Unknown"

    start_col=None
    end_col=None

    for col in wards.columns:
        if col.lower() in ["start","start_id","from"]:
            start_col=col
        if col.lower() in ["end","end_id","to"]:
            end_col=col

    if start_col is None or end_col is None:
        return "Unknown"

    try:
        voter_id=int(voter_id)
    except:
        return "Unknown"

    for _,row in wards.iterrows():
        try:
            if int(row[start_col])<=voter_id<=int(row[end_col]):
                return row["Ward"]
        except:
            pass

    return "Unknown"

# --------------------------------------------------
# WELCOME SCREEN (FIRST INTERFACE)
# --------------------------------------------------
if "start" not in st.session_state:
    st.session_state.start=False

if not st.session_state.start:

    # optional village background image
    try:
        img=BASE_DIR/"photos"/"village.jpg"
        if img.exists():
            with open(img,"rb") as f:
                data=base64.b64encode(f.read()).decode()

            st.markdown(f"""
            <style>
            .stApp {{
            background-image:url("data:image/jpg;base64,{data}");
            background-size:cover;
            }}
            </style>
            """,unsafe_allow_html=True)
    except:
        pass

    st.session_state.lang=st.selectbox("Language / భాష",["English","Telugu"])
    L=LANG[st.session_state.lang]

    st.markdown(f"<h1 style='text-align:center'>{L['welcome']}</h1>",unsafe_allow_html=True)

    st.markdown("""
    <marquee style='font-size:28px;color:green'>
    SARVAPOOR KOTHAPALLE VILLAGE DIGITAL SERVICE
    </marquee>
    """,unsafe_allow_html=True)

    if st.button(L["enter"]):
        st.session_state.start=True
        st.rerun()

    st.stop()

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
if "role" not in st.session_state:
    st.session_state.role=None

st.sidebar.title("🔐 Login")
login_type=st.sidebar.selectbox("Login As",["User","Admin"])

if login_type=="User":
    if st.sidebar.button("Enter"):
        st.session_state.role="user"

if login_type=="Admin":
    pwd=st.sidebar.text_input("Password",type="password")
    if st.sidebar.button("Login"):
        if pwd=="admin123":
            st.session_state.role="admin"
        else:
            st.sidebar.error("Wrong password")

if st.session_state.role is None:
    st.stop()

# --------------------------------------------------
# PREMIUM MENU (YOUR ORIGINAL + STORIES ADDED)
# --------------------------------------------------
with st.sidebar:
    selected=option_menu(
        "Village Portal",
        ["Dashboard","Families","Pupils","Village Team","Places","Today Stories"],
        icons=["house-fill","people-fill","person-badge","person-workspace","geo-alt-fill","camera-fill"],
        default_index=0
    )

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if selected=="Dashboard":

    st.title("🏡SARVAPOOR KOTHAPALLE Village Smart Dashboard")

    c1,c2,c3,c4=st.columns(4)
    c1.metric("Families",len(families))
    c2.metric("Members",len(pupils))
    c3.metric("Locations",len(places))
    c4.metric("Team Members",len(team))

    st.divider()

    # SEARCH
    st.subheader("🔎 Smart Search (Pupil Details)")
    search=st.text_input("Enter Pupil Name")

    if search:
        result=pupils[pupils["Name"].astype(str).str.contains(search,case=False)]

        if not result.empty:
            for _,row in result.iterrows():

                fam=families[families["Family_ID"]==row["Family_ID"]]
                ward_detected=get_ward(row.get("Voter_ID"))

                col1,col2=st.columns(2)

                with col1:
                    st.success("Pupil Details")
                    st.write("Name:",row["Name"])
                    st.write("Relation:",row["Relation"])
                    st.write("Age:",row["Age"])
                    st.write("Voter ID:",row.get("Voter_ID"))
                    st.write("Ward:",ward_detected)

                with col2:
                    if not fam.empty:
                        st.success("Family Details")
                        st.write("Family Head:",fam.iloc[0]["Head_of_Family"])
                        st.write("Address:",fam.iloc[0]["Address"])

                st.subheader("👨‍👩‍👧 Full Family Members")
                family_members=pupils[pupils["Family_ID"]==row["Family_ID"]]
                st.dataframe(family_members)

        else:
            st.warning("No record found")

    st.divider()

    # MAP
    st.subheader("🗺 Village Map")
    m=folium.Map(location=[18.678054,78.961130],zoom_start=15)

    for _,row in places.iterrows():
        try:
            folium.Marker(
                [float(row["Latitude"]),float(row["Longitude"])],
                popup=f"{row['Name']} ({row['Type']})"
            ).add_to(m)
        except:
            pass

    st_folium(m,width=900)

# --------------------------------------------------
# FAMILIES
# --------------------------------------------------
if selected=="Families":
    st.header("Families")
    st.dataframe(families)

# --------------------------------------------------
# PUPILS
# --------------------------------------------------
if selected=="Pupils":
    st.header("Pupils")
    st.dataframe(pupils)

# --------------------------------------------------
# TEAM
# --------------------------------------------------
if selected=="Village Team":
    st.header("Village Team")
    st.dataframe(team)

# --------------------------------------------------
# PLACES
# --------------------------------------------------
if selected=="Places":
    st.header("Village Locations")
    st.dataframe(places)

# --------------------------------------------------
# TODAY STORIES (NEW FEATURE)
# --------------------------------------------------
if selected=="Today Stories":

    st.header("📸 Today Stories (Auto delete after 24 hrs)")

    user=st.text_input("Your Name")
    text=st.text_input("Write Update")
    img=st.file_uploader("Upload Photo",type=["jpg","png","jpeg"])

    if st.button("Post Story"):

        img_path=""
        if img:
            os.makedirs("story_images",exist_ok=True)
            img_path=f"story_images/{time.time()}.jpg"
            with open(img_path,"wb") as f:
                f.write(img.read())

        new=pd.DataFrame([[user,text,img_path,datetime.now()]],
                         columns=["User","Text","Image","Time"])

        new.to_csv("stories.csv",mode="a",header=False,index=False)
        st.success("Story Posted")

    st.subheader("Active Stories")

    stories=pd.read_csv("stories.csv")
    if not stories.empty:
        stories["Time"]=pd.to_datetime(stories["Time"],errors="coerce")
        active=stories[stories["Time"]>datetime.now()-timedelta(hours=24)]

        for _,r in active.iterrows():
            st.write("User:",r["User"])
            st.write(r["Text"])
            if r["Image"] and os.path.exists(r["Image"]):
                st.image(r["Image"],width=300)
            st.divider()