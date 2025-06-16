import streamlit as st
import core
import config

class Arg:
    def __init__(self, value: str):
        self.value = value
    def get(self):
        return self.value

core.initialize()

st.set_page_config(page_title="BukkitGPT v3", page_icon="🧩")

st.title("BukkitGPT v3 WebUI")

st.sidebar.image("banner.jpeg")
st.sidebar.markdown(f"**Version:** {config.VERSION_NUMBER}")
st.sidebar.markdown("[GitHub](https://github.com/CyniaAI/BukkitGPT-v3)")

tab_generate, tab_edit, tab_settings = st.tabs(["Generate", "Edit", "Settings"])

with tab_generate:
    plugin_name = st.text_input("Plugin Name", "ExamplePlugin")
    plugin_desc = st.text_area(
        "Plugin Description",
        "Send msg 'hello' to every joined player.",
    )

    if st.button("Generate Plugin"):
        with st.spinner("Generating..."):
            try:
                args = {
                    "PluginName": Arg(plugin_name),
                    "PluginDescription": Arg(plugin_desc),
                }
                core.generate(args)
                st.success("Generation complete. Check the console output for details.")
            except Exception as e:
                st.error(str(e))

with tab_edit:
    original_jar = st.text_input("Original JAR")
    edit_request = st.text_area(
        "Edit Request",
        "Add a command to send a message to all players.",
    )

    if st.button("Edit Plugin"):
        with st.spinner("Editing..."):
            try:
                args = {
                    "OriginalJAR": Arg(original_jar),
                    "EditRequest": Arg(edit_request),
                }
                core.edit(args)
                st.success("Edit complete. Check the console output for details.")
            except Exception as e:
                st.error(str(e))

with tab_settings:
    st.write("Configuration")
    api_key = st.text_input("API Key", value=config.API_KEY)
    base_url = st.text_input("BASE URL", value=config.BASE_URL)

    if st.button("Save & Apply"):
        config.edit_config("API_KEY", api_key)
        config.edit_config("BASE_URL", base_url)
        config.load_config()
        st.success("Configuration saved and applied.")

