import streamlit as st
import pandas as pd
from pathlib import Path
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu

st.set_page_config(page_title="My Village Digital Portal", page_icon="🏡", layout="wide")

BASE_DIR = Path(__file__).parent


# ---------------- FILE SETUP ----------------
def ensure_file(file, cols):
    path = BASE_DIR / file
    if not path.exists():
        pd.DataFrame(columns=cols).to_csv(path, index=False)


def load(file):
    path = BASE_DIR / file
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


# ---------------- PREMIUM + MOBILE + COLOR FIX UI ----------------
st.markdown("""
<style>

/* mobile container */
.block-container{
max-width:700px;
margin:auto;
padding-top:1rem;
}

/* background gradient */
.stApp{
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
}

/* FIX TEXT VISIBILITY */
h1,h2,h3,h4,p,span,label{
color:#ffffff !important;
}

/* tables visibility */
[data-testid="stDataFrame"]{
background:white;
color:black;
}

/* login card */
.login-box{
background:linear-gradient(135deg,#ffffff,#f0f0f0);
padding:30px;
border-radius:15px;
color:black;
box-shadow:0 10px 25px rgba(0,0,0,0.3);
text-align:center;
}

/* horizontal scrolling welcome */
.scroll-wrapper{
max-width:700px;
margin:auto;
overflow:hidden;
background:linear-gradient(90deg,#4facfe,#00f2fe);
border-radius:12px;
padding:10px;
}

.scroll-text{
white-space:nowrap;
display:inline-block;
animation:scroll-left 15s linear infinite;
font-size:22px;
font-weight:bold;
color:#fff;
}

@keyframes scroll-left{
0%{transform:translateX(100%);}
100%{transform:translateX(-100%);}
}

/* button */
.stButton>button{
background:linear-gradient(90deg,#ff7e5f,#feb47b);
color:white;
border-radius:10px;
border:none;
}

/* sidebar */
[data-testid="stSidebar"]{
background:linear-gradient(#1f4037,#99f2c8);
}

/* input text */
input, textarea{
color:black !important;
}

</style>
""", unsafe_allow_html=True)


# ---------------- CREATE FILES ----------------
ensure_file("families.csv",["Family_ID","Head_of_Family","Address"])
ensure_file("pupils.csv",["Name","Family_ID","Relation","Age","Voter_ID"])
ensure_file("places.csv",["Name","Type","Latitude","Longitude"])
ensure_file("team.csv",["Name","Role"])
ensure_file("leagues.csv",["Sport","Season","Winner","Runner"])
ensure_file("ward_ranges.csv",["Ward","Start","End"])

# ✅ NEW YOUTH FILE
ensure_file("youth.csv",["Youth_Name","President","Members","Logo"])


# ---------------- LOAD DATA ----------------
families=load("families.csv")
pupils=load("pupils.csv")
places=load("places.csv")
team=load("team.csv")
leagues=load("leagues.csv")
ward_ranges=load("ward_ranges.csv")
youth=load("youth.csv")


# ---------------- FAST SEARCH CACHE ----------------
@st.cache_data
def prepare(df):
    return df.astype(str).apply(lambda x:x.str.lower())

pupils_fast=prepare(pupils)
families_fast=prepare(families)
places_fast=prepare(places)
team_fast=prepare(team)
leagues_fast=prepare(leagues)
youth_fast=prepare(youth)


# ---------------- WARD DETECTION ----------------
def detect_ward(voter_id):
    if pd.isna(voter_id):
        return "Unknown"

    number="".join(filter(str.isdigit,str(voter_id)))
    if number=="":
        return "Unknown"

    number=int(number)

    for _,row in ward_ranges.iterrows():
        try:
            if int(row["Start"]) <= number <= int(row["End"]):
                return int(row["Ward"])
        except:
            pass

    return "Unknown"


# ====================================================
# LOGIN PAGE
# ====================================================
if "role" not in st.session_state:
    st.session_state.role=None

