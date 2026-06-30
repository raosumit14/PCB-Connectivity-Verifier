import requests
from streamlit_image_coordinates import streamlit_image_coordinates
import json
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_image_coordinates import streamlit_image_coordinates

st.title("PCB Connectivity Verifier")

# Session State
if "nodes" not in st.session_state:
    st.session_state.nodes = []

if "selected_point" not in st.session_state:
    st.session_state.selected_point = None

if "connections" not in st.session_state:
    st.session_state.connections = []

if "mode" not in st.session_state:
    st.session_state.mode = "Add Node"

    
if "connection_type" not in st.session_state:
    st.session_state.connection_type = "Trace"

if "expected_resistance" not in st.session_state:
    st.session_state.expected_resistance = 0

if "first_node" not in st.session_state:
    st.session_state.first_node = None

if "second_node" not in st.session_state:
    st.session_state.second_node = None

if "pending_connection" not in st.session_state:
    st.session_state.pending_connection = False

# Upload PCB Image
uploaded_file = st.file_uploader("Upload PCB Image", type=["png", "jpg", "jpeg"])

if uploaded_file:

    image = Image.open(uploaded_file)

    display_image = image.copy()
    draw = ImageDraw.Draw(display_image)

    # Draw Connections
    for conn in st.session_state.connections:

        node1 = next(
            (n for n in st.session_state.nodes if n["name"] == conn["from"]), None
        )

        node2 = next(
            (n for n in st.session_state.nodes if n["name"] == conn["to"]), None
        )

        if node1 and node2:

            draw.line(
                (node1["x"], node1["y"], node2["x"], node2["y"]), fill="lime", width=4
            )

    # Font
    font = ImageFont.truetype("NotoSans-Bold.ttf", 45)

    # Draw Saved Nodes
    for node in st.session_state.nodes:

        x = node["x"]
        y = node["y"]

        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill="cyan", outline="black")

        draw.text((x + 20, y - 20), node["name"], fill="yellow", font=font)

    # Clickable Image
    value = streamlit_image_coordinates(display_image, key="pcb", width=1200)

    if value is not None:

        if st.session_state.mode == "Add Node":

            st.session_state.selected_point = {
                "x": value["x"],
                "y": value["y"],
                "width": value["width"],
                "height": value["height"],
            }

        elif st.session_state.mode == "Connect Nodes":

         st.session_state.selected_point = None

        click_x = int(value["x"] * image.width / value["width"])
        click_y = int(value["y"] * image.height / value["height"])

        clicked_node = None

        for node in st.session_state.nodes:

             if abs(click_x - node["x"]) < 20 and abs(click_y - node["y"]) < 20:

                 clicked_node = node
                 break

    if clicked_node:

        if st.session_state.first_node is None:

            st.session_state.first_node = clicked_node["name"]

        elif st.session_state.second_node is None:

            st.session_state.second_node = clicked_node["name"]

            if (
                st.session_state.first_node
                != st.session_state.second_node
            ):

                st.session_state.pending_connection = True

        st.rerun()

    # Coordinates Display
    if st.session_state.selected_point:

        st.markdown("---")

        col1, col2 = st.columns(2)

        col1.metric("X Coordinate", st.session_state.selected_point["x"])

        col2.metric("Y Coordinate", st.session_state.selected_point["y"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("Mode")
    st.session_state.mode = st.sidebar.radio(
        "Select Mode", ["Add Node", "Connect Nodes"]
    )
   # if st.session_state.mode == "Add Node":
       # st.session_state.first_node = None
    # Sidebar
    if st.session_state.mode == "Add Node":

        st.sidebar.header("Node Information")

        if st.session_state.selected_point:

            st.sidebar.write(f"X = {st.session_state.selected_point['x']}")

            st.sidebar.write(f"Y = {st.session_state.selected_point['y']}")

            node_name = st.sidebar.text_input("Node Name")

            if st.session_state.selected_point:

                st.sidebar.write(f"X = {st.session_state.selected_point['x']}")
                st.sidebar.write(f"Y = {st.session_state.selected_point['y']}")

                with st.sidebar.form("save_node_form"):

                    node_name = st.text_input("Node Name")

                    save_node = st.form_submit_button("Save Node")

                if save_node:

                    scale_x = image.width / st.session_state.selected_point["width"]
                    scale_y = image.height / st.session_state.selected_point["height"]

                    real_x = int(st.session_state.selected_point["x"] * scale_x)
                    real_y = int(st.session_state.selected_point["y"] * scale_y)

                    st.session_state.nodes.append(
                        {
                            "name": node_name,
                            "x": real_x,
                            "y": real_y,
                        }
                    )

                    st.session_state.selected_point = None

                    st.rerun()

                else:

                    st.sidebar.error("Please enter a node name")

# Saved Nodes Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Saved Nodes")

for i, node in enumerate(st.session_state.nodes):

    col1, col2 = st.sidebar.columns([3, 1])

    col1.write(node["name"])

    if col2.button("❌", key=f"delete_{i}"):

        deleted_name = st.session_state.nodes[i]["name"]

        st.session_state.nodes.pop(i)

        st.session_state.connections = [
            c
            for c in st.session_state.connections
            if c["from"] != deleted_name and c["to"] != deleted_name
        ]

        st.rerun()

if st.session_state.mode == "Connect Nodes":

    st.sidebar.markdown("---")

    if st.session_state.pending_connection:

        st.sidebar.subheader("Selected Connection")

        st.sidebar.success(
             f"{st.session_state.first_node} → {st.session_state.second_node}"
        )

        connection_type = st.sidebar.selectbox(
             "Connection Type",
        [
            "Trace",
            "Resistor",
            "Capacitor",
            "Inductor",
            "LED",
            "Diode",
            "Jumper",
            "Switch",
        ],
    )

        if connection_type == "Trace":
             expected_resistance = 0

        elif connection_type == "Capacitor":
             expected_resistance = "OPEN"

        else:
            expected_resistance = st.sidebar.text_input(
            "Expected Resistance (Ω)",
            value="1000",
        )

        if st.sidebar.button("Save Connection"):

            duplicate = any(
            (
                c["from"] == st.session_state.first_node
                and c["to"] == st.session_state.second_node
            )
            or
            (
                c["from"] == st.session_state.second_node
                and c["to"] == st.session_state.first_node
            )
            for c in st.session_state.connections
        )

            if not duplicate:

                st.session_state.connections.append(
                {
                    "from": st.session_state.first_node,
                    "to": st.session_state.second_node,
                    "type": connection_type,
                    "expected_resistance": expected_resistance,
                }
            )

            st.session_state.first_node = None
            st.session_state.second_node = None
            st.session_state.pending_connection = False

            st.rerun()
    

    for i, conn in enumerate(st.session_state.connections):

        col1, col2 = st.sidebar.columns([3, 1])

        col1.write(
            f"{conn['from']} → {conn['to']} "
            f"({conn['type']}, {conn['expected_resistance']})"
        )

        if col2.button("❌", key=f"delete_conn_{i}"):

            st.session_state.connections.pop(i)

            st.rerun()




st.markdown("---")
st.subheader("Export Expected Netlist")
firebase_url = "https://pcb-fault-detection-9e9f0-default-rtdb.asia-southeast1.firebasedatabase.app/netlist.json"
if st.button("Generate Expected Netlist"):

    netlist = {"connections": st.session_state.connections}

    with open("expected_netlist.json", "w") as f:

        json.dump(netlist, f, indent=4)

    st.success("expected_netlist.json created")
if st.button("Upload Netlist to Firebase"):

    netlist = {"connections": st.session_state.connections}

    response = requests.put(firebase_url, json=netlist)

    if response.status_code == 200:

        st.success("Uploaded to Firebase")

    else:

        st.error(f"Upload Failed: {response.text}")