if st.session_state.role is None:

    st.markdown("""
    <div class="scroll-wrapper">
        <div class="scroll-text">
        🏡 Welcome to Sarvapoor Kothapalle Village Digital Portal
        </div>
    </div>
    """,unsafe_allow_html=True)

    col1,col2,col3=st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-box">',unsafe_allow_html=True)

        # ✅ LOGIN LOGO
        st.image("https://cdn-icons-png.flaticon.com/512/684/684908.png",width=120)

        login_type=st.selectbox("Login As",["User","Admin"])

        if login_type=="User":
            name=st.text_input("Enter Name")
            if st.button("Enter"):
                st.session_state.role="user"
                st.session_state.username=name
                st.rerun()

        if login_type=="Admin":
            aid=st.text_input("Admin ID")
            pwd=st.text_input("Password",type="password")
            if st.button("Login"):
                if aid=="admin" and pwd=="admin123":
                    st.session_state.role="admin"
                    st.session_state.username="Administrator"
                    st.rerun()
                else:
                    st.error("Wrong Credentials")

        st.markdown("</div>",unsafe_allow_html=True)

    st.stop()


# ---------------- HEADER ----------------
st.markdown(f"""
<div style='padding:15px;border-radius:10px;background:linear-gradient(90deg,#4facfe,#00f2fe);text-align:center'>
<h3>👋 Welcome {st.session_state.username}</h3>
</div>
""",unsafe_allow_html=True)


# ---------------- MENU ----------------
with st.sidebar:
    selected=option_menu(
        "Village Portal",
        ["Dashboard","Families","Pupils","Village Team","Places","Village Leagues","Youth Association","Ward Settings","Logout"],
        icons=["house","people","person","trophy","geo","award","star","gear","box-arrow-right"]
    )


# ====================================================
# DASHBOARD
# ====================================================
if selected=="Dashboard":

    st.title("Village Dashboard")

    c1,c2,c3,c4=st.columns(4)
    c1.metric("Families",len(families))
    c2.metric("Members",len(pupils))
    c3.metric("Places",len(places))
    c4.metric("Team",len(team))

    st.divider()

    # ---------------- GLOBAL SEARCH ----------------
    st.subheader("Smart Global Search")

    query=st.text_input("Search anything")

    if query:
        q=query.lower()
        found=False

        # PERSON SEARCH
        person=pupils[pupils_fast.apply(lambda x:x.str.contains(q)).any(axis=1)]
        if not person.empty:
            st.success("Person Found")
            st.dataframe(person)

            voter=person.iloc[0]["Voter_ID"]
            ward=detect_ward(voter)
            st.info(f"Detected Ward: {ward}")

            fid=person.iloc[0]["Family_ID"]
            st.subheader("Family Head")
            st.dataframe(families[families["Family_ID"]==fid])

            st.subheader("Full Family Members")
            st.dataframe(pupils[pupils["Family_ID"]==fid])

            # ✅ show youth if exists
            youth_match=youth[youth_fast.apply(lambda x:x.str.contains(q)).any(axis=1)]
            if not youth_match.empty:
                st.subheader("Youth Association")
                st.dataframe(youth_match)

            found=True

        # FAMILY SEARCH
        fam=families[families_fast.apply(lambda x:x.str.contains(q)).any(axis=1)]
        if not fam.empty:
            st.success("Family Found")
            st.dataframe(fam)
            found=True

        # TEAM SEARCH
        t=team[team_fast.apply(lambda x:x.str.contains(q)).any(axis=1)]
        if not t.empty:
            st.success("Team Found")
            st.dataframe(t)
            found=True

        # PLACE SEARCH
        p=places[places_fast.apply(lambda x:x.str.contains(q)).any(axis=1)]
        if not p.empty:
            st.success("Place Found")
            st.dataframe(p)
            found=True

        # LEAGUE SEARCH
        l=leagues[leagues_fast.apply(lambda x:x.str.contains(q)).any(axis=1)]
        if not l.empty:
            st.success("League Found")
            st.dataframe(l)
            found=True

        # YOUTH SEARCH
        y=youth[youth_fast.apply(lambda x:x.str.contains(q)).any(axis=1)]
        if not y.empty:
            st.success("Youth Association Found")
            st.dataframe(y)
            found=True

        if not found:
            st.error("Data Not Found")

    st.divider()

    st.subheader("Village Map")
    m=folium.Map(location=[18.678054,78.961130],zoom_start=15)
    folium.Marker([18.678054,78.961130],popup="SARVAPOOR KOTHAPALLE").add_to(m)
    st_folium(m,width=700)


# ====================================================
# ADMIN CONTROL FUNCTION
# ====================================================
def admin_controls(df,file,cols,title):
    st.header(title)
    st.dataframe(df)

    if st.session_state.role!="admin":
        return

    file_path=BASE_DIR / file

    tab1,tab2,tab3=st.tabs(["Add","Edit","Delete"])

    with tab1:
        data={}
        for c in cols:
            data[c]=st.text_input(f"{c}",key=f"{title}_{c}")
        if st.button("Add"):
            pd.DataFrame([data]).to_csv(file_path,mode="a",header=not file_path.exists(),index=False)
            st.success("Added")

    with tab2:
        if len(df)>0:
            idx=st.number_input("Row",0,len(df)-1)
            new={}
            for c in cols:
                new[c]=st.text_input(f"New {c}",df.iloc[idx][c])
            if st.button("Update"):
                df.loc[idx]=list(new.values())
                df.to_csv(file_path,index=False)
                st.success("Updated")

    with tab3:
        if len(df)>0:
            d=st.number_input("Delete Row",0,len(df)-1)
            if st.button("Delete"):
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

# ✅ NEW YOUTH ADMIN SECTION
if selected=="Youth Association":
    admin_controls(youth,"youth.csv",["Youth_Name","President","Members","Logo"],"Youth Association")

# ====================================================
# WARD SETTINGS
# ====================================================
if selected=="Ward Settings":

    st.header("Ward Range Management")
    st.dataframe(ward_ranges)

    if st.session_state.role!="admin":
        st.warning("Admin only")
        st.stop()

    ward=st.number_input("Ward Number",step=1)
    start=st.number_input("Start Range",step=1)
    end=st.number_input("End Range",step=1)

    if st.button("Save Range"):
        new=pd.DataFrame([[ward,start,end]],columns=["Ward","Start","End"])
        ward_ranges=pd.concat([ward_ranges,new],ignore_index=True)
        ward_ranges.to_csv(BASE_DIR/"ward_ranges.csv",index=False)
        st.success("Saved")
    # ====================================================
# VILLAGE GALLERY (USERS CAN UPLOAD)
# ====================================================
if selected=="Village Gallery":

    st.header("📸 Village Gallery")

    gallery_path = BASE_DIR / "gallery.csv"
    image_folder = BASE_DIR / "gallery_images"
    image_folder.mkdir(exist_ok=True)

    # ---------------- UPLOAD IMAGE ----------------
    uploaded_file = st.file_uploader("Upload Village Photo", type=["jpg","png","jpeg"])

    if uploaded_file:
        file_path = image_folder / uploaded_file.name

        with open(file_path,"wb") as f:
            f.write(uploaded_file.getbuffer())

        new = pd.DataFrame([[uploaded_file.name]],columns=["Image"])
        gallery = pd.concat([gallery,new],ignore_index=True)
        gallery.to_csv(gallery_path,index=False)

        st.success("Image uploaded successfully")
        st.rerun()

    st.divider()

    # ---------------- SHOW IMAGES ----------------
    if len(gallery)==0:
        st.info("No images uploaded yet")
    else:
        cols = st.columns(2)
        for i,row in gallery.iterrows():
            img_path = image_folder / row["Image"]
            if img_path.exists():
                with cols[i%2]:
                    st.image(str(img_path),use_container_width=True)

    # ---------------- ADMIN DELETE ----------------
    if st.session_state.role=="admin" and len(gallery)>0:
        st.divider()
        st.subheader("Delete Image (Admin Only)")

        idx = st.number_input("Select Image Row",0,len(gallery)-1)

        if st.button("Delete Image"):
            img_path = image_folder / gallery.iloc[idx]["Image"]
            if img_path.exists():
                img_path.unlink()

            gallery.drop(idx,inplace=True)
            gallery.to_csv(gallery_path,index=False)
            st.success("Deleted")
            st.rerun()
            # ---------------- LOGOUT ----------------
if selected=="Logout":
    st.session_state.role=None
    st.rerun()   